"""Audit and freeze candidates without editing their data or overwriting releases."""

import hashlib
import json
import platform
import tempfile
from collections import Counter
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path, PurePosixPath

from logmind.generation import generate_dataset, load_templates
from logmind.jsonl import read_incidents
from logmind.schemas import DatasetManifest, FrozenDatasetManifest

DATA_FILES = {"incidents.jsonl", "train.jsonl", "validation.jsonl", "test.jsonl"}
AUDIT_CHECKS = [
    "Strict incident schemas and gold evidence references",
    "Unique incident IDs and scenario split isolation",
    "Combined and split files contain identical corresponding records",
    "Record, scenario, category, and variant counts match the candidate manifest",
    "All candidate bytes reproduce with the recorded seed and current reviewed templates",
    "Frozen artifacts include source, templates, dependencies, and generation settings",
]


def _digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _read_payloads(directory: Path, manifest: DatasetManifest) -> dict[str, bytes]:
    if set(manifest.files) != DATA_FILES:
        raise ValueError("Dataset manifest must list exactly the four dataset JSONL files")
    payloads = {}
    for name, info in manifest.files.items():
        content = (directory / name).read_bytes()
        if _digest(content) != info.sha256:
            raise ValueError(f"{name}: checksum mismatch")
        records = read_incidents(directory / name)
        if len(records) != info.records:
            raise ValueError(f"{name}: record count mismatch")
        payloads[name] = content
    records = read_incidents(directory / "incidents.jsonl")
    if any(not record.variant_tags for record in records):
        raise ValueError("Every dataset record must have a variant tag")
    by_id = {record.id: record for record in records}
    scenarios = {}
    for record in records:
        identity = (record.split, record.category)
        if scenarios.setdefault(record.scenario_id, identity) != identity:
            raise ValueError(f"{record.scenario_id}: inconsistent scenario split/category")
    actual = {
        "records": len(records),
        "scenarios": len(scenarios),
        "records_by_split": dict(Counter(record.split for record in records)),
        "records_by_category": dict(Counter(record.category for record in records)),
        "records_by_variant": dict(Counter(record.variant_tags[0] for record in records)),
        "scenarios_by_split": dict(Counter(split for split, _ in scenarios.values())),
        "scenarios_by_category": dict(Counter(category for _, category in scenarios.values())),
    }
    for field, value in actual.items():
        if getattr(manifest, field) != value:
            raise ValueError(f"Dataset manifest {field} does not match dataset")
    for split in ("train", "validation", "test"):
        split_records = read_incidents(directory / f"{split}.jsonl")
        expected_ids = {record.id for record in records if record.split == split}
        if {record.id for record in split_records} != expected_ids:
            raise ValueError(f"{split}: split membership mismatch")
        if any(record != by_id[record.id] for record in split_records):
            raise ValueError(f"{split}: records differ from combined dataset")
    return payloads


def audit_candidate(directory: Path, templates: Path) -> DatasetManifest:
    manifest_bytes = (directory / "manifest.json").read_bytes()
    manifest = DatasetManifest.model_validate_json(manifest_bytes)
    _read_payloads(directory, manifest)
    with tempfile.TemporaryDirectory(prefix="logmind-audit-") as staging:
        reproduced = Path(staging) / "candidate"
        generate_dataset(templates, reproduced, manifest.seed)
        for name in DATA_FILES | {"manifest.json"}:
            if (directory / name).read_bytes() != (reproduced / name).read_bytes():
                raise ValueError(
                    f"{name}: candidate does not reproduce with current source/templates"
                )
    return manifest


def _artifact_paths(directory: Path) -> dict[str, Path]:
    paths = {}
    for path in directory.rglob("*"):
        if path.is_symlink():
            raise ValueError("Frozen datasets cannot contain symlinks")
        if path.is_file():
            relative = path.relative_to(directory).as_posix()
            if relative not in {"manifest.json", "manifest.sha256"}:
                paths[relative] = path
    return paths


