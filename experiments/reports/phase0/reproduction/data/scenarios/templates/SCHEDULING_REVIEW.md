# Schedule template review

Reviewer: **Codex**, **2026-11-12**. All six records are **reviewed and accepted for future generation** under project-owner authorization to accept passing reviews without further approval. This is agent review, not independent human verification or live-cluster replay.

All observations are fictional snapshot facts. Supplied inventories, release records, and diagnostic traces are explicitly identified; LogMind did not collect them or execute any cluster/database commands for these fixtures. Credentials, raw production logs, and gold annotations are absent from prompt-visible observations. All checks are read-only.

Repeatable checks: `uv run --locked pytest tests/test_templates.py`. Each file is also accepted by `make validate INCIDENTS=data/scenarios/templates/<scenario>.jsonl`. The template suite checks schemas/excerpts, complete 42-scenario coverage, unique IDs, catalogue assignments, two scenarios per class per split, and the group-specific causal consistency checks. Tests complement the assessments below; they do not establish production reliability.

## schedule-01: CPU request exceeds both node headrooms

File: [schedule-01.jsonl](schedule-01.jsonl). Split: **train**. Category: **scheduling_failure**.

Gold root cause: The pod cannot be scheduled because its 500m CPU request exceeds the available requested-capacity headroom on both nodes.

Causal assessment: The effective CPU request is 500m. Nodes each have 2000m allocatable and 1600m/1700m already requested, leaving only 400m/300m. FailedScheduling reports insufficient CPU on both.

Claim boundaries: Use requested capacity, not instantaneous CPU utilization. Both nodes are included; no scaling action is executed.

Gold evidence IDs: `event-1`, `metadata-1`, `metadata-2`. Exact excerpts are stored with the record and validated against the observation text.

Read-only expected checks:

- Inspect the supplied pod requests and hard placement constraints against the complete node snapshot.

- Inspect the FailedScheduling event and relevant allocation/placement metadata without changing requests, labels, tolerations, or existing workloads.


Review checklist:

- [x] Validate schema, gold references, catalogue split, and group-specific evidence consistency.

  <!-- Completed 2026-11-12, Codex: schedule-01 passed authored-template checks, including its evidence/reference and split assertions. -->

- [x] Confirm the diagnosis or information gap follows from the supplied observations without hidden assumptions.

  <!-- Completed 2026-11-12, Codex: schedule-01 causal assessment and unsupported claims are recorded above. -->

- [x] Inspect read-only checks and prompt-visible facts for safety, diagnostic scope, and gold-annotation leakage.

  <!-- Completed 2026-11-12, Codex: expected checks inspect supplied/current information without executing repairs; gold fields and tags remain outside PromptInput. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex, accepted under project-owner authorization for passing agent reviews. -->

## schedule-02: Memory request exceeds both node headrooms

File: [schedule-02.jsonl](schedule-02.jsonl). Split: **train**. Category: **scheduling_failure**.

Gold root cause: The pod cannot be scheduled because its 512 MiB memory request exceeds the available requested-capacity headroom on both nodes.

Causal assessment: The effective request is 512 MiB. Nodes each have 2048 MiB allocatable and 1792/1920 MiB already requested, leaving 256/128 MiB. FailedScheduling reports insufficient memory.

Claim boundaries: This is scheduling against requests, not a running-container OOM or a node memory-pressure diagnosis.

Gold evidence IDs: `event-1`, `metadata-1`, `metadata-2`. Exact excerpts are stored with the record and validated against the observation text.

Read-only expected checks:

- Inspect the supplied pod requests and hard placement constraints against the complete node snapshot.

- Inspect the FailedScheduling event and relevant allocation/placement metadata without changing requests, labels, tolerations, or existing workloads.


Review checklist:

- [x] Validate schema, gold references, catalogue split, and group-specific evidence consistency.

  <!-- Completed 2026-11-12, Codex: schedule-02 passed authored-template checks, including its evidence/reference and split assertions. -->

- [x] Confirm the diagnosis or information gap follows from the supplied observations without hidden assumptions.

  <!-- Completed 2026-11-12, Codex: schedule-02 causal assessment and unsupported claims are recorded above. -->

- [x] Inspect read-only checks and prompt-visible facts for safety, diagnostic scope, and gold-annotation leakage.

  <!-- Completed 2026-11-12, Codex: expected checks inspect supplied/current information without executing repairs; gold fields and tags remain outside PromptInput. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex, accepted under project-owner authorization for passing agent reviews. -->

## schedule-03: Node selector has no matching node

File: [schedule-03.jsonl](schedule-03.jsonl). Split: **validation**. Category: **scheduling_failure**.

Gold root cause: The pod nodeSelector requires disk=nvme, but neither node has that label value.

Causal assessment: The pod requires disk=nvme; the complete two-node inventory instead supplies disk=ssd and disk=hdd. The scheduler reports selector mismatch.

Claim boundaries: Do not assume an unlisted matching node or confuse a required selector with a soft preference.

Gold evidence IDs: `event-1`, `metadata-1`, `metadata-2`. Exact excerpts are stored with the record and validated against the observation text.

Read-only expected checks:

- Inspect the supplied pod requests and hard placement constraints against the complete node snapshot.

- Inspect the FailedScheduling event and relevant allocation/placement metadata without changing requests, labels, tolerations, or existing workloads.


Review checklist:

- [x] Validate schema, gold references, catalogue split, and group-specific evidence consistency.

  <!-- Completed 2026-11-12, Codex: schedule-03 passed authored-template checks, including its evidence/reference and split assertions. -->

