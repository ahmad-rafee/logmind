# Concrete baseline templates

Each JSONL file contains one fully populated `Incident`, used by the seeded variant generator. These are fictional baseline records, not Kubernetes manifests or executable migrations. `make generate` builds a 150-record candidate; the seed-42 data and template inputs are preserved in [frozen v1](../../frozen/README.md). Review metadata lives here rather than in model-visible observations.

## Review progress

**All 42 baseline templates are reviewed and accepted**: six for each of the six incident classes plus six insufficient-evidence scenarios. Each split contains 14 baselines: two per class plus two insufficient-evidence cases. These are fixed baselines, not the planned 150-record variant dataset. The project owner authorized Codex to review and accept passing templates without further human approval. Acceptance records identify this as agent review, not independent human verification.

The original migration reviews are below. The remaining reviews record evidence, claim boundaries, read-only checks, and completion comments:

| Group | Templates | Review record |
| --- | --- | --- |
| Container crash | crash-01 through crash-06 | Migration reviews below; [remaining crash/OOM reviews](CRASH_AND_OOM_REVIEW.md) |
| OOM | oom-01 through oom-06 | [Crash/OOM review](CRASH_AND_OOM_REVIEW.md) |
| Image pull | image-01 through image-06 | [Image-pull review](IMAGE_PULL_REVIEW.md) |
| Probes | probe-01 through probe-06 | [Probe review](PROBE_REVIEW.md) |
| Configuration | config-01 through config-06 | [Configuration review](CONFIG_REVIEW.md) |
| Scheduling | schedule-01 through schedule-06 | [Scheduling review](SCHEDULING_REVIEW.md) |
| Insufficient evidence | unknown-01 through unknown-06 | [Insufficient-evidence review](INSUFFICIENT_EVIDENCE_REVIEW.md) |

Run `uv run --locked pytest tests/test_templates.py` to validate all 42 baselines against their schemas and catalogue assignments, verify class/split balance and unique IDs, and check process, pull, probe, configuration, scheduling, and information-gap evidence. For an individual file, use `make validate INCIDENTS=data/scenarios/templates/oom-01.jsonl` (substitute its filename). `tests/test_generation.py` verifies seeded variants and output checksums; `tests/test_freezing.py` checks audits, frozen releases, and change detection. Verify the sealed release with `make verify-dataset` before baseline runs.

## crash-01: migration attempts to add an existing column

File: [crash-01.jsonl](crash-01.jsonl). Proposed split: train. Status: **reviewed and accepted for future generation**. Reviewer: Codex, 2026-11-12, under the project owner's instruction to accept passing reviews. This is an agent review accepted by the owner, not a separate independent human review.

The names, timestamp, SQL statement, and messages were authored for this project. The pattern was motivated by a read-only cluster inspection, but this is synthetic data, not a redacted production-log export or a controlled-cluster experiment.

### Observations and gold evidence

| Evidence ID | Observation | Role |
| --- | --- | --- |
| metadata-1 | Target is container migrate, attempt 1, in a fictional one-shot Job with restartPolicy Never and backoffLimit 0. | Establishes incident scope; no repeated restart is required. |
| status-1 | The target pod phase is Failed. | Establishes failed execution; insufficient to determine the cause alone. |
| log-1 | The migration process executes ALTER TABLE parcels ADD COLUMN delivery_note text. | Identifies the failed operation and intended column. |
| log-2 | PostgreSQL reports SQLSTATE 42701 and that delivery_note already exists in parcels; process reports an unhandled exception and exit 1. | Direct supporting evidence for the duplicate-column failure. |
| termination-1 | The same container/attempt terminates with reason Error and exit 1 after the log timestamps. | Connects the error to the unsuccessful process exit. |

Gold category: `container_crash`.

Gold root cause: **The migration process exited after PostgreSQL rejected adding delivery_note to parcels because that column already exists.**

