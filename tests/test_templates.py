"""Audit authored data for leakage, split drift, and causal-evidence consistency."""

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

import pytest

from logmind.jsonl import read_incidents

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = sorted((ROOT / "data/scenarios/templates").glob("*.jsonl"))


def load(path):
    records = read_incidents(path)
    assert len(records) == 1
    return records[0]


@pytest.mark.parametrize("path", TEMPLATES, ids=lambda path: path.stem)
def test_template_matches_catalogue_and_hides_annotations(path):
    record = load(path)
    assert record.scenario_id == path.stem
    catalogue = (ROOT / "data/scenarios/README.md").read_text()
    assert f"| {record.scenario_id} | {record.split} | {record.category} |" in catalogue
    prompt = record.to_prompt_input().model_dump()
    assert set(prompt) == {"incident_id", "observations"}
    assert record.scenario_id not in json.dumps(prompt)
    assert record.category not in json.dumps(prompt)  # Raw OOMKilled is permitted.
    assert record.source == "synthetic"
    assert record.evidence
    assert record.expected_actions


def test_template_ids_are_unique_across_files():
    assert TEMPLATES, "Expected authored baseline templates"
    records = [load(path) for path in TEMPLATES]
    assert len({record.id for record in records}) == len(records)
    assert len({record.scenario_id for record in records}) == len(records)


@pytest.mark.parametrize(
    "path",
    [path for path in TEMPLATES if path.stem.startswith(("crash-", "oom-"))],
    ids=lambda path: path.stem,
)
def test_crash_and_oom_diagnostics_match_selected_attempt(path):
    record = load(path)
    if record.category not in {"container_crash", "oom_killed"}:
        pytest.skip("This invariant applies to process termination templates")
    observations = {item.id: item for item in record.observations}
    target = observations["metadata-1"].details
    term = observations["termination-1"].details
    identity = ("namespace", "pod", "container", "attempt")
    assert all(term[field] == target[field] for field in identity)
    start = datetime.fromisoformat(term["started_at"])
    end = datetime.fromisoformat(term["finished_at"])
    assert start < end <= datetime.fromisoformat(term["captured_at"])
    for observation in record.observations:
        if observation.kind != "log":
            continue
        details = observation.details
        assert all(details[field] == target[field] for field in identity)
        assert start <= datetime.fromisoformat(details["timestamp"]) <= end
        assert details["source"]


@pytest.mark.parametrize("scenario", ["oom-02", "oom-04", "oom-06"])
def test_enriched_oom_claims_have_correlated_limit_and_growth_evidence(scenario):
    record = load(ROOT / f"data/scenarios/templates/{scenario}.jsonl")
    observations = {item.id: item for item in record.observations}
    limit = observations["metadata-1"].details["memory_limit_bytes"]
    before = observations["log-1"].details
    after = observations["log-2"].details
    cgroup = observations["log-3"].details
    assert before["cgroup_id"] == after["cgroup_id"] == cgroup["cgroup_id"]
    assert cgroup["source"] == "supplied_cgroup_monitor"
    assert cgroup["memory_max_bytes"] == cgroup["memory_peak_bytes"] == limit
    assert cgroup["oom_after"] > cgroup["oom_before"]
    assert cgroup["oom_kill_after"] > cgroup["oom_kill_before"]
    assert observations["termination-1"].details["reason"] == "OOMKilled"
    gold_ids = {item.observation_id for item in record.evidence}
    assert {"log-1", "log-2", "log-3", "termination-1"} <= gold_ids
    if scenario == "oom-02":
        assert before["cache_bytes"] < after["cache_bytes"]
        assert after["cache_bytes"] + after["other_resident_bytes"] < limit
        assert (
            after["cache_bytes"] + after["other_resident_bytes"] + after["requested_growth_bytes"]
            > limit
        )
    elif scenario == "oom-04":
        assert observations["metadata-2"].details["medium"] == "Memory"
        assert before["used_bytes"] < after["used_bytes"] == after["shmem_bytes"]
        assert after["shmem_bytes"] + after["anon_bytes"] < limit
        assert after["shmem_bytes"] + after["anon_bytes"] + after["requested_write_bytes"] > limit
    else:
        assert observations["metadata-2"].details["heap_max_bytes"] > limit
        assert before["heap_used_bytes"] < after["heap_used_bytes"]
        assert after["heap_used_bytes"] + after["nonheap_resident_bytes"] < limit
        assert (
            after["heap_used_bytes"]
            + after["nonheap_resident_bytes"]
            + after["requested_allocation_bytes"]
            > limit
        )


