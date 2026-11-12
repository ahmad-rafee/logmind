# Config template review

Reviewer: **Codex**, **2026-11-12**. All six records are **reviewed and accepted for future generation** under project-owner authorization to accept passing reviews without further approval. This is agent review, not independent human verification or live-cluster replay.

All observations are fictional snapshot facts. Supplied inventories, release records, and diagnostic traces are explicitly identified; LogMind did not collect them or execute any cluster/database commands for these fixtures. Credentials, raw production logs, and gold annotations are absent from prompt-visible observations. All checks are read-only.

Repeatable checks: `uv run --locked pytest tests/test_templates.py`. Each file is also accepted by `make validate INCIDENTS=data/scenarios/templates/<scenario>.jsonl`. The template suite checks schemas/excerpts, complete 42-scenario coverage, unique IDs, catalogue assignments, two scenarios per class per split, and the group-specific causal consistency checks. Tests complement the assessments below; they do not establish production reliability.

## config-01: Missing required ConfigMap volume

File: [config-01.jsonl](config-01.jsonl). Split: **train**. Category: **missing_config**.

Gold root cause: Referenced ConfigMap api-settings is absent from namespace demo-app.

Causal assessment: The non-optional volume reference names api-settings in demo-app, supplied inventory reports it absent, and FailedMount names the same ConfigMap.

Claim boundaries: Missing workload configuration is the diagnosis; no process has started and no malformed-file or registry error is inferred.

Gold evidence IDs: `metadata-2`, `event-1`, `metadata-1`. Exact excerpts are stored with the record and validated against the observation text.

Read-only expected checks:

- Inspect the workload reference name, namespace, optional flag, and any required key names without displaying configuration or credential values.

- Compare the supplied object/key inventory and release metadata with the workload reference without creating resources, editing references, or restarting workloads.


Review checklist:

- [x] Validate schema, gold references, catalogue split, and group-specific evidence consistency.

  <!-- Completed 2026-11-12, Codex: config-01 passed authored-template checks, including its evidence/reference and split assertions. -->

- [x] Confirm the diagnosis or information gap follows from the supplied observations without hidden assumptions.

  <!-- Completed 2026-11-12, Codex: config-01 causal assessment and unsupported claims are recorded above. -->

- [x] Inspect read-only checks and prompt-visible facts for safety, diagnostic scope, and gold-annotation leakage.

  <!-- Completed 2026-11-12, Codex: expected checks inspect supplied/current information without executing repairs; gold fields and tags remain outside PromptInput. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex, accepted under project-owner authorization for passing agent reviews. -->

## config-02: Missing required Secret environment reference

File: [config-02.jsonl](config-02.jsonl). Split: **train**. Category: **missing_config**.

Gold root cause: The required workload Secret service-auth is absent from namespace demo-app.

Causal assessment: A non-optional environment Secret reference names service-auth; inventory and configuration error both report that object absent.

Claim boundaries: This Secret supplies application configuration, not registry credentials. No Secret value is included or requested for display.

Gold evidence IDs: `metadata-2`, `event-1`, `metadata-1`. Exact excerpts are stored with the record and validated against the observation text.

Read-only expected checks:

- Inspect the workload reference name, namespace, optional flag, and any required key names without displaying configuration or credential values.

- Compare the supplied object/key inventory and release metadata with the workload reference without creating resources, editing references, or restarting workloads.


Review checklist:

- [x] Validate schema, gold references, catalogue split, and group-specific evidence consistency.

  <!-- Completed 2026-11-12, Codex: config-02 passed authored-template checks, including its evidence/reference and split assertions. -->

- [x] Confirm the diagnosis or information gap follows from the supplied observations without hidden assumptions.

  <!-- Completed 2026-11-12, Codex: config-02 causal assessment and unsupported claims are recorded above. -->

- [x] Inspect read-only checks and prompt-visible facts for safety, diagnostic scope, and gold-annotation leakage.

  <!-- Completed 2026-11-12, Codex: expected checks inspect supplied/current information without executing repairs; gold fields and tags remain outside PromptInput. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex, accepted under project-owner authorization for passing agent reviews. -->

## config-03: Required ConfigMap key absent

File: [config-03.jsonl](config-03.jsonl). Split: **validation**. Category: **missing_config**.

Gold root cause: The existing ConfigMap batch-settings lacks the required QUEUE_NAME environment key.

Causal assessment: batch-settings exists, but its supplied key-name inventory lists only LOG_LEVEL; the workload requires QUEUE_NAME and the configuration event names that missing key.

Claim boundaries: Do not claim the entire ConfigMap is missing or infer the expected value of QUEUE_NAME.

Gold evidence IDs: `metadata-2`, `event-1`, `metadata-1`. Exact excerpts are stored with the record and validated against the observation text.

Read-only expected checks:

- Inspect the workload reference name, namespace, optional flag, and any required key names without displaying configuration or credential values.

- Compare the supplied object/key inventory and release metadata with the workload reference without creating resources, editing references, or restarting workloads.


Review checklist:

- [x] Validate schema, gold references, catalogue split, and group-specific evidence consistency.

  <!-- Completed 2026-11-12, Codex: config-03 passed authored-template checks, including its evidence/reference and split assertions. -->

- [x] Confirm the diagnosis or information gap follows from the supplied observations without hidden assumptions.

  <!-- Completed 2026-11-12, Codex: config-03 causal assessment and unsupported claims are recorded above. -->

