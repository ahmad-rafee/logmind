# Synthetic scenario catalogue (v4 baseline templates)

This is the scenario design for Phase 0 step 2. Review status: **all 42 baseline templates reviewed by Codex and accepted under project-owner authorization on 2026-11-12**. Seeded generation produces a [150-record candidate](../generated/README.md); its unchanged seed-42 bytes are preserved in [frozen v1](../frozen/README.md), with splits assigned before augmentation. No template has been exercised against a live cluster. The [template review index](templates/README.md) links baseline acceptance evidence and concrete fictional records. Agent review accepted by the owner is recorded separately from independent human review. Generated variants have automated consistency checks, not independent human causal review.

## Dataset plan

Define 36 answerable scenarios: six per class, two per split. Generate four variants per answerable scenario: baseline, wording, noisy, and long. Add six distinct insufficient-evidence scenarios, one record each. This gives **150 records across 42 scenarios**, with 50 records per split: eight per incident class plus two insufficient-evidence cases. The six incident classes are balanced; abstentions are reported separately.

Variant generation preserves the causal mechanism, split, scenario_id, supporting evidence, and expected diagnosis. Generator v1 changes only allowlisted snapshot framing in metadata/status text for wording variants; raw diagnostic messages, reason codes, structured fields, and application logs are unchanged. Noise and long variants add benign supplied workload notes, never contradictory current failures or new process logs. Incomplete cases below are separate scenarios, not relabeled answerable variants. Local seeded random generators and stable ordering make regeneration reproducible; no language model is used.

These splits hold out scenario templates and contexts, not necessarily failure mechanisms. For example, config-01/config-02 and config-05/config-06 share the absent-resource mechanism despite different surrounding circumstances. OOM scenarios share OOM termination signals, and enriched examples share the limit-exhaustion mechanism. Related duplicate-column and duplicate-table migration failures are both assigned to train. Retries from the same Job or rollout must remain in one scenario/split, not count as independent causes. Scenario-ID isolation prevents variants crossing splits but does not establish generalization to unseen failure mechanisms or independent real-world incidents. Report scenario counts separately from variants and state this limitation alongside results.

## Labeling and evidence policy

- Label the earliest supported primary cause for the selected pod/container and attempt. Keep container identity and attempt/timestamps explicit whenever observations could refer to different failures.
- CrashLoopBackOff, Pending, nonzero exit codes, and exit code 137 alone do not establish a detailed cause. Include the causal evidence specified below or abstain.
- `container_crash` covers unsuccessful application/process exits, including failed migration Jobs; repeated restarts or CrashLoopBackOff are not required. It excludes termination caused by OOM or a failed probe. A malformed file that exists belongs here; an absent referenced ConfigMap/Secret or required key belongs to `missing_config`.
- Successful Job completion (Succeeded pod phase, Completed container reason, exit 0) is expected behavior, not an incident merely because the container is no longer ready. The six-class dataset assumes a supplied incident target; do not map healthy Job completion to a failure label or automatically to insufficient_evidence. Healthy controls belong in a separate future incident-screening evaluation, outside this 150-record diagnosis set.
- Readiness failure makes a container unready; it does not itself restart it. Liveness/startup failure may cause restarts. Probe cases must establish the probe/configuration problem rather than invent an application failure.
- Registry credential problems are `image_pull_failure` when a current pull failure is established, including a missing image-pull Secret. `missing_config` cases concern workload configuration rather than image-pull credentials.
- An `oom_killed` record must include OOM termination evidence for the target container/attempt. A container-limit or application-mechanism claim additionally requires the limit, correlated cgroup evidence, and relevant measurements. Without those additional diagnostics, retain only the supported OOM finding and do not assert cache growth, worker allocations, buffering, or a container-limit breach. Exit code 137 alone remains insufficient. Do not equate node-pressure eviction with a container limit breach or infer a memory leak without measurements.
- Cgroup events and allocation measurements are optional supplied diagnostics, not assumed fields of ordinary pod status/events/logs. When supplied, represent cgroup diagnostics as log observations and measurements as log or metadata observations, with `details` recording diagnostic source, target container/attempt, and capture time. These are synthetic supplied measurements, not measurements collected by LogMind. Only the enriched OOM scenarios below require this additional evidence; ordinary OOM snapshots use narrower root causes. Missing measurements must not be filled in from an author's assumed mechanism.
- Startup-budget claims require observed startup milestone timings or an explicitly identified successful prior attempt with comparable image, configuration, and resources. Do not invent a completed startup duration for an attempt killed before completion. Prior-attempt evidence supports a comparison, not proof that the failing attempt would finish at exactly the same time.
- Observations contain raw diagnostic facts, never injected gold labels, scenario IDs, variant descriptions, gold annotations, or answer text. Preserve authentic reason codes and diagnostic messages such as `OOMKilled`, `FailedScheduling`, and `CrashLoopBackOff`, even when they directly indicate a category. Incident IDs must be opaque and independent of labels/splits. Gold excerpts reference existing observation text verbatim.
- Recommended checks are read-only inspections. Do not instruct the system to change resources or execute repairs.