def test_recovered_service_does_not_assign_previous_oom_to_current_attempt():
    record = load(ROOT / "data/scenarios/templates/oom-03.jsonl")
    observations = {item.id: item for item in record.observations}
    target = observations["metadata-1"].details
    current = observations["status-1"].details
    previous = observations["termination-1"].details
    assert previous["status_field"] == "lastState.terminated"
    assert previous["attempt"] == target["attempt"] < current["attempt"]
    assert current["current_ready"] is True
    assert datetime.fromisoformat(previous["finished_at"]) < datetime.fromisoformat(
        current["started_at"]
    )


def test_init_oom_does_not_attribute_kill_to_main_container():
    record = load(ROOT / "data/scenarios/templates/oom-05.jsonl")
    observations = {item.id: item for item in record.observations}
    target = observations["metadata-1"].details
    status = observations["status-1"].details
    assert target["target_role"] == "init"
    assert observations["termination-1"].details["status_field"].startswith("initContainerStatuses")
    assert status["application_container"] != target["container"]
    assert status["application_started"] is False
    assert status["application_waiting_reason"] == "PodInitializing"


@pytest.mark.parametrize(
    ("number", "signal"),
    [
        (1, "manifest unknown: manifest tagged release-unknown is not found"),
        (2, "401 Unauthorized: UNAUTHORIZED: authentication required"),
        (3, "lookup registry.example.invalid on 192.0.2.53:53: no such host"),
        (4, "x509: certificate signed by unknown authority"),
        (5, "no match for platform linux/arm64 in manifest"),
        (6, "429 Too Many Requests: TOOMANYREQUESTS: pull rate limit exceeded"),
    ],
)
def test_image_failure_has_current_pull_evidence_without_process_exit(number, signal):
    record = load(ROOT / f"data/scenarios/templates/image-{number:02d}.jsonl")
    observations = {item.id: item for item in record.observations}
    target = observations["metadata-1"].details
    status = observations["status-1"].details
    assert status["phase"] == "Pending"
    assert status["pod_scheduled"] is True
    assert status["waiting_reason"] == "ImagePullBackOff"
    assert status["container_started"] is False
    assert status["restart_count"] == 0
    assert all(item.kind not in {"termination", "log"} for item in record.observations)
    identity = ("namespace", "pod", "container", "node_name", "image", "pull_attempt")
    previous_time = None
    for event_id, reason in [("event-1", "Pulling"), ("event-2", "Failed"), ("event-3", "BackOff")]:
        event = observations[event_id]
        assert all(event.details[field] == target[field] for field in identity)
        assert target["image"] in event.text
        assert event.details["source"] == "kubernetes_event"
        assert event.details["reason"] == reason
        timestamp = datetime.fromisoformat(event.details["timestamp"])
        if previous_time is not None:
            assert previous_time < timestamp
        previous_time = timestamp
    assert previous_time <= datetime.fromisoformat(status["captured_at"])
    assert signal in observations["event-2"].text
    assert any(item.observation_id == "event-2" for item in record.evidence)
    assert all(status[field] == target[field] for field in identity)


def test_image_platform_mismatch_has_node_and_index_evidence():
    record = load(ROOT / "data/scenarios/templates/image-05.jsonl")
    observations = {item.id: item for item in record.observations}
    node = observations["metadata-2"].details
    index = observations["metadata-3"].details
    expected_platform = {"os": node["operating_system"], "architecture": node["architecture"]}
    assert index["available_platforms"]
    assert expected_platform not in index["available_platforms"]
    assert index["image"] == observations["metadata-1"].details["image"]
    assert {"metadata-2", "metadata-3"} <= {item.observation_id for item in record.evidence}


def test_private_registry_example_contains_references_without_credentials():
    record = load(ROOT / "data/scenarios/templates/image-02.jsonl")
    inventory = next(item for item in record.observations if item.id == "metadata-2")
    assert inventory.details["private_repository"] is True
    assert inventory.details["credential_object_present"] is True
    assert inventory.details["image_pull_secrets"] == ["demo-registry-access"]
    assert "kubernetes.io/dockerconfigjson" == inventory.details["credential_object_type"]
    # References may enter the snapshot; auth payloads and secret data may not.
    for item in record.observations:
        assert not {"password", "token", "auth", "data", "stringData"} & item.details.keys()