def verify_frozen(directory: Path, expected_sha256: str | None = None) -> FrozenDatasetManifest:
    """Verify a release independently of the current working templates/generator."""
    manifest_bytes = (directory / "manifest.json").read_bytes()
    recorded_hash = (directory / "manifest.sha256").read_text().strip()
    if _digest(manifest_bytes) != recorded_hash:
        raise ValueError("Frozen manifest checksum mismatch")
    if expected_sha256 is not None and recorded_hash != expected_sha256:
        raise ValueError("Frozen manifest does not match the externally pinned checksum")
    manifest = FrozenDatasetManifest.model_validate_json(manifest_bytes)
    # Reject unsafe names before using any manifest-supplied artifact paths.
    for name in manifest.artifacts:
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or path.as_posix() != name:
            raise ValueError("Unsafe frozen artifact path")
    paths = _artifact_paths(directory)
    if set(paths) != set(manifest.artifacts):
        raise ValueError("Frozen artifact inventory mismatch")
    for name, path in paths.items():
        if _digest(path.read_bytes()) != manifest.artifacts[name]:
            raise ValueError(f"{name}: frozen artifact checksum mismatch")
    candidate_bytes = (directory / "candidate-manifest.json").read_bytes()
    if _digest(candidate_bytes) != manifest.candidate_manifest_sha256:
        raise ValueError("Candidate manifest checksum mismatch")
    if DatasetManifest.model_validate_json(candidate_bytes) != manifest.candidate:
        raise ValueError("Frozen and candidate manifest settings disagree")
    _read_payloads(directory, manifest.candidate)
    reproduction = directory / "reproduction"
    _, templates_hash = load_templates(reproduction / "data/scenarios/templates")
    if templates_hash != manifest.candidate.templates_sha256:
        raise ValueError("Frozen template aggregate checksum mismatch")
    source = reproduction / "src/logmind/generation.py"
    if _digest(source.read_bytes()) != manifest.candidate.generator_sha256:
        raise ValueError("Frozen generator source checksum mismatch")
    return manifest


def freeze_dataset(
    candidate: Path,
    output: Path,
    templates: Path,
    project: Path,
    dataset_version: str = "v1",
) -> FrozenDatasetManifest:
    """Audit, copy, and seal one release; a differing existing release is an error."""
    if not dataset_version.strip():
        raise ValueError("Dataset version must not be empty")
    candidate_manifest = audit_candidate(candidate, templates)
    candidate_bytes = (candidate / "manifest.json").read_bytes()
    if output.exists():
        existing = verify_frozen(output)
        if (
            existing.dataset_version == dataset_version
            and existing.candidate_manifest_sha256 == _digest(candidate_bytes)
        ):
            return existing
        raise ValueError(f"{output}: frozen release already exists; choose a new version/path")
    payloads = {name: (candidate / name).read_bytes() for name in DATA_FILES}
    payloads["candidate-manifest.json"] = candidate_bytes
    for name in ("pyproject.toml", "uv.lock", ".python-version", "README.md", "Makefile"):
        payloads[f"reproduction/{name}"] = (project / name).read_bytes()
    for source in sorted((project / "src/logmind").glob("*.py")):
        payloads[f"reproduction/src/logmind/{source.name}"] = source.read_bytes()
    for template in sorted(templates.glob("*.jsonl")):
        payloads[f"reproduction/data/scenarios/templates/{template.name}"] = template.read_bytes()
    # Ensure a caller-supplied project cannot silently bundle an unrelated generator.
    if (
        _digest(payloads["reproduction/src/logmind/generation.py"])
        != candidate_manifest.generator_sha256
    ):
        raise ValueError("Reproduction project does not contain the candidate generator source")
    manifest = FrozenDatasetManifest(
        format_version=1,
        status="frozen",
        dataset_version=dataset_version,
        frozen_at_utc=datetime.now(UTC).isoformat(),
        candidate_manifest_sha256=_digest(candidate_bytes),
        candidate=candidate_manifest,
        audit_checks=AUDIT_CHECKS,
        environment={"python": platform.python_version(), "pydantic": version("pydantic")},
        artifacts={name: _digest(content) for name, content in sorted(payloads.items())},
    )
    encoded = (json.dumps(manifest.model_dump(), indent=2) + "\n").encode()
    payloads["manifest.json"] = encoded
    payloads["manifest.sha256"] = (_digest(encoded) + "\n").encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".logmind-freeze-", dir=output.parent) as temporary:
        staging = Path(temporary) / "release"
        staging.mkdir()
        for name, content in payloads.items():
            path = staging / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        verify_frozen(staging)
        staging.rename(output)
    return manifest
