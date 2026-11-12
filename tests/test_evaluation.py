import json

import pytest

from logmind.evaluation import automatic_flags, evaluate, parse_response, prepare_review
from logmind.schemas import Incident, Observation, Prediction, RunManifest


def run():
    return RunManifest(
        run_id="unit-run",
        backend_id="unit",
        revision="unit-source",
        tokenizer_revision=None,
        prompt_version="unit",
        decoding_settings={},
        seed=42,
        dataset_sha256="0" * 64,
        environment={},
    )


def case(identifier, category, tags=None):
    return Incident(
        id=identifier,
        scenario_id=identifier,
        split="validation",
        source="synthetic",
        category=category,
        root_cause="Unit ground truth.",
        observations=[
            Observation(id="obs", kind="termination", text="exitCode=1", details={"exit_code": 1})
        ],
        evidence=[],
        expected_actions=[],
        variant_tags=tags or ["baseline"],
    )


def response(incident, category):
    return Prediction(
        incident_id=incident.id,
        category=category,
        root_cause="Supported unit claim.",
        evidence_ids=["obs"],
        explanation="Unit explanation.",
        recommended_checks=["Inspect logs."],
        uncertain=category == "insufficient_evidence",
    ).model_dump_json()


def record(incident, category):
    return parse_response(response(incident, category), incident.to_prompt_input(), run(), 0.01)


def test_hand_calculated_accuracy_f1_and_abstention_behavior():
    a = case("a", "container_crash")
    b = case("b", "container_crash")
    c = case("c", "oom_killed")
    d = case("d", "insufficient_evidence", ["missing_diagnostics"])
    metrics = evaluate(
        [a, b, c, d],
        [
            record(a, "container_crash"),
            record(b, "insufficient_evidence"),
            record(c, "container_crash"),
            record(d, "insufficient_evidence"),
        ],
    )
    assert metrics["accuracy"] == 0.5
    assert metrics["answerable_accuracy"] == pytest.approx(1 / 3)
    assert metrics["per_class"]["container_crash"] == {
        "support": 2,
        "precision": 0.5,
        "recall": 0.5,
        "f1": 0.5,
    }
    assert metrics["macro_f1_six_classes"] == pytest.approx(0.5 / 6)
    assert metrics["answerable_abstentions"] == 1
    assert metrics["correct_abstention_rate"] == 1.0
    assert metrics["abstention_groups"]["missing_diagnostics"]["support"] == 1
    assert metrics["abstention_groups"]["target_ambiguity"]["correct_abstention_rate"] is None


@pytest.mark.parametrize("failure", ["parse", "schema", "reference", "missing"])
def test_invalid_and_missing_predictions_are_wrong_in_full_denominator(failure):
    incident = case("a", "container_crash")
    raw = response(incident, "container_crash")
    if failure == "parse":
        raw = "not JSON"
    elif failure == "schema":
        data = json.loads(raw)
        data["extra"] = True
        raw = json.dumps(data)
    elif failure == "reference":
        data = json.loads(raw)
        data["evidence_ids"] = ["invented"]
        raw = json.dumps(data)
    outputs = (
        []
        if failure == "missing"
        else [parse_response(raw, incident.to_prompt_input(), run(), 0.01)]
    )
    metrics = evaluate([incident], outputs)
    assert metrics["accuracy"] == metrics["macro_f1_six_classes"] == 0.0
    assert metrics["valid_output_rate"] == 0.0
    assert metrics["confusion_matrix"]["container_crash"]["invalid"] == 1
    if failure == "reference":
        assert metrics["strict_schema_success_rate"] == 1.0
        assert metrics["automatic_flags_by_code"]["nonexistent_evidence_id"] == 1


def test_raw_response_is_authoritative_not_claimed_parsed_prediction():
    incident = case("a", "container_crash")
    output = record(incident, "container_crash")
    output.raw_response = "broken JSON"
    assert evaluate([incident], [output])["accuracy"] == 0.0


def test_duplicate_unknown_and_mixed_run_records_are_rejected():
    incident = case("a", "container_crash")
    output = record(incident, "container_crash")
    with pytest.raises(ValueError, match="duplicate"):
        evaluate([incident], [output, output])
    with pytest.raises(ValueError, match="Unknown"):
        evaluate([incident], [record(case("unknown", "container_crash"), "container_crash")])
    other = case("b", "oom_killed")
    second = record(other, "oom_killed")
    second.run.run_id = "another-run"
    with pytest.raises(ValueError, match="one run"):
        evaluate([incident, other], [output, second])


def test_flags_are_specific_review_aids_not_hallucination_measurements():
    incident = case("a", "container_crash")
    output = record(incident, "container_crash")
    output.prediction.root_cause = 'Pod "invented-pod" terminated with exitCode=137.'
    flags = automatic_flags(incident.to_prompt_input(), output.prediction)
    assert {flag["code"] for flag in flags} == {
        "unobserved_named_resource",
        "contradictory_exit_code",
    }
    assert evaluate([incident], [output])["reviewed_hallucination_rate"] is None


def test_review_sample_is_deterministic_and_includes_invalid_and_abstained_outputs():
    incidents = [case(str(i), "container_crash") for i in range(5)]
    outputs = [record(incident, "container_crash") for incident in incidents]
    outputs[0].raw_response = "broken JSON"
    outputs[1] = record(incidents[1], "insufficient_evidence")
    sample = prepare_review(incidents, outputs)
    assert {item["incident_id"] for item in sample} == {"0", "1"}
    assert prepare_review(list(reversed(incidents)), list(reversed(outputs))) == sample
    assert all(item["reviewer"] is None for item in sample)


def test_nonstandard_json_constants_are_parse_failures():
    incident = case("a", "container_crash")
    output = parse_response("NaN", incident.to_prompt_input(), run(), 0.0)
    assert output.parse_errors and output.prediction is None