def test_complete_catalogue_has_42_baselines_and_balanced_splits():
    prefixes = {"crash", "oom", "image", "probe", "config", "schedule", "unknown"}
    expected = {f"{prefix}-{number:02d}" for prefix in prefixes for number in range(1, 7)}
    assert {path.stem for path in TEMPLATES} == expected
    records = [load(path) for path in TEMPLATES]
    assert Counter(record.split for record in records) == {
        "train": 14,
        "validation": 14,
        "test": 14,
    }
    support = Counter((record.category, record.split) for record in records)
    assert len(support) == 21
    assert set(support.values()) == {2}


@pytest.mark.parametrize("number", range(1, 7))
def test_probe_failures_distinguish_readiness_from_restart(number):
    record = load(ROOT / f"data/scenarios/templates/probe-{number:02d}.jsonl")
    observations = {item.id: item for item in record.observations}
    metadata = observations["metadata-1"].details
    config = metadata["probe_config"]
    events = [item for item in record.observations if item.details.get("reason") == "Unhealthy"]
    assert len(events) == config["failure_threshold"]
    assert all(event.details["probe_type"] == metadata["probe_type"] for event in events)
    target = {field: metadata[field] for field in ("namespace", "pod", "container", "attempt")}
    for event in events:
        assert all(event.details[field] == value for field, value in target.items())
    times = [datetime.fromisoformat(event.details["timestamp"]) for event in events]
    assert times == sorted(times)
    if metadata["probe_type"] == "readiness":
        assert "event-kill" not in observations
        assert "termination-1" not in observations
        status = observations["status-1"].details
        assert status["phase"] == "Running" and status["restart_count"] == 0
        assert status["ready"] is False
    else:
        kill = observations["event-kill"].details
        term = observations["termination-1"].details
        assert kill["reason"] == "Killing"
        assert times[-1] < datetime.fromisoformat(kill["timestamp"])
        assert datetime.fromisoformat(kill["timestamp"]) < datetime.fromisoformat(
            term["finished_at"]
        )
        assert all(term[field] == value for field, value in target.items())
    gold_ids = {item.observation_id for item in record.evidence}
    assert "metadata-1" in gold_ids
    assert any(event.id in gold_ids for event in events)


def test_probe_configuration_mismatches_have_independent_endpoint_evidence():
    for scenario in ("probe-01", "probe-02", "probe-04", "probe-05"):
        observations = {
            item.id: item
            for item in load(ROOT / f"data/scenarios/templates/{scenario}.jsonl").observations
        }
        config = observations["metadata-1"].details["probe_config"]
        inventory = observations["metadata-2"].details
        if scenario == "probe-01":
            assert config["path"] == inventory["missing_path"]
            assert config["path"] not in inventory["served_paths"]
        elif scenario == "probe-02":
            assert config["port"] == inventory["absent_port"]
            assert config["port"] not in inventory["listening_ports"]
        elif scenario == "probe-04":
            assert config["command"] == [inventory["path"]] and inventory["exists"] is False
        else:
            assert config["port"] == inventory["port"]
            assert config["scheme"] == "HTTPS" and inventory["scheme"] == "HTTP"


def test_startup_and_liveness_timing_claims_are_supported():
    startup = load(ROOT / "data/scenarios/templates/probe-03.jsonl")
    observations = {item.id: item for item in startup.observations}
    assert observations["log-1"].details["initialization_complete"] is False
    milestone = datetime.fromisoformat(observations["log-1"].details["timestamp"])
    last_failure = datetime.fromisoformat(observations["event-3"].details["timestamp"])
    assert milestone < last_failure
    timeout = load(ROOT / "data/scenarios/templates/probe-06.jsonl")
    observations = {item.id: item for item in timeout.observations}
    limit = observations["metadata-1"].details["probe_config"]["timeout_seconds"]
    assert all(duration > limit for duration in observations["log-1"].details["durations_seconds"])


