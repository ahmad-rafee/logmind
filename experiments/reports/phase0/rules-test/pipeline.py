"""Frozen-data rules runs with raw outputs, immutable source revision, and metrics."""

import hashlib
import json
import platform
import tempfile
from pathlib import Path
from time import perf_counter

from logmind import __version__, rules
from logmind.evaluation import evaluate, parse_response, prepare_review
from logmind.freezing import verify_frozen
from logmind.jsonl import read_incidents, read_jsonl, write_jsonl
from logmind.schemas import PredictionRecord, RunManifest


def evaluate_files(incidents: Path, records: Path) -> tuple[dict, list[dict]]:
    inputs = read_incidents(incidents)
    outputs = list(read_jsonl(records, PredictionRecord))
    checksum = hashlib.sha256(incidents.read_bytes()).hexdigest()
    if any(record.run.dataset_sha256 != checksum for record in outputs):
        raise ValueError("Prediction run dataset checksum does not match incident file")
    metrics = evaluate(inputs, outputs)
    metrics["dataset_sha256"] = checksum
    metrics["records_sha256"] = hashlib.sha256(records.read_bytes()).hexdigest()
    metrics["evaluator_sha256"] = hashlib.sha256(
        Path(__file__).with_name("evaluation.py").read_bytes()
    ).hexdigest()
    metrics["selector_sha256"] = hashlib.sha256(Path(rules.__file__).read_bytes()).hexdigest()
    metrics["run"] = outputs[0].run.model_dump() if outputs else None
    return metrics, prepare_review(inputs, outputs)


def run_rules(dataset: Path, output: Path, split: str = "validation") -> dict:
    if split not in {"train", "validation", "test"}:
        raise ValueError("Split must be train, validation, or test")
    if output.exists():
        raise ValueError(f"{output}: already exists; choose a new run output directory")
    frozen = verify_frozen(dataset)
    path = dataset / f"{split}.jsonl"
    incidents = read_incidents(path)
    source = Path(rules.__file__).read_bytes()
    revision = hashlib.sha256(source).hexdigest()
    dataset_sha256 = frozen.candidate.files[path.name].sha256
    run = RunManifest(
        run_id=f"rules-{revision[:12]}-{dataset_sha256[:12]}",
        backend_id="rules",
        revision=revision,
        tokenizer_revision=None,
        prompt_version="rules-v1-no-prompt",
        decoding_settings={},
        seed=0,
        dataset_sha256=dataset_sha256,
        environment={
            "python": platform.python_version(),
            "logmind": __version__,
            "dataset_version": frozen.dataset_version,
            "split": split,
            "frozen_manifest_sha256": hashlib.sha256(
                (dataset / "manifest.json").read_bytes()
            ).hexdigest(),
        },
    )
    records = []
    for incident in incidents:
        start = perf_counter()
        visible = incident.to_prompt_input()
        raw = rules.predict(visible).model_dump_json()
        record = parse_response(raw, visible, run, 0.0)
        record.elapsed_seconds = perf_counter() - start
        records.append(record)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".logmind-rules-", dir=output.parent) as temporary:
        staging = Path(temporary) / "run"
        staging.mkdir()
        write_jsonl(staging / "records.jsonl", records)
        write_jsonl(staging / "predictions.jsonl", [r.prediction for r in records if r.prediction])
        (staging / "run.json").write_text(json.dumps(run.model_dump(), indent=2) + "\n")
        (staging / "rules.py").write_bytes(source)
        for name in ("evaluation.py", "pipeline.py", "schemas.py"):
            (staging / name).write_bytes(Path(__file__).with_name(name).read_bytes())
        metrics, review = evaluate_files(path, staging / "records.jsonl")
        (staging / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
        (staging / "review-sample.jsonl").write_text(
            "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in review)
        )
        staging.rename(output)
    return metrics
