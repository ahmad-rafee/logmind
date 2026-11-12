import json

import pytest

from logmind.evaluation import parse_response, prepare_review
from logmind.review import summarize_reviews
from logmind.schemas import RunManifest


def worksheet(tmp_path, incident, prediction):
    run = RunManifest(
        run_id="review-unit",
        backend_id="unit",
        revision="source",
        tokenizer_revision=None,
        prompt_version="unit",
        decoding_settings={},
        seed=42,
        dataset_sha256="0" * 64,
        environment={},
    )
    record = parse_response(prediction.model_dump_json(), incident.to_prompt_input(), run, 0.01)
    sample = prepare_review([incident], [record])
    sample_path = tmp_path / "sample.jsonl"
    sample_path.write_text(json.dumps(sample[0]) + "\n")
    completed = dict(sample[0])
    completed.update(
        support_rating="supported",
        unsupported_factual_claim=False,
        recommendations_relevant=True,
        recommendations_safe=True,
        reviewer="unit-reviewer",
        reviewer_type="agent",
        review_date="2026-11-12",
        notes="Claims match the selected observations.",
    )
    completed_path = tmp_path / "completed.jsonl"
    completed_path.write_text(json.dumps(completed) + "\n")
    return sample_path, completed_path, completed


def test_review_reports_numerator_denominator_and_reviewer_type(tmp_path, incident, prediction):
    sample, completed, _ = worksheet(tmp_path, incident, prediction)
    report = summarize_reviews(sample, completed)
    assert report["unsupported_factual_claims"] == 0
    assert report["reviewed_predictions"] == 1
    assert report["reviewer_types"] == ["agent"]


@pytest.mark.parametrize("problem", ["facts", "missing", "unfinished", "inconsistent"])
def test_review_rejects_modified_sample_or_unfinished_ratings(
    tmp_path, incident, prediction, problem
):
    sample, path, completed = worksheet(tmp_path, incident, prediction)
    if problem == "facts":
        completed["raw_response"] = "changed output"
    elif problem == "unfinished":
        completed["unsupported_factual_claim"] = None
    elif problem == "inconsistent":
        completed["unsupported_factual_claim"] = True
    path.write_text("" if problem == "missing" else json.dumps(completed) + "\n")
    with pytest.raises(ValueError):
        summarize_reviews(sample, path)
