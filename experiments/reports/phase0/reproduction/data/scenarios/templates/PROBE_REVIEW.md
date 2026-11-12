# Probe template review

Reviewer: **Codex**, **2026-11-12**. All six records are **reviewed and accepted for future generation** under project-owner authorization to accept passing reviews without further approval. This is agent review, not independent human verification or live-cluster replay.

All observations are fictional snapshot facts. Supplied inventories, release records, and diagnostic traces are explicitly identified; LogMind did not collect them or execute any cluster/database commands for these fixtures. Credentials, raw production logs, and gold annotations are absent from prompt-visible observations. All checks are read-only.

Repeatable checks: `uv run --locked pytest tests/test_templates.py`. Each file is also accepted by `make validate INCIDENTS=data/scenarios/templates/<scenario>.jsonl`. The template suite checks schemas/excerpts, complete 42-scenario coverage, unique IDs, catalogue assignments, two scenarios per class per split, and the group-specific causal consistency checks. Tests complement the assessments below; they do not establish production reliability.

## probe-01: Readiness path absent

File: [probe-01.jsonl](probe-01.jsonl). Split: **train**. Category: **probe_failure**.

Gold root cause: The readiness probe requests /readyz-old, which the running HTTP server does not serve, so the container remains unready.

Causal assessment: The configured /readyz-old path differs from the supplied /readyz endpoint inventory; three readiness responses are 404. Running/unready status and zero restarts agree.

Claim boundaries: No restart or application process crash is attributed to readiness failure.

Gold evidence IDs: `metadata-2`, `event-1`, `event-2`, `event-3`, `metadata-1`, `status-1`. Exact excerpts are stored with the record and validated against the observation text.

Read-only expected checks:

- Inspect the configured readiness path against the supplied endpoint inventory.

- Inspect the readiness response and container status without changing probe settings or restarting the container.


Review checklist:

- [x] Validate schema, gold references, catalogue split, and group-specific evidence consistency.

  <!-- Completed 2026-11-12, Codex: probe-01 passed authored-template checks, including its evidence/reference and split assertions. -->

- [x] Confirm the diagnosis or information gap follows from the supplied observations without hidden assumptions.

  <!-- Completed 2026-11-12, Codex: probe-01 causal assessment and unsupported claims are recorded above. -->

- [x] Inspect read-only checks and prompt-visible facts for safety, diagnostic scope, and gold-annotation leakage.

  <!-- Completed 2026-11-12, Codex: expected checks inspect supplied/current information without executing repairs; gold fields and tags remain outside PromptInput. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex, accepted under project-owner authorization for passing agent reviews. -->

## probe-02: Liveness port mismatch

File: [probe-02.jsonl](probe-02.jsonl). Split: **train**. Category: **probe_failure**.

Gold root cause: The liveness probe targets port 8081 while the application listens on 8080, causing probe failures and a probe-triggered restart.

Causal assessment: The probe targets 8081, while supplied socket inventory lists only 8080. Three connection-refused probe events precede a Killing event and matching exit 143.

Claim boundaries: A refused probe port does not establish a database or network-policy defect; restart attribution uses the explicit Killing event.

Gold evidence IDs: `metadata-2`, `event-1`, `event-2`, `event-3`, `event-kill`, `termination-1`, `metadata-1`. Exact excerpts are stored with the record and validated against the observation text.

Read-only expected checks:

- Inspect the liveness port and supplied listener inventory for the same container.

- Inspect the Unhealthy/Killing events and termination timeline without changing ports or restarting workloads.


Review checklist:

- [x] Validate schema, gold references, catalogue split, and group-specific evidence consistency.

  <!-- Completed 2026-11-12, Codex: probe-02 passed authored-template checks, including its evidence/reference and split assertions. -->

- [x] Confirm the diagnosis or information gap follows from the supplied observations without hidden assumptions.

  <!-- Completed 2026-11-12, Codex: probe-02 causal assessment and unsupported claims are recorded above. -->

- [x] Inspect read-only checks and prompt-visible facts for safety, diagnostic scope, and gold-annotation leakage.

  <!-- Completed 2026-11-12, Codex: expected checks inspect supplied/current information without executing repairs; gold fields and tags remain outside PromptInput. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex, accepted under project-owner authorization for passing agent reviews. -->

## probe-03: Startup threshold reached during initialization

File: [probe-03.jsonl](probe-03.jsonl). Split: **validation**. Category: **probe_failure**.

Gold root cause: The startup probe reaches its configured failure threshold while the application is still initializing, causing a probe-triggered restart.

Causal assessment: Failures at 09:00:01Z, 06Z, and 11Z match the threshold of three with five-second periods. A 09:00:09Z milestone still shows initialization, followed by probe-triggered restart.

Claim boundaries: The failed attempt never completed startup. No successful-completion duration or counterfactual completion time is invented.

Gold evidence IDs: `log-1`, `event-1`, `event-2`, `event-3`, `event-kill`, `termination-1`, `metadata-1`. Exact excerpts are stored with the record and validated against the observation text.

Read-only expected checks:

- Inspect the startup probe period, threshold, and timestamped initialization milestones.

- Compare available startup progress with probe failure times without assuming a completion time or changing the probe.


Review checklist:

- [x] Validate schema, gold references, catalogue split, and group-specific evidence consistency.

  <!-- Completed 2026-11-12, Codex: probe-03 passed authored-template checks, including its evidence/reference and split assertions. -->

