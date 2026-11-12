import hashlib
import json
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from logmind.cli import app
from logmind.freezing import audit_candidate, freeze_dataset, verify_frozen
from logmind.generation import generate_dataset

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "data/scenarios/templates"


@pytest.fixture
def candidate(tmp_path):
    path = tmp_path / "candidate"
    generate_dataset(TEMPLATES, path)
    return path


@pytest.fixture
def frozen(candidate, tmp_path):
    path = tmp_path / "frozen"
    freeze_dataset(candidate, path, TEMPLATES, ROOT)
    return path


def test_freeze_preserves_candidate_bytes_and_verifies_pinned_manifest(candidate, tmp_path):
    original = {p.name: p.read_bytes() for p in candidate.iterdir()}
    output = tmp_path / "frozen"
    manifest = freeze_dataset(candidate, output, TEMPLATES, ROOT)
    assert manifest.status == "frozen"
    assert manifest.candidate.records == 150
    for name in ("incidents.jsonl", "train.jsonl", "validation.jsonl", "test.jsonl"):
        assert (output / name).read_bytes() == original[name]
    assert (output / "candidate-manifest.json").read_bytes() == original["manifest.json"]
    pin = hashlib.sha256((output / "manifest.json").read_bytes()).hexdigest()
    assert verify_frozen(output, pin) == manifest
    assert {p.name: p.read_bytes() for p in candidate.iterdir()} == original
    assert (output / "reproduction/uv.lock").read_bytes() == (ROOT / "uv.lock").read_bytes()
    assert len(list((output / "reproduction/data/scenarios/templates").glob("*.jsonl"))) == 42
    assert freeze_dataset(candidate, output, TEMPLATES, ROOT) == manifest


@pytest.mark.parametrize("artifact", ["test.jsonl", "reproduction/src/logmind/generation.py"])
def test_frozen_data_and_source_tampering_is_detected(frozen, artifact):
    path = frozen / artifact
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="checksum mismatch"):
        verify_frozen(frozen)


def test_manifest_tampering_and_wrong_external_pin_are_detected(frozen):
    with pytest.raises(ValueError, match="externally pinned"):
        verify_frozen(frozen, "0" * 64)
    path = frozen / "manifest.json"
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="manifest checksum mismatch"):
        verify_frozen(frozen)


def test_frozen_inventory_rejects_extra_files_and_symlinks(frozen, tmp_path):
    extra = frozen / "unexpected.txt"
    extra.write_text("not sealed")
    with pytest.raises(ValueError, match="inventory mismatch"):
        verify_frozen(frozen)
    extra.unlink()
    target = tmp_path / "outside.txt"
    target.write_text("outside")
    (frozen / "link").symlink_to(target)
    with pytest.raises(ValueError, match="symlinks"):
        verify_frozen(frozen)


def test_candidate_counts_are_audited_before_freezing(candidate, tmp_path):
    path = candidate / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest["records_by_category"]["container_crash"] += 1
    path.write_text(json.dumps(manifest))
    output = tmp_path / "frozen"
    with pytest.raises(ValueError, match="records_by_category"):
        freeze_dataset(candidate, output, TEMPLATES, ROOT)
    assert not output.exists()


def test_coherent_candidate_changes_still_fail_reproduction_audit(candidate):
    manifest_path = candidate / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    combined = [
        json.loads(line) for line in (candidate / "incidents.jsonl").read_text().splitlines()
    ]
    changed = combined[0]
    changed["root_cause"] = "An unsupported alternative diagnosis."
    for name in ("incidents.jsonl", f"{changed['split']}.jsonl"):
        records = [json.loads(line) for line in (candidate / name).read_text().splitlines()]
        for record in records:
            if record["id"] == changed["id"]:
                record["root_cause"] = changed["root_cause"]
        content = "".join(json.dumps(record) + "\n" for record in records).encode()
        (candidate / name).write_bytes(content)
        manifest["files"][name]["sha256"] = hashlib.sha256(content).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="does not reproduce"):
        audit_candidate(candidate, TEMPLATES)


def test_conflicting_frozen_version_is_not_overwritten(candidate, frozen):
    before = (frozen / "manifest.json").read_bytes()
    with pytest.raises(ValueError, match="already exists"):
        freeze_dataset(candidate, frozen, TEMPLATES, ROOT, dataset_version="v2")
    assert (frozen / "manifest.json").read_bytes() == before


def test_verification_uses_frozen_templates_not_working_copy(candidate, tmp_path):
    templates = tmp_path / "templates"
    shutil.copytree(TEMPLATES, templates)
    output = tmp_path / "frozen"
    freeze_dataset(candidate, output, templates, ROOT)
    (templates / "crash-01.jsonl").unlink()
    assert verify_frozen(output).candidate.records == 150


def test_freeze_and_verification_cli(candidate, tmp_path):
    output = tmp_path / "release"
    result = CliRunner().invoke(
        app,
        [
            "freeze",
            "--candidate",
            str(candidate),
            "--output",
            str(output),
            "--templates",
            str(TEMPLATES),
            "--project",
            str(ROOT),
        ],
    )
    assert result.exit_code == 0, result.output
    result = CliRunner().invoke(app, ["verify-dataset", str(output)])
    assert result.exit_code == 0, result.output
    (output / "test.jsonl").write_text("bad data\n")
    result = CliRunner().invoke(app, ["verify-dataset", str(output)])
    assert result.exit_code == 1
    assert "checksum mismatch" in result.output
