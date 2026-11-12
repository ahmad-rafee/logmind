"""Matched fixed-subset, cold-process and warmed benchmark orchestration."""

import hashlib
import json
import statistics
import subprocess
import sys
from pathlib import Path

from logmind.freezing import verify_frozen
from logmind.jsonl import read_incidents, write_jsonl


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    location = (len(ordered) - 1) * fraction
    lower = int(location)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (location - lower)


def summarize(results: list[dict]) -> dict:
    measurements = [item["measurement"] for item in results]
    latencies = [item["elapsed_seconds"] for item in measurements]
    summary = {
        "n_measurements": len(results),
        "median_seconds": statistics.median(latencies),
        "p95_seconds": percentile(latencies, 0.95),
        "peak_rss_bytes": max(item["peak_rss_bytes"] for item in measurements),
        "inference_errors": sum(item["inference_error"] is not None for item in measurements),
        "valid_outputs": sum(
            not (
                item["record"]["parse_errors"]
                or item["record"]["schema_errors"]
                or item["record"]["reference_errors"]
            )
            for item in results
        ),
    }
    for field in ("gpu_peak_allocated_bytes", "gpu_peak_reserved_bytes"):
        available = [item[field] for item in measurements if item[field] is not None]
        summary[field] = max(available) if available else None
    for field in ("input_tokens", "output_tokens", "generated_tokens_per_second"):
        available = [item[field] for item in measurements if item[field] is not None]
        summary[field] = (
            {"median": statistics.median(available), "min": min(available), "max": max(available)}
            if available
            else None
        )
    return summary


def run_benchmark(dataset: Path, output: Path, config: Path, repetitions: int = 3) -> dict:
    if repetitions < 3:
        raise ValueError("At least three repetitions are required")
    if output.exists():
        raise ValueError(f"{output}: benchmark output exists; choose a new directory")
    frozen = verify_frozen(dataset)
    records = read_incidents(dataset / "test.jsonl")
    # Selection is fixed by label and hash before inspecting any predictions/scores.
    subset = []
    for category in sorted({item.category for item in records}):
        subset.append(
            min(
                (item for item in records if item.category == category),
                key=lambda item: hashlib.sha256(f"42:{item.id}".encode()).hexdigest(),
            )
        )
    output.mkdir(parents=True)
    inputs = output / "inputs.jsonl"
    write_jsonl(inputs, subset)
    report = {
        "dataset_version": frozen.dataset_version,
        "frozen_manifest_sha256": hashlib.sha256(
            (dataset / "manifest.json").read_bytes()
        ).hexdigest(),
        "subset_sha256": hashlib.sha256(inputs.read_bytes()).hexdigest(),
        "incident_ids": [item.id for item in subset],
        "repetitions": repetitions,
        "policy": (
            "One hash-selected held-out incident per category, seed 42. Cold: new Python "
            "process/model per incident/repetition, including imports/load/first "
            "prediction; OS file cache is not flushed. Warm: one loaded process per "
            "backend, one discarded warm-up, then three complete repetitions. End-to-end "
            "prompt assembly/inference/parsing, including instrumentation. RSS sampled "
            "every 10ms plus process-lifetime peak for cold; CUDA peaks from PyTorch. p95 "
            "uses linear interpolation. Rules have no tokenizer/output-token throughput."
        ),
        "backends": {},
    }
    config_path = config.resolve()
    for backend in ("rules", "model"):
        destination = output / backend
        destination.mkdir()
        cold_results = []
        base = [
            sys.executable,
            "-m",
            "logmind.benchmark_worker",
            "--backend",
            backend,
            "--inputs",
            str(inputs.resolve()),
            "--config",
            str(config_path),
        ]
        for repetition in range(1, repetitions + 1):
            for incident in subset:
                path = destination / f"cold-{repetition}-{incident.id}.json"
                subprocess.run(
                    base
                    + [
                        "--mode",
                        "cold",
                        "--incident-id",
                        incident.id,
                        "--output",
                        str(path.resolve()),
                    ],
                    check=True,
                )
                data = json.loads(path.read_text())
                data["results"][0]["repetition"] = repetition
                cold_results.extend(data["results"])
                print(
                    f"Benchmark {backend} cold {repetition}/{repetitions}: {incident.id}",
                    flush=True,
                )
        warm_path = destination / "warm.json"
        subprocess.run(
            base
            + [
                "--mode",
                "warm",
                "--repetitions",
                str(repetitions),
                "--output",
                str(warm_path.resolve()),
            ],
            check=True,
        )
        warm_data = json.loads(warm_path.read_text())
        report["backends"][backend] = {
            "run": warm_data["run"],
            "cold": summarize(cold_results),
            "warm": summarize(warm_data["results"]),
        }
        (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
        print(f"Benchmark {backend} complete", flush=True)
    return report
