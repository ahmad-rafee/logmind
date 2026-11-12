from pathlib import Path

import pytest

from logmind.jsonl import read_incidents
from logmind.schemas import Incident, Prediction


@pytest.fixture
def incident() -> Incident:
    return read_incidents(Path(__file__).parent / "fixtures" / "incident.jsonl")[0]


@pytest.fixture
def prediction(incident: Incident) -> Prediction:
    return Prediction(
        incident_id=incident.id,
        category="missing_config",
        root_cause=incident.root_cause,
        evidence_ids=["event-2"],
        explanation="The FailedMount event identifies the missing ConfigMap.",
        recommended_checks=incident.expected_actions,
        uncertain=False,
    )