@pytest.mark.parametrize("number", range(1, 7))
def test_missing_config_is_required_and_prevents_process_start(number):
    record = load(ROOT / f"data/scenarios/templates/config-{number:02d}.jsonl")
    observations = {item.id: item for item in record.observations}
    reference = observations["metadata-1"].details
    inventory = observations["metadata-2"].details
    assert reference["optional"] is False
    assert reference["usage"] in {"env", "volume", "projected_volume"}
    assert observations["status-1"].details["container_started"] is False
    assert all(item.kind not in {"log", "termination"} for item in record.observations)
    assert {"metadata-1", "metadata-2", "event-1"} <= {
        item.observation_id for item in record.evidence
    }
    if reference["required_key"] is not None:
        assert inventory["exists"] is True
        assert reference["required_key"] not in inventory["key_names"]
    else:
        assert inventory["exists"] is False
    for item in record.observations:
        assert not {"data", "stringData", "password", "token"} & item.details.keys()


def test_namespace_and_secret_replacement_context_is_supplied():
    namespace_case = load(ROOT / "data/scenarios/templates/config-05.jsonl")
    observations = {item.id: item for item in namespace_case.observations}
    assert observations["metadata-2"].details["other_namespace"] != "demo-app"
    assert observations["metadata-2"].details["exists_in_other_namespace"] is True
    replacement_case = load(ROOT / "data/scenarios/templates/config-06.jsonl")
    observations = {item.id: item for item in replacement_case.observations}
    assert observations["metadata-2"].details["replacement_exists"] is True
    assert (
        observations["metadata-1"].details["resource_name"]
        != observations["metadata-2"].details["replacement_name"]
    )


@pytest.mark.parametrize("number", range(1, 7))
def test_scheduling_claim_excludes_every_node_in_complete_inventory(number):
    record = load(ROOT / f"data/scenarios/templates/schedule-{number:02d}.jsonl")
    observations = {item.id: item for item in record.observations}
    pod = observations["metadata-1"].details
    inventory = observations["metadata-2"].details
    assert inventory["complete_node_inventory"] is True
    nodes = inventory["nodes"]
    assert len(nodes) == 2
    assert observations["event-1"].details["reason"] == "FailedScheduling"
    status = observations["status-1"].details
    assert status["pod_scheduled"] is False and status["node_name"] is None
    assert status["container_started"] is False
    assert {"metadata-1", "metadata-2", "event-1"} <= {
        item.observation_id for item in record.evidence
    }
    for node in nodes:
        if number == 1:
            assert (
                pod["requests"]["cpu_millicores"]
                > node["cpu_allocatable_millicores"] - node["cpu_requested_millicores"]
            )
        elif number == 2:
            assert (
                pod["requests"]["memory_bytes"]
                > node["memory_allocatable_bytes"] - node["memory_requested_bytes"]
            )
        elif number == 3:
            assert any(
                node["labels"].get(key) != value for key, value in pod["node_selector"].items()
            )
        elif number == 4:
            assert pod["tolerations"] == []
            assert any(taint["effect"] == "NoSchedule" for taint in node["taints"])
        elif number == 5:
            rule = pod["required_anti_affinity"]
            assert rule["topology_key"] == "kubernetes.io/hostname"
            assert any(
                existing["namespace"] == rule["namespace"]
                and all(existing["labels"].get(k) == v for k, v in rule["label_selector"].items())
                and existing["node"] == node["name"]
                for existing in node["existing_pods"]
            )
        else:
            assert pod["requests"]["gpu"] > node["gpu_allocatable"] - node["gpu_requested"]


@pytest.mark.parametrize("number", range(1, 7))
def test_insufficient_evidence_retains_the_intended_information_gap(number):
    record = load(ROOT / f"data/scenarios/templates/unknown-{number:02d}.jsonl")
    observations = {item.id: item for item in record.observations}
    assert record.category == "insufficient_evidence"
    tag = "target_ambiguity" if number == 6 else "missing_diagnostics"
    assert tag in record.variant_tags
    assert tag not in json.dumps(record.to_prompt_input().model_dump())
    if number in (1, 2, 4):
        assert len(record.observations) == 1
        assert record.observations[0].kind == "status"
    elif number == 3:
        assert len(record.observations) == 1
        details = observations["termination-1"].details
        assert details["exit_code"] == 137
        assert "reason" not in details and "signal" not in details
    elif number == 5:
        assert observations["metadata-1"].details["attempt"] == 3
        assert observations["termination-1"].details["attempt"] == 1
        assert observations["status-1"].details["attempt"] == 3
        assert all(item.kind != "log" for item in record.observations)
    else:
        assert "container" not in observations["metadata-1"].details
        assert (
            observations["event-1"].details["container"]
            != observations["event-2"].details["container"]
        )
