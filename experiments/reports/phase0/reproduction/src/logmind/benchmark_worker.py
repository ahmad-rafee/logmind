"""Fresh-process benchmark worker; invoked by logmind.benchmark, not imported by core CLI."""

from time import perf_counter

PROCESS_START = perf_counter()


def main():
    import argparse
    import hashlib
    import json
    import platform
    import resource
    from pathlib import Path

    from logmind.evaluation import parse_response
    from logmind.jsonl import read_incidents
    from logmind.local_model import LocalModel, MemoryMonitor, read_config
    from logmind.model_pipeline import model_run_manifest
    from logmind.rules import predict
    from logmind.schemas import RunManifest

    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", choices=["rules", "model"], required=True)
    parser.add_argument("--mode", choices=["cold", "warm"], required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--incident-id")
    parser.add_argument("--repetitions", type=int, default=3)
    args = parser.parse_args()
    inputs = read_incidents(args.inputs)
    checksum = hashlib.sha256(args.inputs.read_bytes()).hexdigest()
    model = None
    if args.backend == "model":
        model = LocalModel(read_config(args.config))
        run = model_run_manifest(model.config, model, checksum, f"benchmark-{args.mode}")
    else:
        from logmind import rules

        run = RunManifest(
            run_id="rules-benchmark",
            backend_id="rules",
            revision=hashlib.sha256(Path(rules.__file__).read_bytes()).hexdigest(),
            tokenizer_revision=None,
            prompt_version="rules-v1-no-prompt",
            decoding_settings={},
            seed=42,
            dataset_sha256=checksum,
            environment={"python": platform.python_version()},
        )

    def measure(incident):
        if model:
            return model.predict(
                incident.to_prompt_input(), run, reset_peak_memory=args.mode != "cold"
            )
        start = perf_counter()
        with MemoryMonitor() as monitor:
            visible = incident.to_prompt_input()
            record = parse_response(predict(visible).model_dump_json(), visible, run, 0.0)
            record.elapsed_seconds = perf_counter() - start
        return record, {
            "incident_id": incident.id,
            "input_tokens": None,
            "output_tokens": None,
            "elapsed_seconds": record.elapsed_seconds,
            "generated_tokens_per_second": None,
            "peak_rss_bytes": monitor.peak,
            "process_lifetime_peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            * 1024,
            "gpu_peak_allocated_bytes": None,
            "gpu_peak_reserved_bytes": None,
            "inference_error": None,
        }

    results = []
    warmup = None
    if args.mode == "cold":
        incident = next(item for item in inputs if item.id == args.incident_id)
        record, telemetry = measure(incident)
        telemetry["prediction_elapsed_seconds"] = telemetry["elapsed_seconds"]
        telemetry["elapsed_seconds"] = perf_counter() - PROCESS_START
        telemetry["peak_rss_bytes"] = telemetry["process_lifetime_peak_rss_bytes"]
        if telemetry["output_tokens"] is not None:
            telemetry["generated_tokens_per_second"] = (
                telemetry["output_tokens"] / telemetry["elapsed_seconds"]
            )
        results.append({"repetition": 1, "record": record.model_dump(), "measurement": telemetry})
    else:
        record, telemetry = measure(inputs[0])
        warmup = {"record": record.model_dump(), "measurement": telemetry}
        for repetition in range(1, args.repetitions + 1):
            for incident in inputs:
                record, telemetry = measure(incident)
                results.append(
                    {
                        "repetition": repetition,
                        "record": record.model_dump(),
                        "measurement": telemetry,
                    }
                )
    args.output.write_text(
        json.dumps(
            {
                "backend": args.backend,
                "mode": args.mode,
                "run": run.model_dump(),
                "warmup": warmup,
                "results": results,
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
