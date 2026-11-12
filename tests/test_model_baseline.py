import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from logmind.benchmark import percentile, summarize
from logmind.evaluation import parse_response
from logmind.local_model import ModelConfig, read_config
from logmind.model_pipeline import run_model
from logmind.prompts import messages

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "experiments/configs/qwen3-1.7b-zero-shot-v1.json"


def test_prompt_uses_only_allowlisted_input(incident):
    prompt = messages(incident.to_prompt_input())
    assert json.loads(prompt[1]["content"]) == incident.to_prompt_input().model_dump()
    assert "root_cause" not in json.loads(prompt[1]["content"])
    assert "scenario_id" not in prompt[1]["content"]
    assert prompt[0]["role"] == "system"


def test_model_and_tokenizer_are_immutable_and_decoding_fixed():
    config = read_config(CONFIG)
    assert config.revision == config.tokenizer_revision
    assert not config.do_sample and not config.enable_thinking
    altered = config.model_dump()
    altered["revision"] = "main"
    with pytest.raises(ValidationError):
        ModelConfig.model_validate(altered)


def test_percentile_is_linear_interpolation():
    assert percentile([3.0, 1.0, 2.0], 0.95) == pytest.approx(2.9)


def test_invalid_model_outputs_are_preserved_and_counted(tmp_path, monkeypatch):
    class FakeModel:
        def __init__(self, config):
            self.config = config
            self.environment = {"runtime": "fake-no-inference"}

        def predict(self, incident, run):
            record = parse_response("not JSON", incident, run, 0.1)
            return record, {
                "input_tokens": 10,
                "output_tokens": 2,
                "elapsed_seconds": 0.1,
                "inference_error": None,
            }

    monkeypatch.setattr("logmind.model_pipeline.LocalModel", FakeModel)
    output = tmp_path / "model-run"
    metrics = run_model(ROOT / "data/frozen/v1", output, CONFIG, split="validation")
    assert metrics["n"] == 50 and metrics["valid_outputs"] == 0
    assert metrics["accuracy"] == 0
    assert len((output / "records.jsonl").read_text().splitlines()) == 50
    assert (output / "predictions.jsonl").read_text() == ""
    assert "not JSON" in (output / "records.jsonl").read_text()


def test_benchmark_reports_failures_and_resource_peaks():
    item = {
        "record": {"parse_errors": ["bad"], "schema_errors": [], "reference_errors": []},
        "measurement": {
            "elapsed_seconds": 2.0,
            "peak_rss_bytes": 100,
            "inference_error": "OOM",
            "gpu_peak_allocated_bytes": 80,
            "gpu_peak_reserved_bytes": 90,
            "input_tokens": 10,
            "output_tokens": 0,
            "generated_tokens_per_second": 0.0,
        },
    }
    report = summarize([item, item, item])
    assert report["inference_errors"] == 3 and report["valid_outputs"] == 0
    assert report["median_seconds"] == report["p95_seconds"] == 2
    assert report["gpu_peak_reserved_bytes"] == 90
