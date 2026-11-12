from pathlib import Path

import pytest

from logmind.jsonl import read_incidents
from logmind.rules import predict
from logmind.schemas import Observation, PromptInput

ROOT = Path(__file__).resolve().parents[1]


def visible(*observations):
    return PromptInput(incident_id="opaque-case", observations=list(observations))


@pytest.mark.parametrize("split", ["train", "validation"])
def test_rules_on_development_splits_only(split):
    for incident in read_incidents(ROOT / f"data/frozen/v1/{split}.jsonl"):
        result = predict(incident.to_prompt_input())
        assert result.category == incident.category, incident.id
        result.validate_against(incident.to_prompt_input())


def test_rules_do_not_read_gold_or_depend_on_observation_order():
    incident = read_incidents(ROOT / "data/frozen/v1/train.jsonl")[0]
    first = predict(incident.to_prompt_input())
    incident.category = "insufficient_evidence"
    incident.root_cause = "Unrelated hidden annotation."
    incident.scenario_id = "unrelated"
    incident.evidence = []
    incident.expected_actions = []
    incident.observations.reverse()
    assert predict(incident.to_prompt_input()) == first


def test_exit_137_and_backoff_alone_do_not_establish_oom():
    incident = visible(
        Observation(
            id="status",
            kind="termination",
            text="exitCode=137; restartCount=3",
            details={"exit_code": 137},
        )
    )
    assert predict(incident).category == "insufficient_evidence"


def test_old_oom_cannot_override_selected_attempt():
    incident = visible(
        Observation(
            id="scope",
            kind="metadata",
            text="Selected attempt 3.",
            details={
                "source": "supplied_target_selection",
                "container": "api",
                "attempt": 3,
            },
        ),
        Observation(
            id="old",
            kind="termination",
            text="reason=OOMKilled",
            details={
                "container": "api",
                "attempt": 1,
                "reason": "OOMKilled",
                "exit_code": 137,
            },
        ),
        Observation(
            id="current",
            kind="status",
            text="CrashLoopBackOff",
            details={
                "container": "api",
                "attempt": 3,
            },
        ),
    )
    assert predict(incident).category == "insufficient_evidence"


def test_probe_restart_is_not_misclassified_as_application_crash():
    incident = visible(
        Observation(id="event", kind="event", text="Liveness probe failed: timeout."),
        Observation(id="term", kind="termination", text="exitCode=143", details={"exit_code": 143}),
    )
    assert predict(incident).category == "probe_failure"


def test_conflicting_causes_and_healthy_completion_abstain():
    incident = visible(
        Observation(
            id="oom", kind="termination", text="reason=OOMKilled", details={"reason": "OOMKilled"}
        ),
        Observation(id="image", kind="event", text='Failed to pull image "demo": unauthorized.'),
    )
    assert predict(incident).uncertain
    completed = visible(
        Observation(
            id="term",
            kind="termination",
            text="Completed",
            details={"reason": "Completed", "exit_code": 0},
        )
    )
    assert predict(completed).category == "insufficient_evidence"


def test_unexpected_json_metadata_types_do_not_crash_rules():
    incident = visible(
        Observation(
            id="metadata",
            kind="metadata",
            text="Incomplete snapshot.",
            details={
                "source": "target_selection",
                "container": ["not", "a", "name"],
                "attempt": {},
            },
        )
    )
    assert predict(incident).uncertain
