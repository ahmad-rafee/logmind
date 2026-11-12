"""Conservative, reproducible variants of the reviewed fictional baselines."""

import hashlib
import json
import random
import tempfile
from collections import Counter
from pathlib import Path

from logmind.jsonl import read_incidents
from logmind.schemas import DatasetFile, DatasetManifest, Incident, Observation

GENERATOR_VERSION = "1"
SPLITS = ("train", "validation", "test")
GROUPS = {
    "crash": "container_crash",
    "oom": "oom_killed",
    "image": "image_pull_failure",
    "probe": "probe_failure",
    "config": "missing_config",
    "schedule": "scheduling_failure",
    "unknown": "insufficient_evidence",
}
VARIANTS = ("baseline", "wording", "noisy", "long")
LONG_CONTEXT_RECORDS = 32
PROSE = (
    ("Target: ", ("Selected workload: ", "Workload under inspection: ")),
    ("Target pod ", ("Selected pod ", "Pod under inspection: ")),
    ("Pod phase ", ("Observed pod phase ", "Reported pod phase ")),
)
NOTES = (
    "The workload documentation lists the owning team as {team} "
    "and the handbook edition as {edition}.",
    "The display preferences specify the {theme} theme and a {language} translation catalogue.",
    "The documentation index groups this component under section {edition} "
    "of the service handbook.",
    "The release notes include a formatting update for the {language} help pages "
    "maintained by {team}.",
    "The supplied workload notes use the {theme} diagram palette "
    "and reference handbook edition {edition}.",
)


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def load_templates(directory: Path) -> tuple[list[Incident], str]:
    """Require the complete reviewed catalogue, with fixed scenario-level splits."""
    expected = {f"{group}-{number:02d}" for group in GROUPS for number in range(1, 7)}
    paths = sorted(directory.glob("*.jsonl"))
    if {path.stem for path in paths} != expected:
        raise ValueError("Template directory must contain exactly the 42 catalogue JSONL files")
    records = []
    digest = hashlib.sha256()
    for path in paths:
        content = path.read_bytes()
        digest.update(path.name.encode() + b"\0" + content + b"\0")
        items = read_incidents(path)
        if len(items) != 1:
            raise ValueError(f"{path}: expected one baseline record")
        record = items[0]
        group, number = path.stem.split("-")
        expected_split = SPLITS[(int(number) - 1) // 2]
        if (
            record.scenario_id != path.stem
            or record.category != GROUPS[group]
            or record.split != expected_split
            or record.source != "synthetic"
            or record.variant_tags
            != ["baseline"]
            + (
                ["target_ambiguity" if number == "06" else "missing_diagnostics"]
                if group == "unknown"
                else []
            )
        ):
            raise ValueError(f"{path}: baseline identity, category, split, source, or tags drifted")
        records.append(record)
    if len({record.id for record in records}) != len(records):
        raise ValueError("Baseline incident IDs must be unique")
    return records, digest.hexdigest()


def _key(seed: int, scenario: str, variant: str) -> str:
    return _sha256(f"{GENERATOR_VERSION}\0{seed}\0{scenario}\0{variant}".encode())


def _wording(record: Incident, rng: random.Random) -> None:
    """Rephrase snapshot framing, leaving actual diagnostic strings untouched."""
    changed = False
    for observation in record.observations:
        if observation.kind not in {"metadata", "status"}:
            continue
        replacements = [(old, rng.choice(choices)) for old, choices in PROSE]
        for old, new in replacements:
            if old not in observation.text:
                continue
            observation.text = observation.text.replace(old, new)
            for evidence in record.evidence:
                if evidence.observation_id == observation.id:
                    evidence.excerpt = evidence.excerpt.replace(old, new)
            changed = True
    if not changed:
        raise ValueError(f"{record.scenario_id}: no supported snapshot wording transformation")


def _add_context(record: Incident, rng: random.Random, count: int) -> None:
    known = {observation.id for observation in record.observations}
    for index in range(count):
        identifier = f"context-{index + 1}"
        if identifier in known:
            raise ValueError(f"{record.scenario_id}: context observation ID collision")
        note = rng.choice(NOTES).format(
            team=rng.choice(("harbor", "orchard", "meadow", "cedar")),
            edition=rng.randint(1, 99),
            theme=rng.choice(("slate", "sand", "forest", "ocean")),
            language=rng.choice(("Arabic", "English", "French")),
        )
        record.observations.append(
            Observation(
                id=identifier,
                kind="metadata",
                text=f"Workload note {index + 1}: {note}",
                details={"source": "supplied_workload_notes", "note": note},
            )
        )
    # Vary evidence position without changing any original diagnostic facts.
    rng.shuffle(record.observations)


def generate_records(templates: list[Incident], seed: int) -> list[Incident]:
    """Four variants per answerable case; abstention cases stay deliberately incomplete."""
    results = []
    for template in sorted(templates, key=lambda record: record.scenario_id):
        variants = ("baseline",) if template.category == "insufficient_evidence" else VARIANTS
        for variant in variants:
            key = _key(seed, template.scenario_id, variant)
            rng = random.Random(int(key, 16))
            record = template.model_copy(deep=True)
            record.id = f"case-{key[:24]}"
            record.variant_tags = [variant] + template.variant_tags[1:]
            if variant == "wording":
                _wording(record, rng)
            elif variant in {"noisy", "long"}:
                count = LONG_CONTEXT_RECORDS if variant == "long" else rng.randint(2, 4)
                _add_context(record, rng, count)
            results.append(Incident.model_validate(record.model_dump()))
    if len({record.id for record in results}) != len(results):
        raise ValueError("Generated incident ID collision")
    # Opaque seeded IDs also prevent file position from trivially encoding labels.
    return sorted(results, key=lambda record: record.id)


def _jsonl(records: list[Incident]) -> bytes:
    return "".join(record.model_dump_json() + "\n" for record in records).encode("utf-8")


def generate_dataset(templates_dir: Path, output: Path, seed: int = 42) -> DatasetManifest:
    """Write a candidate dataset and checksums; never overwrite a different dataset."""
    templates, templates_sha256 = load_templates(templates_dir)
    records = generate_records(templates, seed)
    payloads = {"incidents.jsonl": _jsonl(records)}
    by_split = {split: [record for record in records if record.split == split] for split in SPLITS}
    payloads.update({f"{split}.jsonl": _jsonl(items) for split, items in by_split.items()})
    manifest = DatasetManifest(
        format_version=1,
        status="candidate",
        generator_version=GENERATOR_VERSION,
        generator_sha256=_sha256(Path(__file__).read_bytes()),
        templates_sha256=templates_sha256,
        seed=seed,
        records=len(records),
        scenarios=len(templates),
        records_by_split={split: len(items) for split, items in by_split.items()},
        scenarios_by_split=dict(sorted(Counter(record.split for record in templates).items())),
        scenarios_by_category=dict(
            sorted(Counter(record.category for record in templates).items())
        ),
        records_by_category=dict(sorted(Counter(record.category for record in records).items())),
        records_by_variant=dict(
            sorted(Counter(record.variant_tags[0] for record in records).items())
        ),
        files={
            name: DatasetFile(sha256=_sha256(content), records=len(content.splitlines()))
            for name, content in payloads.items()
        },
    )
    payloads["manifest.json"] = (json.dumps(manifest.model_dump(), indent=2) + "\n").encode()
    if output.exists():
        if output.is_dir() and {path.name for path in output.iterdir()} == set(payloads):
            if all((output / name).read_bytes() == content for name, content in payloads.items()):
                return manifest
        raise ValueError(
            f"{output}: already exists with different contents; choose a new output path"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".logmind-", dir=output.parent) as staging:
        staged = Path(staging) / "dataset"
        staged.mkdir()
        for name, content in payloads.items():
            (staged / name).write_bytes(content)
        staged.rename(output)
    return manifest
