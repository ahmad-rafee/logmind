"""Validate published evidence without rerunning or retuning held-out inference."""

import hashlib
import json
from pathlib import Path

from logmind.freezing import verify_frozen
from logmind.jsonl import read_jsonl
from logmind.review import summarize_reviews
from logmind.schemas import PredictionRecord

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "experiments/reports/phase0"


def test_archived_raw_runs_cover_the_same_frozen_test_set():
    frozen = verify_frozen(ROOT / "data/frozen/v1")
    checksum = frozen.candidate.files["test.jsonl"].sha256
    identifiers = []
    for backend in ("rules", "model"):
        records = list(read_jsonl(REPORT / f"{backend}-test/records.jsonl", PredictionRecord))
        assert len(records) == 50
        assert all(record.run.dataset_sha256 == checksum for record in records)
        identifiers.append({record.incident_id for record in records})
        metrics = json.loads((REPORT / f"{backend}-test/metrics.json").read_text())
        assert metrics["n"] == 50 and metrics["scenarios"] == 14
        assert len(metrics["per_class"]) == 6
    assert len(identifiers[0]) == 50 and identifiers[0] == identifiers[1]


def test_published_reviews_recompute_from_unchanged_samples():
    for backend in ("rules", "model"):
        actual = summarize_reviews(
            REPORT / f"{backend}-review-sample.jsonl", REPORT / f"{backend}-review-completed.jsonl"
        )
        expected = json.loads((REPORT / f"{backend}-review-summary.json").read_text())
        assert actual == expected
        assert actual["reviewed_predictions"] == 14
        assert actual["reviewer_types"] == ["agent"]


def test_archive_source_matches_pretest_pins():
    reproduction = REPORT / "reproduction"
    lock = json.loads(
        (reproduction / "experiments/configs/phase0-evaluation-lock.json").read_text()
    )
    for relative, expected in lock["sources"].items():
        assert hashlib.sha256((reproduction / relative).read_bytes()).hexdigest() == expected


def test_benchmark_has_matched_inputs_and_three_repetitions():
    report = json.loads((REPORT / "benchmark/summary.json").read_text())
    assert report["repetitions"] == 3
    assert len(report["incident_ids"]) == 7
    for backend in ("rules", "model"):
        assert report["backends"][backend]["cold"]["n_measurements"] == 21
        assert report["backends"][backend]["warm"]["n_measurements"] == 21
        warm = json.loads((REPORT / f"benchmark/{backend}/warm.json").read_text())
        assert warm["warmup"] is not None
        assert {item["record"]["incident_id"] for item in warm["results"]} == set(
            report["incident_ids"]
        )


def test_archive_checksum_inventory():
    index = REPORT / "SHA256SUMS"
    assert index.is_file()
    recorded = set()
    for line in index.read_text().splitlines():
        expected, relative = line.split("  ", 1)
        recorded.add(relative)
        assert hashlib.sha256((REPORT / relative).read_bytes()).hexdigest() == expected
    assert recorded == {
        path.relative_to(REPORT).as_posix()
        for path in REPORT.rglob("*")
        if path.is_file() and path != index
    }
