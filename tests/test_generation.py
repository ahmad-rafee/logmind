import hashlib
import json
import random
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import pytest
from typer.testing import CliRunner

from logmind.cli import app
from logmind.generation import generate_dataset, generate_records, load_templates
from logmind.jsonl import read_incidents, write_jsonl
from logmind.schemas import DatasetManifest

TEMPLATES = Path(__file__).resolve().parents[1] / "data/scenarios/templates"


@pytest.fixture(scope="module")
def templates():
    return load_templates(TEMPLATES)[0]


def test_generation_is_byte_reproducible_and_manifest_checksums_match(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    manifest = generate_dataset(TEMPLATES, first, seed=42)
    generate_dataset(TEMPLATES, second, seed=42)
    assert {p.name: p.read_bytes() for p in first.iterdir()} == {
        p.name: p.read_bytes() for p in second.iterdir()
    }
    assert DatasetManifest.model_validate_json((first / "manifest.json").read_text()) == manifest
    assert manifest.status == "candidate"
    for name, info in manifest.files.items():
        assert hashlib.sha256((first / name).read_bytes()).hexdigest() == info.sha256
        assert len(read_incidents(first / name)) == info.records


def test_expected_counts_and_no_scenario_crosses_splits(tmp_path):
    manifest = generate_dataset(TEMPLATES, tmp_path / "data")
    records = read_incidents(tmp_path / "data/incidents.jsonl")
    assert manifest.records == len(records) == 150
    assert manifest.scenarios == 42
    assert manifest.records_by_split == {"train": 50, "validation": 50, "test": 50}
    assert manifest.scenarios_by_split == {"train": 14, "validation": 14, "test": 14}
    assert len(manifest.scenarios_by_category) == 7
    assert set(manifest.scenarios_by_category.values()) == {6}
    assert manifest.records_by_variant == {"baseline": 42, "wording": 36, "noisy": 36, "long": 36}
    support = Counter(record.category for record in records)
    assert support.pop("insufficient_evidence") == 6
    assert len(support) == 6 and set(support.values()) == {24}
    scenarios = defaultdict(set)
    by_id = {record.id: record for record in records}
    for split in ("train", "validation", "test"):
        split_records = read_incidents(tmp_path / f"data/{split}.jsonl")
        assert len(split_records) == 50
        for record in split_records:
            assert record.split == split
            assert record == by_id[record.id]
            scenarios[record.scenario_id].add(split)
    assert len(scenarios) == 42
    assert all(len(splits) == 1 for splits in scenarios.values())


def test_local_seed_changes_context_without_changing_splits_or_global_rng(templates):
    state = random.getstate()
    first = generate_records(templates, seed=42)
    second = generate_records(list(reversed(templates)), seed=42)
    third = generate_records(templates, seed=43)
    assert random.getstate() == state
    assert first == second
    assert {record.id for record in first}.isdisjoint(record.id for record in third)

    def contexts(records):
        return {
            (record.scenario_id, record.variant_tags[0]): record.observations for record in records
        }

    assert contexts(first) != contexts(third)
    assert {(r.scenario_id, r.split) for r in first} == {(r.scenario_id, r.split) for r in third}


def test_variants_preserve_raw_diagnostics_and_gold_and_do_not_mutate_templates(templates):
    originals = {record.scenario_id: record.model_dump_json() for record in templates}
    by_scenario = {record.scenario_id: record for record in templates}
    for record in generate_records(templates, 42):
        template = by_scenario[record.scenario_id]
        assert (record.category, record.root_cause, record.expected_actions, record.split) == (
            template.category,
            template.root_cause,
            template.expected_actions,
            template.split,
        )
        observations = {item.id: item for item in record.observations}
        baseline_ids = {item.id for item in template.observations}
        assert baseline_ids <= observations.keys()
        for original in template.observations:
            changed = observations[original.id]
            assert changed.details == original.details
            if record.variant_tags[0] != "wording" or original.kind not in {"metadata", "status"}:
                assert changed == original
        variant = record.variant_tags[0]
        if variant == "wording":
            assert record.observations != template.observations
            assert len(record.observations) == len(template.observations)
        elif variant in {"noisy", "long"}:
            added = [item for item in record.observations if item.id not in baseline_ids]
            assert len(added) == 32 if variant == "long" else 2 <= len(added) <= 4
            assert all(item.kind == "metadata" for item in added)
            assert all(item.details["source"] == "supplied_workload_notes" for item in added)
            assert record.evidence == template.evidence
        else:
            assert record.observations == template.observations
            assert record.variant_tags[1:] == template.variant_tags[1:]
        # Schema validation checks that adjusted wording excerpts still occur verbatim.
        prompt = json.dumps(record.to_prompt_input().model_dump())
        assert record.category not in prompt
        assert record.scenario_id not in prompt
        assert all(tag not in prompt for tag in record.variant_tags)
    assert {record.scenario_id: record.model_dump_json() for record in templates} == originals


def test_output_is_idempotent_but_never_overwrites_different_data(tmp_path):
    output = tmp_path / "data"
    expected = generate_dataset(TEMPLATES, output)
    assert generate_dataset(TEMPLATES, output) == expected
    before = {path.name: path.read_bytes() for path in output.iterdir()}
    with pytest.raises(ValueError, match="different contents"):
        generate_dataset(TEMPLATES, output, seed=43)
    assert {path.name: path.read_bytes() for path in output.iterdir()} == before


@pytest.mark.parametrize("problem", ["missing", "split", "category", "duplicates"])
def test_bad_template_catalogue_is_rejected_without_writing_output(tmp_path, problem):
    directory = tmp_path / "templates"
    shutil.copytree(TEMPLATES, directory)
    path = directory / "crash-01.jsonl"
    if problem == "missing":
        path.unlink()
    else:
        record = read_incidents(path)[0]
        if problem == "split":
            record.split = "test"
        elif problem == "category":
            record.category = "probe_failure"
        else:
            record.id = read_incidents(directory / "crash-02.jsonl")[0].id
        write_jsonl(path, [record])
    output = tmp_path / "out"
    with pytest.raises(ValueError):
        generate_dataset(directory, output)
    assert not output.exists()


def test_generate_cli_honors_options_and_reports_conflict(tmp_path):
    output = tmp_path / "candidate"
    args = ["generate", "--templates", str(TEMPLATES), "--output", str(output), "--seed", "17"]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert "150 candidate incidents" in result.output
    assert json.loads((output / "manifest.json").read_text())["seed"] == 17
    result = CliRunner().invoke(app, args[:-1] + ["18"])
    assert result.exit_code == 1
    assert "different contents" in result.output


def test_cli_default_output_uses_selected_seed(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["generate", "--templates", str(TEMPLATES), "--seed", "19"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "data/generated/v1-seed19/manifest.json").is_file()