## Answerable scenarios

The evidence column states what the eventual template must contain, not an exact Kubernetes message to fabricate. Each row needs concrete observations, gold excerpts, and read-only expected checks before it becomes an executable template.

| scenario_id | Split | Category | Primary cause | Required distinguishing evidence |
| --- | --- | --- | --- | --- |
| crash-01 | train | container_crash | Migration Job exits after attempting to add an existing database column | PostgreSQL SQLSTATE 42701 and duplicate-column message, attempted ALTER TABLE statement, and matching process exit 1; do not infer who created the column. |
| crash-02 | train | container_crash | Migration Job exits after attempting to create an existing database table | PostgreSQL SQLSTATE 42P07 and duplicate-table message, attempted CREATE TABLE statement, and matching process exit 1; no unsupported migration-history explanation. |
| crash-03 | validation | container_crash | Application exits after startup database connection refusal | Fatal startup log and connection refusal for the same attempt; do not infer why the database refuses. |
| crash-04 | validation | container_crash | Application cannot read a mounted file due to permissions | Permission-denied log, file identity/mount metadata, and application exit. |
| crash-05 | test | container_crash | Application runtime lacks a required module | Import/module-not-found fatal log and nonzero exit; image was pulled successfully. |
| crash-06 | test | container_crash | Process crashes with segmentation fault | Matching signal/exit details and crash log; no claim about the underlying code defect. |
| oom-01 | train | oom_killed | Job container is terminated with OOMKilled | Target container state reports OOMKilled with matching attempt/timestamps; configured limit is context only, not proof of a limit breach or memory-growth mechanism. |
| oom-02 | train | oom_killed | In-memory cache grows beyond container limit | OOMKilled, limit, cache-size measurements, and matching cgroup OOM event. |
| oom-03 | validation | oom_killed | Service container's explicitly selected previous attempt was OOM-killed | lastState termination reason OOMKilled and timestamps, restart count, and current running status; diagnose the selected previous attempt, not an ongoing outage or presumed leak. |
| oom-04 | validation | oom_killed | Memory-backed temporary files exhaust container memory allowance | OOMKilled, memory-backed volume metadata/usage, limit, and matching cgroup OOM event. |
| oom-05 | test | oom_killed | Init container's latest terminated attempt was OOM-killed, delaying application startup | Init-container termination reason OOMKilled, attempt/timestamps, and application waiting status; do not misattribute termination to the main container or infer the allocation mechanism. |
| oom-06 | test | oom_killed | JVM memory growth exhausts container allowance while maximum heap is configured above that allowance | OOMKilled, configured heap and limit, measured heap/non-heap growth and allocation request, and matching cgroup OOM event; do not claim measured heap alone exceeded the container limit. |
| image-01 | train | image_pull_failure | Referenced image tag does not exist | Current pull error identifying missing manifest/tag and exact image reference. |
| image-02 | train | image_pull_failure | Private registry rejects image pull as unauthorized | Current unauthorized pull response and private image reference; no credential values or unsupported claims about which credential is wrong. |
| image-03 | validation | image_pull_failure | Registry hostname cannot be resolved | Current pull failure with name-resolution error; do not claim a particular DNS configuration defect. |
| image-04 | validation | image_pull_failure | Registry certificate verification fails | Current pull failure with explicit certificate verification error; no invented certificate diagnosis. |
| image-05 | test | image_pull_failure | Registry has no image manifest for the node platform | Current no-matching-platform pull error plus node architecture and image reference. |
| image-06 | test | image_pull_failure | Registry rate limit prevents image retrieval | Current explicit rate-limit/429 pull error and affected image reference. |
| probe-01 | train | probe_failure | Readiness probe uses a nonexistent HTTP path | Readiness 404, probe path, and documented serving endpoint; running container with no probe-caused restart. |
| probe-02 | train | probe_failure | Liveness probe targets the wrong port | Probe connection refusal, configured probe/listening ports, and matching probe-triggered restart. |
| probe-03 | validation | probe_failure | Startup probe exhausts its budget while the application is still initializing | Configured probe budget, timestamped initialization milestones, probe failures, and matching restart. If citing completed startup time, identify a comparable successful prior attempt; do not claim the failed attempt completed or would finish at an exact time. |
| probe-04 | validation | probe_failure | Exec readiness probe references an absent probe binary | Probe command and executable-not-found event; application remains running. |
| probe-05 | test | probe_failure | HTTPS readiness probe targets a plain HTTP endpoint | Probe scheme/port, observed server protocol, and matching protocol error. |
| probe-06 | test | probe_failure | Liveness timeout is shorter than measured health-handler response time | Timeout events, timeout setting, correlated handler timings, and matching restart; no unsupported claim about why handler is slow. |
| config-01 | train | missing_config | Referenced ConfigMap volume is absent | Failed mount identifies non-optional ConfigMap and namespace. |
| config-02 | train | missing_config | Required Secret environment reference is absent | Container configuration error identifies missing non-optional Secret. |
| config-03 | validation | missing_config | Existing ConfigMap lacks a required environment key | Configuration error names missing key; metadata confirms referenced ConfigMap exists. |
| config-04 | validation | missing_config | Existing Secret lacks a required projected key | Volume/configuration error identifies absent key and existing Secret; no secret values. |
| config-05 | test | missing_config | Referenced ConfigMap exists only in another namespace | Current namespace lookup failure and supplied cross-namespace metadata. |
| config-06 | test | missing_config | Workload references an old Secret name after replacement under a new name | Current missing-Secret error, stale workload reference, and supplied release metadata documenting deletion of the old object and creation of its replacement; no Kubernetes in-place rename is assumed. |
| schedule-01 | train | scheduling_failure | CPU requests cannot fit any eligible node | FailedScheduling insufficient-CPU event plus requests and eligible-node allocatable/requested totals. |
| schedule-02 | train | scheduling_failure | Memory requests cannot fit any eligible node | FailedScheduling insufficient-memory event plus requests and eligible-node allocatable/requested totals. |
| schedule-03 | validation | scheduling_failure | Node selector matches no eligible node | FailedScheduling selector mismatch, selector, and node labels. |
| schedule-04 | validation | scheduling_failure | Pod lacks tolerations for taints on every otherwise eligible node | FailedScheduling untolerated-taint evidence plus node taints and pod tolerations. |
| schedule-05 | test | scheduling_failure | Required pod anti-affinity excludes all eligible nodes | FailedScheduling anti-affinity evidence, required rule, and existing pod placement. |
| schedule-06 | test | scheduling_failure | Requested GPU resource is unavailable on eligible nodes | FailedScheduling insufficient extended-resource evidence plus GPU requests and node resource totals. |

