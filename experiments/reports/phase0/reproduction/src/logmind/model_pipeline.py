"""Pinned zero-shot inference artifacts and the held-out baseline run."""

import hashlib
import json
import tempfile
from pathlib import Path
from time import perf_counter

from logmind import local_model, prompts
from logmind.freezing import verify_frozen
from logmind.jsonl import read_incidents, write_jsonl
from logmind.local_model import LocalModel, ModelConfig, read_config
from logmind.pipeline import evaluate_files
from logmind.schemas import RunManifest


def model_run_manifest(
    config: ModelConfig, model: LocalModel, checksum: str, split: str
) -> RunManifest:
    prompt_hash = hashlib.sha256(Path(prompts.__file__).read_bytes()).hexdigest()
    return RunManifest(
        run_id=f"qwen-{config.revision[:12]}-{checksum[:12]}-{prompt_hash[:12]}",
        backend_id=f"transformers/{config.model_id}",
        revision=config.revision,
        tokenizer_revision=config.tokenizer_revision,
        prompt_version=config.prompt_version,
        decoding_settings=config.model_dump(),
        seed=config.seed,
        dataset_sha256=checksum,
        environment={
            **model.environment,
            "split": split,
            "prompt_sha256": prompt_hash,
            "inference_source_sha256": hashlib.sha256(
                Path(local_model.__file__).read_bytes()
            ).hexdigest(),
        },
    )


def run_model(dataset: Path, output: Path, config_path: Path, split: str = "test") -> dict:
    if split not in {"train", "validation", "test"}:
        raise ValueError("Split must be train, validation, or test")
    if output.exists():
        raise ValueError(f"{output}: already exists; choose a new run directory")
    frozen = verify_frozen(dataset)
    config = read_config(config_path)
    incidents_path = dataset / f"{split}.jsonl"
    incidents = read_incidents(incidents_path)
    start = perf_counter()
    model = LocalModel(config)
    load_seconds = perf_counter() - start
    run = model_run_manifest(
        config, model, frozen.candidate.files[incidents_path.name].sha256, split
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".logmind-model-", dir=output.parent) as temporary:
        staging = Path(temporary) / "run"
        staging.mkdir()
        records = []
        telemetry = []
        for index, incident in enumerate(incidents, 1):
            record, measurement = model.predict(incident.to_prompt_input(), run)
            records.append(record)
            telemetry.append(measurement)
            valid = not (record.parse_errors or record.schema_errors or record.reference_errors)
            print(
                f"Model {index}/{len(incidents)}: {incident.id}; "
                f"{measurement['input_tokens']} in/{measurement['output_tokens']} out; "
                f"{measurement['elapsed_seconds']:.2f}s; "
                f"valid={valid}",
                flush=True,
            )
            # Keep progress artifacts in staging if execution needs inspection.
            write_jsonl(staging / "records.jsonl", records)
        write_jsonl(staging / "predictions.jsonl", [r.prediction for r in records if r.prediction])
        (staging / "telemetry.jsonl").write_text(
            "".join(json.dumps(item) + "\n" for item in telemetry)
        )
        (staging / "run.json").write_text(json.dumps(run.model_dump(), indent=2) + "\n")
        (staging / "config.json").write_bytes(config_path.read_bytes())
        for name in ("prompts.py", "local_model.py", "model_pipeline.py", "evaluation.py"):
            (staging / name).write_bytes(Path(__file__).with_name(name).read_bytes())
        metrics, review = evaluate_files(incidents_path, staging / "records.jsonl")
        metrics["model_load_seconds"] = load_seconds
        metrics["inference_errors"] = sum(item["inference_error"] is not None for item in telemetry)
        (staging / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
        (staging / "review-sample.jsonl").write_text(
            "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in review)
        )
        staging.rename(output)
    return metrics