- [x] Confirm the diagnosis or information gap follows from the supplied observations without hidden assumptions.

  <!-- Completed 2026-11-12, Codex: schedule-03 causal assessment and unsupported claims are recorded above. -->

- [x] Inspect read-only checks and prompt-visible facts for safety, diagnostic scope, and gold-annotation leakage.

  <!-- Completed 2026-11-12, Codex: expected checks inspect supplied/current information without executing repairs; gold fields and tags remain outside PromptInput. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex, accepted under project-owner authorization for passing agent reviews. -->

## schedule-04: Untolerated NoSchedule taint

File: [schedule-04.jsonl](schedule-04.jsonl). Split: **validation**. Category: **scheduling_failure**.

Gold root cause: Both otherwise eligible nodes have a dedicated=batch:NoSchedule taint that the pod does not tolerate.

Causal assessment: Both otherwise eligible nodes carry dedicated=batch:NoSchedule. The pod has no matching toleration; the scheduler names that untolerated taint.

Claim boundaries: NoSchedule blocks placement; an eviction or a running-container failure is not claimed.

Gold evidence IDs: `event-1`, `metadata-1`, `metadata-2`. Exact excerpts are stored with the record and validated against the observation text.

Read-only expected checks:

- Inspect the supplied pod requests and hard placement constraints against the complete node snapshot.

- Inspect the FailedScheduling event and relevant allocation/placement metadata without changing requests, labels, tolerations, or existing workloads.


Review checklist:

- [x] Validate schema, gold references, catalogue split, and group-specific evidence consistency.

  <!-- Completed 2026-11-12, Codex: schedule-04 passed authored-template checks, including its evidence/reference and split assertions. -->

- [x] Confirm the diagnosis or information gap follows from the supplied observations without hidden assumptions.

  <!-- Completed 2026-11-12, Codex: schedule-04 causal assessment and unsupported claims are recorded above. -->

- [x] Inspect read-only checks and prompt-visible facts for safety, diagnostic scope, and gold-annotation leakage.

  <!-- Completed 2026-11-12, Codex: expected checks inspect supplied/current information without executing repairs; gold fields and tags remain outside PromptInput. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex, accepted under project-owner authorization for passing agent reviews. -->

## schedule-05: Required anti-affinity excludes both hostnames

File: [schedule-05.jsonl](schedule-05.jsonl). Split: **test**. Category: **scheduling_failure**.

Gold root cause: Required pod anti-affinity excludes both nodes because each hostname domain already contains a matching pod.

Causal assessment: The hard anti-affinity rule selects app=search in demo-app with hostname topology. Each node already hosts a matching pod in that domain; the scheduler reports anti-affinity failure.

Claim boundaries: The rule is required, not preferred; namespace and topology are supplied, not guessed.

Gold evidence IDs: `event-1`, `metadata-1`, `metadata-2`. Exact excerpts are stored with the record and validated against the observation text.

Read-only expected checks:

- Inspect the supplied pod requests and hard placement constraints against the complete node snapshot.

- Inspect the FailedScheduling event and relevant allocation/placement metadata without changing requests, labels, tolerations, or existing workloads.


Review checklist:

- [x] Validate schema, gold references, catalogue split, and group-specific evidence consistency.

  <!-- Completed 2026-11-12, Codex: schedule-05 passed authored-template checks, including its evidence/reference and split assertions. -->

- [x] Confirm the diagnosis or information gap follows from the supplied observations without hidden assumptions.

  <!-- Completed 2026-11-12, Codex: schedule-05 causal assessment and unsupported claims are recorded above. -->

- [x] Inspect read-only checks and prompt-visible facts for safety, diagnostic scope, and gold-annotation leakage.

  <!-- Completed 2026-11-12, Codex: expected checks inspect supplied/current information without executing repairs; gold fields and tags remain outside PromptInput. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex, accepted under project-owner authorization for passing agent reviews. -->

## schedule-06: Requested GPU unavailable

File: [schedule-06.jsonl](schedule-06.jsonl). Split: **test**. Category: **scheduling_failure**.

Gold root cause: The pod requests one nvidia.com/gpu resource, but neither eligible node advertises any allocatable GPU resource.

Causal assessment: The pod requests one nvidia.com/gpu. Both eligible nodes report zero allocatable GPUs and the scheduler reports insufficient nvidia.com/gpu.

Claim boundaries: Do not infer a broken GPU driver or absent physical hardware from advertised allocatable resources alone.

Gold evidence IDs: `event-1`, `metadata-1`, `metadata-2`. Exact excerpts are stored with the record and validated against the observation text.

Read-only expected checks:

- Inspect the supplied pod requests and hard placement constraints against the complete node snapshot.

- Inspect the FailedScheduling event and relevant allocation/placement metadata without changing requests, labels, tolerations, or existing workloads.


Review checklist:

- [x] Validate schema, gold references, catalogue split, and group-specific evidence consistency.

  <!-- Completed 2026-11-12, Codex: schedule-06 passed authored-template checks, including its evidence/reference and split assertions. -->

- [x] Confirm the diagnosis or information gap follows from the supplied observations without hidden assumptions.

  <!-- Completed 2026-11-12, Codex: schedule-06 causal assessment and unsupported claims are recorded above. -->

- [x] Inspect read-only checks and prompt-visible facts for safety, diagnostic scope, and gold-annotation leakage.

  <!-- Completed 2026-11-12, Codex: expected checks inspect supplied/current information without executing repairs; gold fields and tags remain outside PromptInput. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex, accepted under project-owner authorization for passing agent reviews. -->

## Technical references

- [Official Kubernetes reference 1](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/)

- [Official Kubernetes reference 2](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/)

- [Official Kubernetes reference 3](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)