## Insufficient-evidence scenarios

All six carry category `insufficient_evidence`. The root_cause must describe the information gap rather than assert a hidden cause. Evidence can cite the limited observations; checks should request the specific missing diagnostic information.

Tag unknown-01 through unknown-05 with `missing_diagnostics`, and unknown-06 with `target_ambiguity`, in variant_tags only; do not expose these annotations in prompt input. Report abstention results separately for the two groups, alongside the overall result. With only one target-ambiguity record, report its individual outcome and support rather than a broad reliability claim.

| scenario_id | Split | Category | Available observations | Why the system should abstain |
| --- | --- | --- | --- | --- |
| unknown-01 | train | insufficient_evidence | CrashLoopBackOff and restart count only | No prior termination details, logs, or events establish the cause. |
| unknown-02 | train | insufficient_evidence | Pending with no scheduling, pull, or mount events | Pod phase alone cannot distinguish the six causes. |
| unknown-03 | validation | insufficient_evidence | Exit code 137 without reason or memory evidence | Exit code alone cannot establish a container memory-limit OOM. |
| unknown-04 | validation | insufficient_evidence | Readiness is false, with no probe result or application diagnostics | Unready status alone cannot establish a probe configuration problem. |
| unknown-05 | test | insufficient_evidence | Old OOM termination and a later generic crash status, with no current termination/log evidence | A historical cause cannot be assigned to the current failed attempt. |
| unknown-06 | test | insufficient_evidence | One sidecar has a pull error, another container has a probe error, and no target container is specified | Target ambiguity: each failure may be diagnosable, but a single primary target cannot be selected. Ask which container/incident to diagnose rather than claim both causes are unknown. |

