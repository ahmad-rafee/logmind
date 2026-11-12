"""Command-line entry points for the implemented Phase 0 contracts."""

import json
from pathlib import Path
from typing import Annotated

import typer

from logmind import __version__
from logmind.freezing import freeze_dataset, verify_frozen
from logmind.generation import generate_dataset
from logmind.jsonl import read_incidents, read_jsonl
from logmind.pipeline import evaluate_files, run_rules
from logmind.schemas import (
    DatasetManifest,
    FrozenDatasetManifest,
    Incident,
    Prediction,
    PredictionRecord,
    PromptInput,
    RunManifest,
)

app = typer.Typer(no_args_is_help=True)


@app.command()
def review_summary(
    sample: Path,
    completed: Path,
    output: Annotated[Path, typer.Option(help="New review summary JSON")],
) -> None:
    """Validate the entire fixed review sample and compute its numerator/denominator."""
    from logmind.review import summarize_reviews

    report = summarize_reviews(sample, completed)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    typer.echo(
        f"Reviewed unsupported claims: {report['unsupported_factual_claims']}/"
        f"{report['reviewed_predictions']}; reviewers: {report['reviewers']}"
    )


@app.command()
def download_model(
    config: Annotated[Path, typer.Option()] = Path(
        "experiments/configs/qwen3-1.7b-zero-shot-v1.json"
    ),
) -> None:
    """Download exact public model/tokenizer revisions into the Hugging Face cache."""
    from huggingface_hub import snapshot_download

    from logmind.local_model import read_config

    settings = read_config(config)
    for revision in sorted({settings.revision, settings.tokenizer_revision}):
        path = snapshot_download(
            settings.model_id,
            revision=revision,
            max_workers=2,
            allow_patterns=["*.json", "*.safetensors", "merges.txt", "vocab.json", "LICENSE"],
        )
        typer.echo(path)


@app.command()
def predict_model(
    output: Annotated[Path, typer.Option(help="New model run directory")],
    dataset: Annotated[Path, typer.Option()] = Path("data/frozen/v1"),
    config: Annotated[Path, typer.Option()] = Path(
        "experiments/configs/qwen3-1.7b-zero-shot-v1.json"
    ),
    split: Annotated[str, typer.Option()] = "test",
) -> None:
    """Run the fixed zero-shot model without response repair or input truncation."""
    from logmind.model_pipeline import run_model

    metrics = run_model(dataset, output, config, split)
    typer.echo(
        f"Model {split}: N={metrics['n']}, accuracy={metrics['accuracy']:.3f}, "
        f"macro-F1={metrics['macro_f1_six_classes']:.3f}."
    )


@app.command()
def benchmark(
    output: Annotated[Path, typer.Option(help="New benchmark directory")],
    dataset: Annotated[Path, typer.Option()] = Path("data/frozen/v1"),
    config: Annotated[Path, typer.Option()] = Path(
        "experiments/configs/qwen3-1.7b-zero-shot-v1.json"
    ),
    repetitions: Annotated[int, typer.Option(min=3)] = 3,
) -> None:
    """Benchmark identical hash-selected inputs with fresh cold and warmed processes."""
    from logmind.benchmark import run_benchmark

    run_benchmark(dataset, output, config, repetitions)
    typer.echo(f"Benchmark complete: {output}")


@app.command()
def predict_rules(
    output: Annotated[Path, typer.Option(help="New run directory")],
    dataset: Annotated[Path, typer.Option(help="Verified frozen release")] = Path("data/frozen/v1"),
    split: Annotated[
        str, typer.Option(help="train, validation, or explicitly test")
    ] = "validation",
) -> None:
    """Run the CPU rules baseline, save raw records, metrics, and a review worksheet."""
    try:
        metrics = run_rules(dataset, output, split)
    except (OSError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    typer.echo(
        f"Rules {split}: N={metrics['n']}, accuracy={metrics['accuracy']:.3f}, "
        f"macro-F1={metrics['macro_f1_six_classes']:.3f}. Output: {output}"
    )


@app.command("evaluate")
def evaluate_command(
    incidents: Path,
    records: Path,
    output: Annotated[Path, typer.Option(help="New metrics JSON file")],
) -> None:
    """Score authoritative PredictionRecord JSONL, retaining invalid/missing outputs in N."""
    try:
        if output.exists():
            raise ValueError(f"{output}: already exists; choose a new output path")
        metrics, _ = evaluate_files(incidents, records)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(metrics, indent=2) + "\n")
    except (OSError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"Evaluated {metrics['n']} incidents. Output: {output}")


