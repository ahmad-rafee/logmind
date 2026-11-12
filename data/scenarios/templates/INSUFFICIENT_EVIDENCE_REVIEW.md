# Unknown template review

Reviewer: **Codex**, **2026-11-12**. All six records are **reviewed and accepted for future generation** under project-owner authorization to accept passing reviews without further approval. This is agent review, not independent human verification or live-cluster replay.

All observations are fictional snapshot facts. Supplied inventories, release records, and diagnostic traces are explicitly identified; LogMind did not collect them or execute any cluster/database commands for these fixtures. Credentials, raw production logs, and gold annotations are absent from prompt-visible observations. All checks are read-only.

Repeatable checks: `uv run --locked pytest tests/test_templates.py`. Each file is also accepted by `make validate INCIDENTS=data/scenarios/templates/<scenario>.jsonl`. The template suite checks schemas/excerpts, complete 42-scenario coverage, unique IDs, catalogue assignments, two scenarios per class per split, and the group-specific causal consistency checks. Tests complement the assessments below; they do not establish production reliability.

Unknown-01 through unknown-05 carry the gold-only `missing_diagnostics` tag; unknown-06 carries `target_ambiguity`. These tags stay outside PromptInput. Future evaluation must report the two groups separately; the evaluator is not implemented yet.

## unknown-01: Backoff without diagnostic detail

File: [unknown-01.jsonl](unknown-01.jsonl). Split: **train**. Category: **insufficient_evidence**.

Gold root cause: Restart backoff is visible, but no termination details, events, or logs establish the cause.

Causal assessment: Only CrashLoopBackOff and restart count are supplied. No matching termination reason, events, or logs distinguish OOM, probe termination, or process errors.

Claim boundaries: Do not convert a restart symptom into a particular cause.

Gold evidence IDs: `status-1`. Exact excerpts are stored with the record and validated against the observation text.

Read-only expected checks:

- Inspect the selected attempt termination reason, prior logs, and matching Kubernetes events.


Review checklist:

- [x] Validate schema, gold references, catalogue split, and group-specific evidence consistency.

  <!-- Completed 2026-11-12, Codex: unknown-01 passed authored-template checks, including its evidence/reference and split assertions. -->

- [x] Confirm the diagnosis or information gap follows from the supplied observations without hidden assumptions.

  <!-- Completed 2026-11-12, Codex: unknown-01 causal assessment and unsupported claims are recorded above. -->

- [x] Inspect read-only checks and prompt-visible facts for safety, diagnostic scope, and gold-annotation leakage.

  <!-- Completed 2026-11-12, Codex: expected checks inspect supplied/current information without executing repairs; gold fields and tags remain outside PromptInput. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex, accepted under project-owner authorization for passing agent reviews. -->

## unknown-02: Pending without conditions

File: [unknown-02.jsonl](unknown-02.jsonl). Split: **train**. Category: **insufficient_evidence**.

Gold root cause: Pending pod phase alone does not establish whether scheduling, image retrieval, configuration, or another condition is blocking startup.

Causal assessment: Only Pending is supplied, without scheduling conditions, container states, events, or logs.

Claim boundaries: Pending alone cannot choose scheduling_failure, image_pull_failure, or missing_config.

Gold evidence IDs: `status-1`. Exact excerpts are stored with the record and validated against the observation text.

Read-only expected checks:

- Inspect scheduling conditions and current scheduling, image-pull, and volume/configuration events.


Review checklist:

- [x] Validate schema, gold references, catalogue split, and group-specific evidence consistency.

  <!-- Completed 2026-11-12, Codex: unknown-02 passed authored-template checks, including its evidence/reference and split assertions. -->

- [x] Confirm the diagnosis or information gap follows from the supplied observations without hidden assumptions.

  <!-- Completed 2026-11-12, Codex: unknown-02 causal assessment and unsupported claims are recorded above. -->

- [x] Inspect read-only checks and prompt-visible facts for safety, diagnostic scope, and gold-annotation leakage.

  <!-- Completed 2026-11-12, Codex: expected checks inspect supplied/current information without executing repairs; gold fields and tags remain outside PromptInput. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex, accepted under project-owner authorization for passing agent reviews. -->

## unknown-03: Exit 137 without reason

File: [unknown-03.jsonl](unknown-03.jsonl). Split: **validation**. Category: **insufficient_evidence**.

Gold root cause: Exit code 137 is supplied without a termination reason or memory diagnostics, so an OOM cause cannot be established.

Causal assessment: The record provides exit code 137 but omits the reason, signal details, events, and memory diagnostics.

Claim boundaries: No OOM diagnosis is justified from exit code alone.

Gold evidence IDs: `termination-1`. Exact excerpts are stored with the record and validated against the observation text.

Read-only expected checks:

- Inspect the selected attempt termination reason and any time-aligned memory/cgroup or kill diagnostics.


Review checklist:

- [x] Validate schema, gold references, catalogue split, and group-specific evidence consistency.

  <!-- Completed 2026-11-12, Codex: unknown-03 passed authored-template checks, including its evidence/reference and split assertions. -->