## Human review checklist

### Design review

- [x] Acknowledge shared mechanisms across splits and limit generalization claims accordingly.
  <!-- Completed 2026-11-12: project owner accepted the split limitations during review; Dataset plan documents shared absent-resource/OOM mechanisms and distinguishes template isolation from unseen-mechanism generalization. -->
- [x] Define readiness behavior separately from liveness/startup-triggered restarts.
  <!-- Completed 2026-11-12: project owner accepted the probe policy in Labeling and evidence policy; verification of concrete probe observations remains open below. -->
- [x] Define the boundary between missing workload configuration and image retrieval/authentication failures.
  <!-- Completed 2026-11-12: project owner accepted missing_config versus image_pull_failure policy, including image-pull credentials; consistent application in concrete templates remains open below. -->
- [x] Limit OOM claims to supplied evidence and require additional diagnostics for deeper mechanisms.
  <!-- Completed 2026-11-12: project owner accepted OOM claim boundaries; OOMKilled supports an OOM finding, while container-limit and application-mechanism claims require correlated additional evidence. -->
- [x] Preserve authentic diagnostic reason codes while prohibiting injected gold annotations.
  <!-- Completed 2026-11-12: project owner accepted retention of OOMKilled, FailedScheduling, and other authentic messages; generated-record leakage checks remain open below. -->

### Scenario amendments and template verification

- [x] Incorporate fictional migration Job failures and ordinary OOM snapshots inspired by the cluster inspection; distinguish successful Completed Jobs from failures.
  <!-- Completed 2026-11-12: draft v3 replaces crash-01/crash-02 with migration conflicts and oom-01/oom-03/oom-05 with ordinary OOM snapshots. Labeling policy includes unsuccessful Job exits and excludes healthy completions; the 36-scenario class plan is preserved. This closes catalogue amendments only, not concrete template review. -->
- [x] Each baseline scenario's root cause or information gap follows from supplied observations, without hidden assumptions.
  <!-- Completed 2026-11-12, Codex under project-owner authorization: all 42 templates have individual causal assessments and claim boundaries linked from templates/README.md; schemas validate every gold evidence excerpt. This acceptance applies to baselines, not uncreated variants. -->
- [x] Causes shared across splits differ in mechanism/context rather than names alone; related mechanisms are acknowledged in limitations.
  <!-- Completed 2026-11-12, Codex: reviewed the seven six-scenario groups, each with two scenarios per split; contexts/constraints differ, while shared OOM and missing-resource mechanisms are explicitly acknowledged in Dataset plan. No unseen-mechanism generalization is claimed. -->
