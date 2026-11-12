"""Command-line entry points for the implemented Phase 0 contracts."""

import json
from pathlib import Path

import typer

from logmind import __version__
from logmind.jsonl import read_incidents, read_jsonl
from logmind.schemas import Incident, Prediction, PredictionRecord, PromptInput, RunManifest

app = typer.Typer(no_args_is_help=True)


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
        for schema in (Incident, PromptInput, Prediction, RunManifest, PredictionRecord):
            target = output / f"{schema.__name__}.schema.json"
            target.write_text(json.dumps(schema.model_json_schema(), indent=2) + "\n")
    except OSError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"Exported schemas to {output}.")
