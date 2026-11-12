"""Strict data contracts; only PromptInput may be passed to a prompt builder."""

from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

Text = Annotated[str, Field(min_length=1, pattern=r"\S")]
Category = Literal[
    "container_crash",
    "oom_killed",
    "image_pull_failure",
    "probe_failure",
    "missing_config",
    "scheduling_failure",
    "insufficient_evidence",
]


class StrictModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


class Observation(StrictModel):
    id: Text
    kind: Literal["status", "termination", "event", "log", "metadata"]
    text: Text
    details: dict[str, JsonValue] = Field(default_factory=dict)


class Evidence(StrictModel):
    observation_id: Text
    excerpt: Text


class PromptInput(StrictModel):
    incident_id: Text
    observations: Annotated[list[Observation], Field(min_length=1)]

    @model_validator(mode="after")
    def unique_observations(self) -> Self:
        ids = [observation.id for observation in self.observations]
        if len(ids) != len(set(ids)):
            raise ValueError("Observation IDs must be unique within an incident")
        return self


class Incident(StrictModel):
    id: Text
    scenario_id: Text
    split: Literal["train", "validation", "test"]
    source: Literal["synthetic", "controlled_cluster"]
    category: Category
    root_cause: Text
    observations: Annotated[list[Observation], Field(min_length=1)]
    evidence: list[Evidence]
    expected_actions: list[Text]
    variant_tags: list[Text]

    def to_prompt_input(self) -> PromptInput:
        """Explicit allowlist: labels, scenario IDs, and gold evidence stay private."""
        return PromptInput(incident_id=self.id, observations=self.observations)

    @model_validator(mode="after")
    def valid_evidence(self) -> Self:
        self.to_prompt_input()  # Also checks observation-ID uniqueness.
        observations = {item.id: item for item in self.observations}
        for item in self.evidence:
            if item.observation_id not in observations:
                raise ValueError(f"Unknown gold evidence ID: {item.observation_id}")
            if item.excerpt not in observations[item.observation_id].text:
                raise ValueError(f"Gold excerpt absent from observation: {item.observation_id}")
        return self


class Prediction(StrictModel):
    incident_id: Text
    category: Category
    root_cause: Text
    evidence_ids: list[Text]
    explanation: Text
    recommended_checks: list[Text]
    uncertain: bool

    def validate_against(self, incident: PromptInput) -> None:
        """Check references separately from JSON/schema validity."""
        if self.incident_id != incident.incident_id:
            raise ValueError("Prediction incident_id does not match input")
        known_ids = {item.id for item in incident.observations}
        unknown_ids = set(self.evidence_ids) - known_ids
        if unknown_ids:
            raise ValueError(f"Unknown predicted evidence IDs: {sorted(unknown_ids)}")


class RunManifest(StrictModel):
    run_id: Text
    backend_id: Text
    revision: Text  # Immutable model commit or rules implementation revision.
    tokenizer_revision: Text | None
    prompt_version: Text
    decoding_settings: dict[str, JsonValue]
    seed: int
    dataset_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    environment: dict[str, JsonValue]


class PredictionRecord(StrictModel):
    """Envelope preserves failed outputs without manufacturing a valid prediction."""

    incident_id: Text
    run: RunManifest
    raw_response: str
    prediction: Prediction | None
    parse_errors: list[Text]
    schema_errors: list[Text]
    reference_errors: list[Text]
    elapsed_seconds: Annotated[float, Field(ge=0, allow_inf_nan=False)]

    @model_validator(mode="after")
    def consistent_result(self) -> Self:
        if self.prediction is None:
            if not (self.parse_errors or self.schema_errors):
                raise ValueError("Missing prediction must retain parse or schema errors")
        else:
            if self.parse_errors or self.schema_errors:
                raise ValueError("Parsed prediction cannot have parse or schema errors")
            if self.prediction.incident_id != self.incident_id:
                raise ValueError("Envelope and prediction incident IDs differ")
        return self