- [x] Confirm the diagnosis or information gap follows from the supplied observations without hidden assumptions.

  <!-- Completed 2026-11-12, Codex: unknown-03 causal assessment and unsupported claims are recorded above. -->

- [x] Inspect read-only checks and prompt-visible facts for safety, diagnostic scope, and gold-annotation leakage.

  <!-- Completed 2026-11-12, Codex: expected checks inspect supplied/current information without executing repairs; gold fields and tags remain outside PromptInput. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex, accepted under project-owner authorization for passing agent reviews. -->

## unknown-04: Unready without probe results

File: [unknown-04.jsonl](unknown-04.jsonl). Split: **validation**. Category: **insufficient_evidence**.

Gold root cause: The container is unready, but no probe results or application diagnostics establish why.

Causal assessment: Only Running and ready=false are supplied; neither probe configuration/results nor application logs identify a failure.

Claim boundaries: An unready container is not sufficient evidence for a probe configuration defect or a process crash.

Gold evidence IDs: `status-1`. Exact excerpts are stored with the record and validated against the observation text.

Read-only expected checks:

- Inspect readiness probe configuration/results and matching application health diagnostics.


Review checklist:

- [x] Validate schema, gold references, catalogue split, and group-specific evidence consistency.

  <!-- Completed 2026-11-12, Codex: unknown-04 passed authored-template checks, including its evidence/reference and split assertions. -->

- [x] Confirm the diagnosis or information gap follows from the supplied observations without hidden assumptions.

  <!-- Completed 2026-11-12, Codex: unknown-04 causal assessment and unsupported claims are recorded above. -->

- [x] Inspect read-only checks and prompt-visible facts for safety, diagnostic scope, and gold-annotation leakage.

  <!-- Completed 2026-11-12, Codex: expected checks inspect supplied/current information without executing repairs; gold fields and tags remain outside PromptInput. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex, accepted under project-owner authorization for passing agent reviews. -->

## unknown-05: Historical OOM is for a different attempt

File: [unknown-05.jsonl](unknown-05.jsonl). Split: **test**. Category: **insufficient_evidence**.

Gold root cause: The old OOM termination belongs to attempt 1; no termination or log evidence establishes the cause of the selected later attempt 3 failure.

Causal assessment: The selected target is attempt 3 at 09:00:15Z, while the OOM observation explicitly describes attempt 1 at 08:30:00Z. Current backoff contains no termination/log evidence for attempt 3.

Claim boundaries: Keep a real historical OOM observation intact, but do not assign it to the selected later failure.

Gold evidence IDs: `termination-1`, `status-1`, `metadata-1`. Exact excerpts are stored with the record and validated against the observation text.

Read-only expected checks:

- Inspect termination details, events, and logs for attempt 3 rather than reuse attempt 1 diagnostics.


Review checklist:

- [x] Validate schema, gold references, catalogue split, and group-specific evidence consistency.

  <!-- Completed 2026-11-12, Codex: unknown-05 passed authored-template checks, including its evidence/reference and split assertions. -->

- [x] Confirm the diagnosis or information gap follows from the supplied observations without hidden assumptions.

  <!-- Completed 2026-11-12, Codex: unknown-05 causal assessment and unsupported claims are recorded above. -->

- [x] Inspect read-only checks and prompt-visible facts for safety, diagnostic scope, and gold-annotation leakage.

  <!-- Completed 2026-11-12, Codex: expected checks inspect supplied/current information without executing repairs; gold fields and tags remain outside PromptInput. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex, accepted under project-owner authorization for passing agent reviews. -->

## unknown-06: No target among two container failures

File: [unknown-06.jsonl](unknown-06.jsonl). Split: **test**. Category: **insufficient_evidence**.

Gold root cause: Two containers have different failures and no target container is specified, so a single primary diagnosis cannot be selected.

Causal assessment: The incident scope does not select a container. uploader has an unauthorized pull; metrics-sidecar separately has readiness 503. Both may be independently diagnosable but there is no single selected target.

Claim boundaries: Abstention concerns target ambiguity, not an assertion that all observed failures are unknowable. Recommended action asks which incident/container is primary.

Gold evidence IDs: `event-1`, `event-2`, `metadata-1`. Exact excerpts are stored with the record and validated against the observation text.

Read-only expected checks:

- Clarify which container and failure should be the primary incident target; inspect each container separately.


Review checklist:

- [x] Validate schema, gold references, catalogue split, and group-specific evidence consistency.

  <!-- Completed 2026-11-12, Codex: unknown-06 passed authored-template checks, including its evidence/reference and split assertions. -->

- [x] Confirm the diagnosis or information gap follows from the supplied observations without hidden assumptions.

  <!-- Completed 2026-11-12, Codex: unknown-06 causal assessment and unsupported claims are recorded above. -->

- [x] Inspect read-only checks and prompt-visible facts for safety, diagnostic scope, and gold-annotation leakage.

  <!-- Completed 2026-11-12, Codex: expected checks inspect supplied/current information without executing repairs; gold fields and tags remain outside PromptInput. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex, accepted under project-owner authorization for passing agent reviews. -->
