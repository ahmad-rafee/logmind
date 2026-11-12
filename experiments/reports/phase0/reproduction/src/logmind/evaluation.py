"""Full-denominator metrics and conservative flags; no automatic hallucination rate."""

import hashlib
import json
import re
from collections import Counter
from typing import get_args

from pydantic import ValidationError

from logmind.rules import selected_observations
from logmind.schemas import (
    Category,
    Incident,
    Prediction,
    PredictionRecord,
    PromptInput,
    RunManifest,
)

CLASSES = [label for label in get_args(Category) if label != "insufficient_evidence"]
LABELS = CLASSES + ["insufficient_evidence"]


def _reject_constant(value: str) -> None:
    raise ValueError(f"Invalid JSON constant: {value}")


def parse_response(
    raw: str, incident: PromptInput, run: RunManifest, elapsed: float
) -> PredictionRecord:
    prediction = None
    parse_errors = []
    schema_errors = []
    reference_errors = []
    try:
        json.loads(raw, parse_constant=_reject_constant)
    except (json.JSONDecodeError, ValueError) as exc:
        parse_errors.append(str(exc))
    if not parse_errors:
        try:
            prediction = Prediction.model_validate_json(raw)
        except ValidationError as exc:
            schema_errors.append(str(exc))
    if prediction is not None:
        try:
            prediction.validate_against(incident)
        except ValueError as exc:
            reference_errors.append(str(exc))
    return PredictionRecord(
        incident_id=incident.incident_id,
        run=run,
        raw_response=raw,
        prediction=prediction,
        parse_errors=parse_errors,
        schema_errors=schema_errors,
        reference_errors=reference_errors,
        elapsed_seconds=elapsed,
    )


def automatic_flags(incident: PromptInput, prediction: Prediction) -> list[dict]:
    flags = []
    known = {item.id for item in incident.observations}
    for identifier in sorted(set(prediction.evidence_ids) - known):
        flags.append({"code": "nonexistent_evidence_id", "value": identifier})
    claims = " ".join(
        [prediction.root_cause, prediction.explanation, *prediction.recommended_checks]
    )
    tokens = set(re.findall(r"[\w./:-]+", json.dumps(incident.model_dump(), ensure_ascii=False)))
    for name in sorted(
        set(
            re.findall(
                r"(?:ConfigMap|Secret|pod|namespace|image)\s+[`\"]([\w./:-]+)[`\"]", claims, re.I
            )
        )
    ):
        if name not in tokens:
            flags.append({"code": "unobserved_named_resource", "value": name})
    observations, ambiguous = selected_observations(incident)
    if not ambiguous:
        for field, expression in (
            ("exit_code", r"exitCode\s*[=:]\s*(\d+)"),
            ("restart_count", r"restartCount\s*[=:]\s*(\d+)"),
        ):
            observed = {o.details[field] for o in observations if type(o.details.get(field)) is int}
            for value in sorted(set(map(int, re.findall(expression, claims)))):
                if observed and value not in observed:
                    flags.append({"code": f"contradictory_{field}", "value": value})
    return flags


def _rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def assess(incidents: list[Incident], records: list[PredictionRecord]) -> list[dict]:
    if not incidents:
        raise ValueError("Evaluation requires a nonempty incident dataset")
    inputs = {incident.id: incident for incident in incidents}
    if len(inputs) != len(incidents):
        raise ValueError("Duplicate incident IDs")
    supplied = {}
    for record in records:
        if record.incident_id not in inputs or record.incident_id in supplied:
            raise ValueError(f"Unknown or duplicate prediction incident: {record.incident_id}")
        supplied[record.incident_id] = record
    if len({record.run.model_dump_json() for record in records}) > 1:
        raise ValueError("Evaluate one run/configuration at a time")
    assessed = []
    for incident in incidents:
        original = supplied.get(incident.id)
        record = (
            None
            if original is None
            else parse_response(
                original.raw_response,
                incident.to_prompt_input(),
                original.run,
                original.elapsed_seconds,
            )
        )
        valid = record is not None and not (
            record.parse_errors or record.schema_errors or record.reference_errors
        )
        prediction = record.prediction if record is not None else None
        flags = automatic_flags(incident.to_prompt_input(), prediction) if prediction else []
        assessed.append(
            {
                "incident": incident,
                "record": record,
                "valid": valid,
                "flags": flags,
                "predicted": prediction.category if valid else "invalid",
            }
        )
    return assessed