- [x] OOM cases distinguish supported container-limit kills from OOM terminations without established kill mechanism, node pressure, or external kills.
  <!-- Completed 2026-11-12, Codex under project-owner authorization: all six OOM templates reviewed; oom-01/03/05 use narrow OOMKilled claims, while oom-02/04/06 supply correlated container cgroup limit/OOM evidence. Ordinary cases do not infer node pressure or limit breach. See templates/CRASH_AND_OOM_REVIEW.md. -->
- [x] Enriched OOM evidence identifies its source, container/attempt, and time; less detailed inputs receive narrower gold claims.
  <!-- Completed 2026-11-12, Codex: supplied measurements in oom-02/04/06 include provenance, matching cgroup/target identity, and timestamps; claim boundaries and quantitative checks are documented in the batch review and tests/test_templates.py. -->
- [x] Probe cases distinguish readiness changes from probe-triggered restarts.
  <!-- Completed 2026-11-12, Codex: probe-01/04/05 remain running and unready with zero restarts; probe-02/03/06 have explicit Killing events and matched termination timelines. See templates/PROBE_REVIEW.md and template tests. -->
- [x] Startup timing claims identify milestones or comparable prior attempts without inventing completion of a killed attempt.
  <!-- Completed 2026-11-12, Codex: probe-03 cites a current initialization milestone before the third failed startup probe and restart; it asserts no completed startup duration or counterfactual finish time. -->
- [x] Missing configuration and registry credentials follow the labeling policy consistently.
  <!-- Completed 2026-11-12, Codex: config-01 through config-06 concern required workload objects/keys, while image-02 has a current unauthorized image pull. References/key names are provided without credential values. See CONFIG_REVIEW.md and IMAGE_PULL_REVIEW.md. -->
- [x] Review image-01 through image-06 using direct image-pull evidence and bounded diagnoses.
  <!-- Completed 2026-11-12, Codex under project-owner authorization: six fictional image templates reviewed; templates/IMAGE_PULL_REVIEW.md records evidence, read-only checks, limits, and individual completion comments. tests/test_templates.py checks pull identity/timing, lack of container execution, platform evidence, and credential-reference boundaries. Workload-configuration template review remains open. -->
- [x] Ambiguous cases genuinely lack sufficient evidence for a single selected diagnosis.
  <!-- Completed 2026-11-12, Codex: unknown-01 through unknown-05 deliberately omit diagnostic/attempt information; unknown-06 omits target selection among two distinct container failures. Individual gaps are assessed in INSUFFICIENT_EVIDENCE_REVIEW.md. -->
- [x] Missing diagnostics and target ambiguity have separate gold-only tags and a documented reporting requirement; authentic diagnostic reason codes are retained.
  <!-- Completed 2026-11-12, Codex: five missing_diagnostics templates and one target_ambiguity template preserve raw status/event reasons; tests confirm the tags do not enter PromptInput. Separate evaluator reporting remains a follow-through task below. -->
- [x] Read-only checks are useful and no baseline observation leaks a gold annotation.
  <!-- Completed 2026-11-12, Codex: reviewed all expected_actions and raw observation payloads; checks inspect diagnostics/specification/inventories without repairs, gold fields remain outside PromptInput, and incident IDs are opaque. Real diagnostic messages remain intact. -->
- [x] Record reviewer, date, review method, and any amendments for every baseline template.
  <!-- Completed 2026-11-12: all 42 templates have dated Codex review records with completion comments and owner-authorization basis, linked in templates/README.md. No independent human review or live-cluster reproduction is claimed. -->

### Generation and evaluation follow-through

- [x] Verify that generated variants retain causal evidence, scenario IDs, split isolation, and annotation separation.
  <!-- Completed 2026-11-12: tests/test_generation.py checks all 150 candidate records against their original templates, preserving raw diagnostic facts and labels, revalidating adjusted gold excerpts, retaining unknown-case information gaps, and verifying scenario split isolation and prompt boundaries. No independent human review of variants is claimed. -->
