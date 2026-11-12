"""Validate completed preregistered worksheets and report reviewed rates honestly."""

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import model_validator

from logmind.jsonl import read_jsonl
from logmind.schemas import Category, JsonValue, Observation, Prediction, StrictModel, Text


class CompletedReview(StrictModel):
    incident_id: Text
    gold_category: Category
    observations: list[Observation]
    raw_response: str | None
    prediction: Prediction | None
    parse_errors: list[str]
    schema_errors: list[str]
    reference_errors: list[str]
    automatic_flags: list[dict[str, JsonValue]]
    valid: bool
    support_rating: Literal["supported", "partially_supported", "unsupported"]
    unsupported_factual_claim: bool
    recommendations_relevant: bool
    recommendations_safe: bool
    reviewer: Text
    reviewer_type: Literal["agent", "human"]
    review_date: Text
    notes: Text

    @model_validator(mode="after")
    def consistent_rating(self):
        if self.support_rating == "supported" and self.unsupported_factual_claim:
            raise ValueError("A supported rating cannot include unsupported factual claims")
        return self


EDITABLE_FIELDS = {
    "support_rating",
    "unsupported_factual_claim",
    "recommendations_relevant",
    "recommendations_safe",
    "reviewer",
    "reviewer_type",
    "review_date",
    "notes",
}


def summarize_reviews(sample_path: Path, completed_path: Path) -> dict:
    sample = [json.loads(line) for line in sample_path.read_text().splitlines()]
    completed = list(read_jsonl(completed_path, CompletedReview))
    original = {row["incident_id"]: row for row in sample}
    if not sample or len(original) != len(sample):
        raise ValueError("Review sample must be nonempty with unique IDs")
    if len(completed) != len(sample) or {row.incident_id for row in completed} != set(original):
        raise ValueError(
            "Complete exactly the preregistered sample, without additions or omissions"
        )
    if len({row.incident_id for row in completed}) != len(completed):
        raise ValueError("Duplicate completed review IDs")
    for row in completed:
        preserved = {
            key: value for key, value in row.model_dump().items() if key not in EDITABLE_FIELDS
        }
        expected = {
            key: value
            for key, value in original[row.incident_id].items()
            if key not in EDITABLE_FIELDS
        }
        if preserved != expected:
            raise ValueError(f"{row.incident_id}: original review facts/output were modified")
    numerator = sum(row.unsupported_factual_claim for row in completed)
    denominator = len(completed)
    return {
        "reviewed_predictions": denominator,
        "unsupported_factual_claims": numerator,
        "reviewed_hallucination_rate": numerator / denominator,
        "support_ratings": dict(Counter(row.support_rating for row in completed)),
        "relevant_recommendations": sum(row.recommendations_relevant for row in completed),
        "safe_recommendations": sum(row.recommendations_safe for row in completed),
        "reviewers": sorted({row.reviewer for row in completed}),
        "reviewer_types": sorted({row.reviewer_type for row in completed}),
        "review_dates": sorted({row.review_date for row in completed}),
        "sample_sha256": hashlib.sha256(sample_path.read_bytes()).hexdigest(),
        "completed_review_sha256": hashlib.sha256(completed_path.read_bytes()).hexdigest(),
        "limitations": (
            "Single-reviewer results when only one identity is listed. Agent review is "
            "not independent human review. This unweighted stratified sample "
            "intentionally includes invalid/abstained outputs and correlated synthetic "
            "variants; its rate is not an unbiased production estimate."
        ),
    }