def evaluate(incidents: list[Incident], records: list[PredictionRecord]) -> dict:
    rows = assess(incidents, records)
    n = len(rows)
    correct = sum(row["predicted"] == row["incident"].category for row in rows)
    confusion = {label: {column: 0 for column in LABELS + ["invalid"]} for label in LABELS}
    for row in rows:
        confusion[row["incident"].category][row["predicted"]] += 1
    per_class = {}
    for label in CLASSES:
        tp = confusion[label][label]
        support = sum(confusion[label].values())
        predicted = sum(confusion[truth][label] for truth in LABELS)
        per_class[label] = {
            "support": support,
            "precision": _rate(tp, predicted) or 0.0,
            "recall": _rate(tp, support) or 0.0,
            "f1": _rate(2 * tp, support + predicted) or 0.0,
        }
    answerable = [row for row in rows if row["incident"].category != "insufficient_evidence"]
    ambiguous = [row for row in rows if row["incident"].category == "insufficient_evidence"]
    abstentions = sum(row["predicted"] == "insufficient_evidence" for row in rows)
    parse_ok = sum(row["record"] is not None and not row["record"].parse_errors for row in rows)
    schema_ok = sum(
        row["record"] is not None
        and not (row["record"].parse_errors or row["record"].schema_errors)
        for row in rows
    )
    groups = {}
    for group in ("missing_diagnostics", "target_ambiguity"):
        members = [row for row in ambiguous if group in row["incident"].variant_tags]
        count = sum(row["predicted"] == "insufficient_evidence" for row in members)
        groups[group] = {
            "support": len(members),
            "correct_abstentions": count,
            "correct_abstention_rate": _rate(count, len(members)),
        }
    return {
        "n": n,
        "scenarios": len({i.scenario_id for i in incidents}),
        "responses": len(records),
        "missing_outputs": n - len(records),
        "correct": correct,
        "accuracy": correct / n,
        "answerable_support": len(answerable),
        "answerable_accuracy": _rate(
            sum(r["predicted"] == r["incident"].category for r in answerable), len(answerable)
        ),
        "macro_f1_six_classes": sum(info["f1"] for info in per_class.values()) / 6,
        "per_class": per_class,
        "confusion_matrix": confusion,
        "json_parse_success_rate": parse_ok / n,
        "strict_schema_success_rate": schema_ok / n,
        "valid_outputs": sum(row["valid"] for row in rows),
        "valid_output_rate": sum(row["valid"] for row in rows) / n,
        "reference_success_rate": sum(row["valid"] for row in rows) / n,
        "abstentions": abstentions,
        "abstention_rate": abstentions / n,
        "answerable_abstentions": sum(
            r["predicted"] == "insufficient_evidence" for r in answerable
        ),
        "ambiguous_support": len(ambiguous),
        "correct_abstention_rate": _rate(
            sum(r["predicted"] == "insufficient_evidence" for r in ambiguous), len(ambiguous)
        ),
        "abstention_groups": groups,
        "automatic_flagged_predictions": sum(bool(row["flags"]) for row in rows),
        "automatic_flags_by_code": dict(
            Counter(flag["code"] for row in rows for flag in row["flags"])
        ),
        "reviewed_hallucination_rate": None,
        "metric_policy": (
            "Invalid or missing outputs are incorrect. Reference failures invalidate "
            "classification even if JSON/schema pass. Macro-F1 averages six classes, "
            "including zero-support classes as zero; abstentions on answerable cases are "
            "false negatives and class predictions on abstention cases are false "
            "positives. Automatic flags are incomplete review aids, not reviewed "
            "hallucination measurements. Variants are not independent scenarios."
        ),
    }


def prepare_review(
    incidents: list[Incident], records: list[PredictionRecord], seed: int = 42
) -> list[dict]:
    """Predeclared: two per answerable class, invalid/abstained first; one per ambiguity type."""
    rows = assess(incidents, records)

    def key(row):
        return hashlib.sha256(f"{seed}:{row['incident'].id}".encode()).hexdigest()

    selected = []
    for label in CLASSES:
        pool = sorted((r for r in rows if r["incident"].category == label), key=key)
        chosen = []
        for predicate in (
            lambda r: not r["valid"],
            lambda r: r["predicted"] == "insufficient_evidence",
        ):
            eligible = [r for r in pool if predicate(r) and r not in chosen]
            if eligible:
                chosen.append(eligible[0])
        chosen.extend(r for r in pool if r not in chosen)
        selected.extend(chosen[:2])
    for group in ("missing_diagnostics", "target_ambiguity"):
        pool = sorted((r for r in rows if group in r["incident"].variant_tags), key=key)
        selected.extend(pool[:1])
    return [
        {
            "incident_id": row["incident"].id,
            "gold_category": row["incident"].category,
            "observations": [o.model_dump() for o in row["incident"].observations],
            "raw_response": row["record"].raw_response if row["record"] else None,
            "prediction": row["record"].prediction.model_dump()
            if row["record"] and row["record"].prediction
            else None,
            "parse_errors": row["record"].parse_errors if row["record"] else ["Missing output"],
            "schema_errors": row["record"].schema_errors if row["record"] else [],
            "reference_errors": row["record"].reference_errors if row["record"] else [],
            "automatic_flags": row["flags"],
            "valid": row["valid"],
            "support_rating": None,
            "unsupported_factual_claim": None,
            "recommendations_relevant": None,
            "recommendations_safe": None,
            "reviewer": None,
            "notes": None,
        }
        for row in selected
    ]
