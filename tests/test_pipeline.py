import json
from pathlib import Path

from typer.testing import CliRunner

from logmind.cli import app
from logmind.freezing import verify_frozen
from logmind.pipeline import evaluate_files

ROOT = Path(__file__).resolve().parents[1]


def test_rules_cli_and_evaluation_roundtrip_on_validation(tmp_path):
    output = tmp_path / "run"
    result = CliRunner().invoke(
        app,
        [
            "predict-rules",
            "--dataset",
            str(ROOT / "data/frozen/v1"),
            "--split",
            "validation",
            "--output",
            str(output),
        ],
    )
    assert result.exit_code == 0, result.output
    metrics, review = evaluate_files(
        ROOT / "data/frozen/v1/validation.jsonl", output / "records.jsonl"
    )
    assert metrics["n"] == metrics["valid_outputs"] == 50
    assert metrics["reviewed_hallucination_rate"] is None
    assert len(review) == 13  # 12 answerable cases plus one missing-diagnostics case.
    assert metrics["run"]["environment"]["split"] == "validation"
    report = tmp_path / "metrics.json"
    result = CliRunner().invoke(
        app,
        [
            "evaluate",
            str(ROOT / "data/frozen/v1/validation.jsonl"),
            str(output / "records.jsonl"),
            "--output",
            str(report),
        ],
    )
    assert result.exit_code == 0, result.output
    assert json.loads(report.read_text())["accuracy"] == metrics["accuracy"]
    assert verify_frozen(ROOT / "data/frozen/v1").status == "frozen"
