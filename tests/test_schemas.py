import json

import pytest
from pydantic import ValidationError

from logmind.schemas import Incident, Prediction, PredictionRecord, RunManifest


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("uncertain", "false"),
        ("uncertain", 0),
        ("category", "other"),
        ("extra", True),
        ("root_cause", "   "),
        ("evidence_ids", "event-2"),
    ],
)
def test_prediction_rejects_invalid_types_and_fields(prediction, field, value):
    data = prediction.model_dump()
    data[field] = value
    with pytest.raises(ValidationError):
        Prediction.model_validate_json(json.dumps(data))


@pytest.mark.parametrize("field", list(Prediction.model_fields))
def test_prediction_requires_every_field(prediction, field):
    data = prediction.model_dump()
    del data[field]
    with pytest.raises(ValidationError):
        Prediction.model_validate(data)


def test_prompt_input_excludes_all_ground_truth(incident):
    prompt = incident.to_prompt_input().model_dump()
    assert set(prompt) == {"incident_id", "observations"}
    assert prompt["observations"] == [item.model_dump() for item in incident.observations]


@pytest.mark.parametrize("problem", ["duplicate", "unknown", "excerpt"])
def test_incident_rejects_bad_evidence(incident, problem):
    data = incident.model_dump()
    if problem == "duplicate":
        data["observations"].append(data["observations"][0])
    elif problem == "unknown":
        data["evidence"][0]["observation_id"] = "event-999"
    else:
        data["evidence"][0]["excerpt"] = "invented excerpt"
    with pytest.raises(ValidationError):
        Incident.model_validate(data)


def test_prediction_reference_validation(incident, prediction):
    prediction.validate_against(incident.to_prompt_input())
    prediction.evidence_ids = ["event-999"]
    with pytest.raises(ValueError, match="Unknown predicted evidence"):
        prediction.validate_against(incident.to_prompt_input())
    prediction.incident_id = "other"
    with pytest.raises(ValueError, match="does not match"):
        prediction.validate_against(incident.to_prompt_input())


def test_failed_output_is_preserved(incident):
    run = RunManifest(
        run_id="run-1",
        backend_id="rules",
        revision="rules-v1",
        tokenizer_revision=None,
        prompt_version="none",
        decoding_settings={},
        seed=42,
        dataset_sha256="a" * 64,
        environment={"python": "3.12"},
    )
    record = PredictionRecord(
        incident_id=incident.id,
        run=run,
        raw_response="not JSON",
        prediction=None,
        parse_errors=["Invalid JSON"],
        schema_errors=[],
        reference_errors=[],
        elapsed_seconds=0.1,
    )
    assert record.raw_response == "not JSON"
    assert record.prediction is None
    data = record.model_dump()
    data["parse_errors"] = []
    with pytest.raises(ValidationError, match="must retain"):
        PredictionRecord.model_validate(data)


def test_inconsistent_envelope_rejected(incident, prediction):
    data = {
        "incident_id": "other",
        "run": {
            "run_id": "run-1",
            "backend_id": "rules",
            "revision": "rules-v1",
            "tokenizer_revision": None,
            "prompt_version": "none",
            "decoding_settings": {},
            "seed": 0,
            "dataset_sha256": "a" * 64,
            "environment": {},
        },
        "raw_response": prediction.model_dump_json(),
        "prediction": prediction.model_dump(),
        "parse_errors": [],
        "schema_errors": [],
        "reference_errors": [],
        "elapsed_seconds": 0.1,
    }
    with pytest.raises(ValidationError, match="IDs differ"):
        PredictionRecord.model_validate(data)
