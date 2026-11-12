"""Conservative CPU baseline consuming only prompt-visible observations."""

import re

from logmind.schemas import Category, Observation, Prediction, PromptInput

ROOT_CAUSES: dict[Category, str] = {
    "container_crash": (
        "The selected application process exited unsuccessfully with an application "
        "error in the supplied diagnostics."
    ),
    "oom_killed": (
        "The selected container attempt was terminated with reason OOMKilled; a "
        "deeper allocation mechanism is not established by this rule."
    ),
    "image_pull_failure": (
        "The container image could not be pulled, as reported by the supplied pull failure event."
    ),
    "probe_failure": (
        "A configured container health probe failed, as reported by the supplied probe diagnostics."
    ),
    "missing_config": (
        "A required workload configuration object or key is unavailable, as reported "
        "by the configuration event."
    ),
    "scheduling_failure": (
        "The scheduler could not place the pod under the supplied resource or "
        "placement constraints."
    ),
    "insufficient_evidence": (
        "The supplied observations do not establish one unambiguous primary cause for "
        "a selected container attempt."
    ),
}
CHECKS: dict[Category, str] = {
    "container_crash": (
        "Inspect the selected attempt's application error and termination details "
        "without rerunning or repairing the workload."
    ),
    "oom_killed": (
        "Inspect the selected attempt's memory limit and time-aligned memory/cgroup "
        "diagnostics without changing resources."
    ),
    "image_pull_failure": (
        "Inspect the image reference and matching registry/runtime pull diagnostics "
        "without changing credentials or forcing retries."
    ),
    "probe_failure": (
        "Inspect the probe configuration, response events, and matching application "
        "health diagnostics without changing the probe."
    ),
    "missing_config": (
        "Inspect workload configuration references, namespaces, and required keys "
        "without exposing Secret values or editing resources."
    ),
    "scheduling_failure": (
        "Inspect effective requests and hard placement constraints against the node "
        "inventory without modifying workloads or nodes."
    ),
    "insufficient_evidence": (
        "Inspect missing diagnostics and clarify the target container/attempt before "
        "assigning a primary cause."
    ),
}


def selected_observations(incident: PromptInput) -> tuple[list[Observation], bool]:
    """Honor explicit target selection; do not combine distinct container failures."""
    explicit = []
    for observation in incident.observations:
        details = observation.details
        if observation.kind == "metadata" and "target_selection" in str(details.get("source", "")):
            if isinstance(details.get("container"), str):
                attempt = details.get("attempt")
                explicit.append((details["container"], attempt if type(attempt) is int else None))
    if len(set(explicit)) > 1:
        return [], True
    containers = {
        o.details["container"]
        for o in incident.observations
        if isinstance(o.details.get("container"), str)
    }
    if explicit:
        container, attempt = explicit[0]
    elif len(containers) > 1:
        return [], True
    else:
        container, attempt = next(iter(containers), None), None
    selected = []
    for observation in incident.observations:
        details = observation.details
        if container and details.get("container", container) != container:
            continue
        if attempt is not None and details.get("attempt", attempt) != attempt:
            continue
        if str(details.get("source", "")).startswith("historical_") and attempt is None:
            continue
        selected.append(observation)
    return selected, False


def predict(incident: PromptInput) -> Prediction:
    observations, ambiguous_target = selected_observations(incident)
    candidates: dict[Category, list[Observation]] = {}

    def add(category: Category, observation: Observation) -> None:
        candidates.setdefault(category, []).append(observation)

    terms = []
    failures = []
    for observation in observations:
        text = observation.text
        details = observation.details
        if observation.kind == "termination":
            if details.get("reason") == "OOMKilled" or re.search(r"reason[=:]\s*OOMKilled\b", text):
                add("oom_killed", observation)
            if type(details.get("exit_code")) is int and details["exit_code"] != 0:
                terms.append(observation)
        elif observation.kind == "event":
            if details.get("reason") == "FailedScheduling":
                add("scheduling_failure", observation)
            if re.search(r"failed to pull image\b", text, re.I):
                add("image_pull_failure", observation)
            if re.search(r"\b(readiness|liveness|startup) probe (failed|errored)\b", text, re.I):
                add("probe_failure", observation)
            if re.search(r"configmap|secret", text, re.I) and re.search(
                r"not found|couldn't find key|non-existent.*key", text, re.I
            ):
                add("missing_config", observation)
        elif observation.kind == "log" and re.search(
            r"\bFATAL\b|Unhandled \w*Exception|ModuleNotFoundError|SIGSEGV", text
        ):
            failures.append(observation)
    # A probe/OOM termination is a supported cause; nonzero exit alone is not a crash rule.
    if terms and failures and not ({"probe_failure", "oom_killed"} & candidates.keys()):
        candidates["container_crash"] = terms + failures
    if "missing_config" in candidates and any(
        o.details.get("optional") is True for o in observations
    ):
        ambiguous_target = True  # Contradictory required/optional context needs inspection.
    if ambiguous_target or len(candidates) != 1:
        category: Category = "insufficient_evidence"
        evidence = sorted(incident.observations, key=lambda item: item.id)[:3]
    else:
        category = next(iter(candidates))
        evidence = sorted(candidates[category], key=lambda item: item.id)
    evidence = list({item.id: item for item in evidence}.values())
    explanation = "Supplied observations: " + " | ".join(item.text for item in evidence[:3])
    result = Prediction(
        incident_id=incident.incident_id,
        category=category,
        root_cause=ROOT_CAUSES[category],
        evidence_ids=[item.id for item in evidence],
        explanation=explanation,
        recommended_checks=[CHECKS[category]],
        uncertain=category == "insufficient_evidence",
    )
    result.validate_against(incident)
    return result
