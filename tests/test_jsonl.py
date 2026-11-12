import pytest

from logmind.jsonl import JsonlError, read_incidents, read_jsonl, write_jsonl
from logmind.schemas import Incident


def test_utf8_roundtrip(tmp_path, incident):
    data = incident.model_dump()
    data["root_cause"] = "إعداد مفقود"
    record = Incident.model_validate(data)
    path = tmp_path / "records.jsonl"
    write_jsonl(path, [record])
    assert "إعداد مفقود" in path.read_text(encoding="utf-8")
    assert list(read_jsonl(path, Incident)) == [record]


@pytest.mark.parametrize("bad_line", ["\n", "not JSON\n", "{}\n"])
def test_error_reports_physical_line(tmp_path, incident, bad_line):
    path = tmp_path / "bad.jsonl"
    path.write_text(incident.model_dump_json() + "\n" + bad_line, encoding="utf-8")
    with pytest.raises(JsonlError, match=r"bad.jsonl:2:"):
        list(read_jsonl(path, Incident))


@pytest.mark.parametrize("problem", ["duplicate_id", "split_leakage", "empty"])
def test_dataset_constraints(tmp_path, incident, problem):
    path = tmp_path / "data.jsonl"
    data = incident.model_dump()
    if problem == "split_leakage":
        data.update(id="case-002", split="test")
    records = [] if problem == "empty" else [incident, Incident.model_validate(data)]
    write_jsonl(path, records)
    with pytest.raises(JsonlError):
        read_incidents(path)
