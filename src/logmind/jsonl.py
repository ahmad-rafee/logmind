"""UTF-8 JSONL utilities that report file and physical line on failure."""

from collections.abc import Iterable, Iterator
from pathlib import Path

from pydantic import BaseModel, ValidationError

from logmind.schemas import Incident


class JsonlError(ValueError):
    pass


def read_jsonl[T: BaseModel](path: Path, schema: type[T]) -> Iterator[T]:
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                raise JsonlError(f"{path}:{line_number}: blank JSONL record")
            try:
                yield schema.model_validate_json(line)
            except ValidationError as exc:
                raise JsonlError(f"{path}:{line_number}: {exc}") from exc


def write_jsonl(path: Path, records: Iterable[BaseModel]) -> None:
    """Write records without ASCII-escaping UTF-8 content."""
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for record in records:
            stream.write(record.model_dump_json() + "\n")


def read_incidents(path: Path) -> list[Incident]:
    """Validate dataset-wide identity and scenario split isolation."""
    records = list(read_jsonl(path, Incident))
    if not records:
        raise JsonlError(f"{path}: dataset must contain at least one incident")
    ids: set[str] = set()
    splits: dict[str, str] = {}
    for line, record in enumerate(records, start=1):
        if record.id in ids:
            raise JsonlError(f"{path}:{line}: duplicate incident ID: {record.id}")
        ids.add(record.id)
        previous = splits.setdefault(record.scenario_id, record.split)
        if previous != record.split:
            raise JsonlError(f"{path}:{line}: scenario crosses splits: {record.scenario_id}")
    return records