- [x] Implement separate abstention reporting for missing diagnostics and target ambiguity in the evaluator.
  <!-- Completed 2026-11-12: evaluation.py reports support and correct-abstention rates for both groups, with zero-denominator handling covered by tests. Frozen test has one case per group; rules abstain correctly on both and the model on neither. Raw classification/review artifacts are in experiments/reports/phase0. -->

## Amendment record

- 2026-11-12, Codex technical review (draft v2): clarified optional enriched OOM diagnostics and narrower claims when unavailable; corrected startup timing evidence; retained authentic diagnostic reason codes; documented shared mechanisms across splits; separated missing-diagnostic abstentions from target ambiguity. This records an automated design review, not completed human review or executable-template verification.
- 2026-11-12, project owner review with Codex assistance: accepted the five design decisions checked above and requested their closure. Split design acceptance from scenario amendments and template verification; the full causal-template review remains incomplete.
- 2026-11-12, Codex implementation (draft v3), requested by project owner: incorporated fictional migration conflicts and ordinary OOM contexts; clarified successful Jobs and related retries; created the first schema-valid crash-01 baseline template and review notes. No raw cluster logs, resource names, or credentials were copied into the template. Human template acceptance remains pending.
- 2026-11-12, Codex template review under subsequent project-owner authorization: accepted passing crash-01 review, created and reviewed crash-02, and recorded completion evidence in templates/README.md. Both are accepted for future generation; 2 of 42 planned scenarios have concrete reviewed templates. This supersedes the earlier pending-acceptance status for crash-01 and does not claim independent human review.
- 2026-11-12, Codex continuing review under project-owner authorization: created and accepted crash-03 through crash-06 and oom-01 through oom-06. All 12 authored records have structural/evidence checks; the ten new causal assessments appear in templates/CRASH_AND_OOM_REVIEW.md. Tightened oom-06 to distinguish total memory exhaustion from heap alone exceeding the limit. Thirty planned scenarios, variant generation, and dataset freezing remain pending.
- 2026-11-12, Codex image-pull review under project-owner authorization: created and accepted image-01 through image-06, with individual assessments in templates/IMAGE_PULL_REVIEW.md. Clarified image-02 as an unauthorized pull rather than proof of incorrect credentials. Eighteen of 42 planned templates are reviewed; the remaining 24, generation, and dataset freezing remain pending.
- 2026-11-12, Codex completion review under project-owner authorization (v4): created and accepted the remaining six probe, six configuration, six scheduling, and six insufficient-evidence templates. All 42 fixed baselines now have direct gold evidence and bounded claims, with 14 templates per split. Configuration replacement is described as delete/create rather than an in-place Secret rename. Generated variants, the 150-record dataset, freezing, and evaluator reporting remain pending. This supersedes the earlier partial-completion statuses above.
- 2026-11-12, seeded generation v1: implemented conservative snapshot wording, benign metadata notes, and longer-context variants. Generated 150 seed-42 candidate records (50 per split) with strict checksum/count manifests; tests verify reproducibility, input preservation, split isolation, and refusal to overwrite differing outputs. Dataset freezing and evaluator reporting remain open. This supersedes the earlier pending-generation status.
- 2026-11-12, freeze v1: audited and preserved the seed-42 dataset at data/frozen/v1, including reproduction inputs and a published manifest pin. Verified data/counts/split membership/provenance and regenerated all candidate artifacts byte-for-byte from a writable copy of the captured bundle. Dataset creation/freezing is complete; evaluator reporting remains open. Earlier pending-freeze statements above are historical.

## Technical references

Semantics checked against official Kubernetes documentation; these references support scenario design, not verification of executable fixtures:

- [Liveness, readiness, and startup probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Container resource management](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)
- [Image pulling](https://kubernetes.io/docs/concepts/containers/images/)
- [Required Secret references](https://kubernetes.io/docs/concepts/configuration/secret/)
- [Node placement constraints](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/)
- [Job execution and completion](https://kubernetes.io/docs/concepts/workloads/controllers/job/)
- [PostgreSQL SQLSTATE codes](https://www.postgresql.org/docs/current/errcodes-appendix.html) (42701: duplicate_column; 42P07: duplicate_table)
