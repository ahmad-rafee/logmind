"""Command-line entry points for the implemented Phase 0 contracts."""

import json
from pathlib import Path
from typing import Annotated

import typer

from logmind import __version__
from logmind.freezing import freeze_dataset, verify_frozen
from logmind.generation import generate_dataset
from logmind.jsonl import read_incidents, read_jsonl
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