- [x] Confirm the diagnosis or information gap follows from the supplied observations without hidden assumptions.

  <!-- Completed 2026-11-12, Codex: probe-03 causal assessment and unsupported claims are recorded above. -->

- [x] Inspect read-only checks and prompt-visible facts for safety, diagnostic scope, and gold-annotation leakage.

  <!-- Completed 2026-11-12, Codex: expected checks inspect supplied/current information without executing repairs; gold fields and tags remain outside PromptInput. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex, accepted under project-owner authorization for passing agent reviews. -->

## probe-04: Exec readiness binary absent

File: [probe-04.jsonl](probe-04.jsonl). Split: **validation**. Category: **probe_failure**.

Gold root cause: The exec readiness probe cannot run because its configured executable /usr/local/bin/ready-check is absent from the running container.

Causal assessment: The configured exec path matches both the missing-file inventory and the probe executable-not-found error. The application remains running and unready.

Claim boundaries: The readiness executable is not the application entry point; no process crash or container restart is claimed.

Gold evidence IDs: `metadata-2`, `event-1`, `event-2`, `event-3`, `metadata-1`, `status-1`. Exact excerpts are stored with the record and validated against the observation text.

Read-only expected checks:

- Inspect the configured exec readiness command and the supplied image file inventory.

- Inspect readiness events and running-container status without installing executables or modifying the image.


Review checklist:

- [x] Validate schema, gold references, catalogue split, and group-specific evidence consistency.

  <!-- Completed 2026-11-12, Codex: probe-04 passed authored-template checks, including its evidence/reference and split assertions. -->

- [x] Confirm the diagnosis or information gap follows from the supplied observations without hidden assumptions.

  <!-- Completed 2026-11-12, Codex: probe-04 causal assessment and unsupported claims are recorded above. -->

- [x] Inspect read-only checks and prompt-visible facts for safety, diagnostic scope, and gold-annotation leakage.

  <!-- Completed 2026-11-12, Codex: expected checks inspect supplied/current information without executing repairs; gold fields and tags remain outside PromptInput. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex, accepted under project-owner authorization for passing agent reviews. -->

## probe-05: Readiness protocol mismatch

File: [probe-05.jsonl](probe-05.jsonl). Split: **test**. Category: **probe_failure**.

Gold root cause: The readiness probe uses HTTPS on port 8080 while that endpoint serves plain HTTP, so the readiness check fails.

Causal assessment: The probe uses HTTPS on port 8080, while supplied endpoint inventory identifies HTTP-only service there; the event reports an HTTP response to an HTTPS client.

Claim boundaries: The diagnosis is protocol mismatch, not certificate expiration or an inferred server-side crash.

Gold evidence IDs: `metadata-2`, `event-1`, `event-2`, `event-3`, `metadata-1`, `status-1`. Exact excerpts are stored with the record and validated against the observation text.

Read-only expected checks:

- Inspect the readiness scheme and the supplied endpoint protocol inventory.

- Inspect the probe protocol error without disabling TLS checks or changing server/probe settings.


Review checklist:

- [x] Validate schema, gold references, catalogue split, and group-specific evidence consistency.

  <!-- Completed 2026-11-12, Codex: probe-05 passed authored-template checks, including its evidence/reference and split assertions. -->

- [x] Confirm the diagnosis or information gap follows from the supplied observations without hidden assumptions.

  <!-- Completed 2026-11-12, Codex: probe-05 causal assessment and unsupported claims are recorded above. -->

- [x] Inspect read-only checks and prompt-visible facts for safety, diagnostic scope, and gold-annotation leakage.

  <!-- Completed 2026-11-12, Codex: expected checks inspect supplied/current information without executing repairs; gold fields and tags remain outside PromptInput. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex, accepted under project-owner authorization for passing agent reviews. -->

## probe-06: Liveness timeout shorter than response

File: [probe-06.jsonl](probe-06.jsonl). Split: **test**. Category: **probe_failure**.

Gold root cause: The liveness health handler responds in 2.4 seconds, exceeding the configured one-second timeout; repeated timeouts trigger a container restart.

Causal assessment: Three handler traces take 2.4 seconds versus a one-second timeout. Timeout events at 09:00:02Z, 07Z, and 12Z precede Killing at 13Z and termination at 14Z.

Claim boundaries: Timing establishes the timeout mismatch, not why the handler is slow. The last handler completes at 13.4Z before process termination; no exact performance fix is prescribed.

Gold evidence IDs: `log-1`, `event-1`, `event-2`, `event-3`, `event-kill`, `termination-1`, `metadata-1`. Exact excerpts are stored with the record and validated against the observation text.

Read-only expected checks:

- Inspect the liveness timeout alongside the supplied health-handler timing trace.

- Inspect probe failure and restart events without guessing why the handler is slow or changing timeouts.


Review checklist:

- [x] Validate schema, gold references, catalogue split, and group-specific evidence consistency.

  <!-- Completed 2026-11-12, Codex: probe-06 passed authored-template checks, including its evidence/reference and split assertions. -->

- [x] Confirm the diagnosis or information gap follows from the supplied observations without hidden assumptions.

  <!-- Completed 2026-11-12, Codex: probe-06 causal assessment and unsupported claims are recorded above. -->

- [x] Inspect read-only checks and prompt-visible facts for safety, diagnostic scope, and gold-annotation leakage.

  <!-- Completed 2026-11-12, Codex: expected checks inspect supplied/current information without executing repairs; gold fields and tags remain outside PromptInput. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex, accepted under project-owner authorization for passing agent reviews. -->

## Technical references

- [Official Kubernetes reference 1](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
