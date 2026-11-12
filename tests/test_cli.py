import json

from typer.testing import CliRunner

from logmind.cli import app
from logmind.jsonl import write_jsonl

runner = CliRunner()


def test_validation_commands(tmp_path, incident, prediction):
    inputs = tmp_path / "incidents.jsonl"
    outputs = tmp_path / "predictions.jsonl"
    write_jsonl(inputs, [incident])
    write_jsonl(outputs, [prediction])
    result = runner.invoke(app, ["validate-incidents", str(inputs)])
    assert result.exit_code == 0, result.output
    result = runner.invoke(app, ["validate-predictions", str(outputs), str(inputs)])
    assert result.exit_code == 0, result.output
    prediction.evidence_ids = ["invented"]
    write_jsonl(outputs, [prediction])
    result = runner.invoke(app, ["validate-predictions", str(outputs), str(inputs)])
    assert result.exit_code == 1
    assert "Unknown predicted evidence" in result.output


def test_export_schemas(tmp_path):
    result = runner.invoke(app, ["export-schemas", str(tmp_path)])
    assert result.exit_code == 0, result.output
    schema = json.loads((tmp_path / "Prediction.schema.json").read_text())
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(schema["properties"])


def test_missing_input_reports_failure(tmp_path):
    result = runner.invoke(app, ["validate-incidents", str(tmp_path / "missing.jsonl")])
    assert result.exit_code == 1