- [x] Inspect read-only checks and prompt-visible facts for safety, diagnostic scope, and gold-annotation leakage.

  <!-- Completed 2026-11-12, Codex: expected checks inspect supplied/current information without executing repairs; gold fields and tags remain outside PromptInput. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex, accepted under project-owner authorization for passing agent reviews. -->

## config-04: Required projected Secret key absent

File: [config-04.jsonl](config-04.jsonl). Split: **validation**. Category: **missing_config**.

Gold root cause: The existing Secret signing-material lacks the required projected key signing.pem.

Causal assessment: signing-material exists with verification.pem only, while the required projection selects signing.pem; the mount event names the missing key.

Claim boundaries: Only key names are supplied. No credential values or assumed key contents are exposed.

Gold evidence IDs: `metadata-2`, `event-1`, `metadata-1`. Exact excerpts are stored with the record and validated against the observation text.

Read-only expected checks:

- Inspect the workload reference name, namespace, optional flag, and any required key names without displaying configuration or credential values.

- Compare the supplied object/key inventory and release metadata with the workload reference without creating resources, editing references, or restarting workloads.


Review checklist:

- [x] Validate schema, gold references, catalogue split, and group-specific evidence consistency.

  <!-- Completed 2026-11-12, Codex: config-04 passed authored-template checks, including its evidence/reference and split assertions. -->

- [x] Confirm the diagnosis or information gap follows from the supplied observations without hidden assumptions.

  <!-- Completed 2026-11-12, Codex: config-04 causal assessment and unsupported claims are recorded above. -->

- [x] Inspect read-only checks and prompt-visible facts for safety, diagnostic scope, and gold-annotation leakage.

  <!-- Completed 2026-11-12, Codex: expected checks inspect supplied/current information without executing repairs; gold fields and tags remain outside PromptInput. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex, accepted under project-owner authorization for passing agent reviews. -->

## config-05: ConfigMap in another namespace

File: [config-05.jsonl](config-05.jsonl). Split: **test**. Category: **missing_config**.

Gold root cause: The workload references renderer-settings in demo-app, but the supplied inventory shows that ConfigMap only in demo-shared.

Causal assessment: The required reference resolves in demo-app; inventory shows renderer-settings absent there and present in demo-shared, consistent with the current FailedMount.

Claim boundaries: The snapshot supports a namespace-local reference mismatch, not a claim that the object is globally absent.

Gold evidence IDs: `metadata-2`, `event-1`, `metadata-1`. Exact excerpts are stored with the record and validated against the observation text.

Read-only expected checks:

- Inspect the workload reference name, namespace, optional flag, and any required key names without displaying configuration or credential values.

- Compare the supplied object/key inventory and release metadata with the workload reference without creating resources, editing references, or restarting workloads.


Review checklist:

- [x] Validate schema, gold references, catalogue split, and group-specific evidence consistency.

  <!-- Completed 2026-11-12, Codex: config-05 passed authored-template checks, including its evidence/reference and split assertions. -->

- [x] Confirm the diagnosis or information gap follows from the supplied observations without hidden assumptions.

  <!-- Completed 2026-11-12, Codex: config-05 causal assessment and unsupported claims are recorded above. -->

- [x] Inspect read-only checks and prompt-visible facts for safety, diagnostic scope, and gold-annotation leakage.

  <!-- Completed 2026-11-12, Codex: expected checks inspect supplied/current information without executing repairs; gold fields and tags remain outside PromptInput. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex, accepted under project-owner authorization for passing agent reviews. -->

## config-06: Stale Secret reference after replacement

File: [config-06.jsonl](config-06.jsonl). Split: **test**. Category: **missing_config**.

Gold root cause: The workload still references absent Secret app-auth-v1 after a supplied release change replaced it with app-auth-v2.

Causal assessment: Supplied release metadata records deletion of app-auth-v1 and creation of app-auth-v2. The workload still names v1, the replacement exists, and the current configuration error reports v1 missing.

Claim boundaries: This is a replacement under a new name, not a Kubernetes in-place rename. The release history is supplied evidence, not a guess based only on object names.

Gold evidence IDs: `metadata-2`, `event-1`, `metadata-1`. Exact excerpts are stored with the record and validated against the observation text.

Read-only expected checks:

- Inspect the workload reference name, namespace, optional flag, and any required key names without displaying configuration or credential values.

- Compare the supplied object/key inventory and release metadata with the workload reference without creating resources, editing references, or restarting workloads.


Review checklist:

- [x] Validate schema, gold references, catalogue split, and group-specific evidence consistency.

  <!-- Completed 2026-11-12, Codex: config-06 passed authored-template checks, including its evidence/reference and split assertions. -->

- [x] Confirm the diagnosis or information gap follows from the supplied observations without hidden assumptions.

  <!-- Completed 2026-11-12, Codex: config-06 causal assessment and unsupported claims are recorded above. -->

- [x] Inspect read-only checks and prompt-visible facts for safety, diagnostic scope, and gold-annotation leakage.

  <!-- Completed 2026-11-12, Codex: expected checks inspect supplied/current information without executing repairs; gold fields and tags remain outside PromptInput. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex, accepted under project-owner authorization for passing agent reviews. -->

## Technical references

- [Official Kubernetes reference 1](https://kubernetes.io/docs/concepts/configuration/configmap/)

- [Official Kubernetes reference 2](https://kubernetes.io/docs/concepts/configuration/secret/)