@app.command()
def freeze(
    candidate: Annotated[Path, typer.Option(help="Candidate dataset directory")] = Path(
        "data/generated/v1-seed42"
    ),
    output: Annotated[Path, typer.Option(help="New frozen release directory")] = Path(
        "data/frozen/v1"
    ),
    templates: Annotated[Path, typer.Option(help="Reviewed baseline directory")] = Path(
        "data/scenarios/templates"
    ),
    project: Annotated[Path, typer.Option(help="Project source/dependency root")] = Path("."),
    dataset_version: Annotated[str, typer.Option(help="Frozen version label")] = "v1",
) -> None:
    """Audit candidate reproducibility and create a versioned frozen snapshot."""
    try:
        manifest = freeze_dataset(candidate, output, templates, project, dataset_version)
    except (OSError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    typer.echo(
        f"Frozen {manifest.dataset_version}: {manifest.candidate.records} records at {output}."
    )


@app.command()
def verify_dataset(
    path: Path,
    expected_sha256: Annotated[
        str | None, typer.Option(help="External manifest SHA-256 pin")
    ] = None,
) -> None:
    """Verify frozen data, split membership, provenance, and artifact checksums."""
    try:
        manifest = verify_frozen(path, expected_sha256)
    except (OSError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"Verified frozen {manifest.dataset_version}: {manifest.candidate.records} records.")


@app.command()
def generate(
    output: Annotated[Path | None, typer.Option(help="Candidate output directory")] = None,
    seed: Annotated[int, typer.Option(help="Local random seed")] = 42,
    templates: Annotated[Path, typer.Option(help="42 reviewed baselines")] = Path(
        "data/scenarios/templates"
    ),
) -> None:
    """Generate 150 reproducible incidents, split files, and a checksum manifest."""
    output = output if output is not None else Path(f"data/generated/v1-seed{seed}")
    try:
        manifest = generate_dataset(templates, output, seed)
    except (OSError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    typer.echo(
        f"Generated {manifest.records} candidate incidents from {manifest.scenarios} scenarios."
    )
    typer.echo(f"Output: {output}; seed: {seed}; splits: {manifest.records_by_split}")


@app.command()
def version() -> None:
    """Print the installed package version."""
    typer.echo(__version__)


@app.command()
def validate_incidents(path: Path) -> None:
    """Validate incident schemas, evidence, IDs, and scenario split isolation."""
    try:
        records = read_incidents(path)
    except (OSError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"Validated {len(records)} incidents.")


@app.command()
def validate_predictions(path: Path, incidents: Path) -> None:
    """Validate prediction JSONL and references against the supplied incidents."""
    try:
        inputs = {item.id: item.to_prompt_input() for item in read_incidents(incidents)}
        seen: set[str] = set()
        for line, prediction in enumerate(read_jsonl(path, Prediction), start=1):
            if prediction.incident_id not in inputs:
                raise ValueError(f"{path}:{line}: unknown incident: {prediction.incident_id}")
            if prediction.incident_id in seen:
                raise ValueError(f"{path}:{line}: duplicate prediction: {prediction.incident_id}")
            try:
                prediction.validate_against(inputs[prediction.incident_id])
            except ValueError as exc:
                raise ValueError(f"{path}:{line}: {exc}") from exc
            seen.add(prediction.incident_id)
        if not seen:
            raise ValueError(f"{path}: prediction file must contain at least one record")
    except (OSError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"Validated {len(seen)} predictions (coverage {len(seen)}/{len(inputs)}).")


@app.command()
def export_schemas(output: Path) -> None:
    """Export JSON Schema contracts to a directory."""
    try:
        output.mkdir(parents=True, exist_ok=True)
        for schema in (
            Incident,
            PromptInput,
            Prediction,
            RunManifest,
            PredictionRecord,
            DatasetManifest,
            FrozenDatasetManifest,
        ):
            target = output / f"{schema.__name__}.schema.json"
            target.write_text(json.dumps(schema.model_json_schema(), indent=2) + "\n")
    except OSError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"Exported schemas to {output}.")