Gold supporting excerpts reference log-1, log-2, and termination-1. SQLSTATE 42701 corresponds to duplicate_column in the [PostgreSQL error-code documentation](https://www.postgresql.org/docs/current/errcodes-appendix.html).

The record does not establish whether an earlier partial migration, a manual schema change, or a concurrent deployment created the column. It does not establish database corruption, OOM, failed probes, or missing Kubernetes configuration. Recommendations therefore inspect the migration, existing schema, and migration history without applying changes.

### Review checklist

- [x] Validate required fields, exact types, unique observation IDs, and gold excerpt references with the existing incident validator.
  <!-- Completed 2026-11-12: make validate INCIDENTS=data/scenarios/templates/crash-01.jsonl passed for the single baseline record. This is structural validation, not human causal approval. -->
- [x] Confirm that log-1/log-2 and termination-1 support the stated root cause for the same container/attempt.
  <!-- Completed 2026-11-12, Codex: matching pod/container/attempt details; SQL at 09:00:02Z, duplicate-column error at 09:00:03Z, and exit 1 at 09:00:04Z form a consistent causal sequence. Accepted under the project owner's instruction. -->
- [x] Confirm that the root cause does not speculate about how the pre-existing column was created.
  <!-- Completed 2026-11-12, Codex: the gold claim stops at PostgreSQL rejecting the duplicate column; it does not attribute schema history or concurrency. -->
- [x] Confirm that expected_actions contain only useful read-only checks.
  <!-- Completed 2026-11-12, Codex: checks inspect the migration, schema metadata, and migration history; executing, rolling back, and rerunning migrations are explicitly excluded. -->
- [x] Confirm that observations and the opaque incident ID contain no gold annotations; authentic errors remain intact.
  <!-- Completed 2026-11-12, Codex: observations contain workload facts, logs, and termination details; labels and gold fields stay outside PromptInput. Incident ID is opaque; SQLSTATE remains authentic diagnostic evidence. -->
- [x] Record reviewer, review date, and acceptance basis before accepting this template for generation.
  <!-- Completed 2026-11-12: reviewer Codex; project owner authorized acceptance when the review passes. No independent human causal review is claimed. -->

### Validation

From the project root:

```bash
make validate INCIDENTS=data/scenarios/templates/crash-01.jsonl
```

Only `Incident.to_prompt_input()` output may enter a future prompt. Do not include this review document, scenario_id, split, category, root_cause, evidence, expected_actions, or variant_tags. All retries/variants of this scenario must retain scenario_id crash-01 and the train split.

## crash-02: migration attempts to create an existing table

File: [crash-02.jsonl](crash-02.jsonl). Proposed split: train. Status: **reviewed and accepted for future generation**. Reviewer: Codex, 2026-11-12, under the same project-owner authorization for passing reviews. No independent human review is claimed.

This is a separately authored fictional Job, not a second retry of crash-01 and not a production-log export. Both migration-conflict scenarios remain in train because they share a related failure mechanism.

### Observations and gold evidence

| Evidence ID | Observation | Role |
| --- | --- | --- |
| metadata-1 | Container migrate, attempt 1, in Job dispatch-schema-task; restartPolicy Never and backoffLimit 0. | Identifies the selected one-shot execution. |
| status-1 | The target pod phase is Failed. | Establishes failed execution without asserting its cause. |
| log-1 | The process executes CREATE TABLE public.dispatch_batches. | Identifies the operation that fails. |
| log-2 | SQLSTATE 42P07 reports that relation dispatch_batches already exists; the unhandled exception exits with code 1. | Direct evidence for the migration conflict. |
| termination-1 | The same attempt terminates with reason Error and exit 1 after the error. | Connects the migration error to process termination. |
| metadata-2 | A supplied read-only database catalogue snapshot identifies public.dispatch_batches as a BASE TABLE. | Supports saying an existing table, rather than guessing the kind of conflicting relation. |

Gold category: `container_crash`.

Gold root cause: **The migration process exited after PostgreSQL rejected creating public.dispatch_batches because that table already exists.**

SQLSTATE 42P07 corresponds to duplicate_table in the [PostgreSQL error-code documentation](https://www.postgresql.org/docs/current/errcodes-appendix.html). The supplied catalogue snapshot is optional diagnostic enrichment in general, but required by this concrete template's table-specific claim. It is not collected by LogMind. The record does not establish who created the existing table, whether a previous migration partially succeeded, or whether concurrent deployments were involved.

### Review checklist

- [x] Validate the record with the existing incident validator.
  <!-- Completed 2026-11-12: make validate INCIDENTS=data/scenarios/templates/crash-02.jsonl passed, including gold excerpt references. -->
- [x] Confirm that the failed statement, error, and termination belong to the same container/attempt.
  <!-- Completed 2026-11-12, Codex: matching dispatch-schema-task pod/container/attempt details; statement at 10:30:02Z, error at 10:30:03Z, exit at 10:30:04Z. -->
- [x] Confirm that the existing-table diagnosis is supported without speculation about schema history.
  <!-- Completed 2026-11-12, Codex: SQLSTATE 42P07 and BASE TABLE catalogue metadata support the claim; the gold root cause assigns no author or historical cause to the existing table. -->
- [x] Confirm that recommendations are read-only and observations contain no injected gold annotations.
  <!-- Completed 2026-11-12, Codex: checks inspect migration source, catalogue, and migration history; PromptInput excludes label, split, evidence, expected actions, and variant tags. -->
- [x] Record reviewer, date, and acceptance basis.
  <!-- Completed 2026-11-12: reviewer Codex; accepted under the project owner's instruction for passing reviews, not independent human verification. -->

### Validation

```bash
make validate INCIDENTS=data/scenarios/templates/crash-02.jsonl
```

The prompt-input boundary described for crash-01 also applies here. Keep scenario_id crash-02 and split train for every future retry or variant.
