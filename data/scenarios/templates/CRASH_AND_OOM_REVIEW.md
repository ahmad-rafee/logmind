# Crash and OOM template review batch

Reviewer: **Codex**. Review date: **2026-11-12**. Accepted under the project owner's instruction to review and close passing templates without further human approval. This is agent review, not independent human review or live-cluster verification.

All ten records are fictional fixed baselines. Their source is synthetic; none embeds production logs, names, credentials, or gold annotations inside observations. Splits follow the catalogue. Metadata, application diagnostics, file inventories, and memory/cgroup measurements are supplied snapshot facts, not actions executed by LogMind. The generator and frozen dataset remain pending.

Run `uv run --locked pytest tests/test_templates.py` for the repeatable structural, identity, timing, leakage, and memory-consistency checks. Schema validation also checks every gold excerpt against its observation text. These checks supplement the causal assessments below; they do not establish real-world realism by themselves.

## crash-03: Startup database connection refusal

File: [crash-03.jsonl](crash-03.jsonl). Split: **validation**. Category: **container_crash**. Status: **reviewed and accepted for future generation**.

Gold root cause: The application exited during startup after its connection to ledger-db.demo-app.svc:5432 was refused.

Causal assessment: log-2 explicitly reports connection refusal and process exit; termination-1 matches the same container and attempt after that log.

Claim boundaries: The snapshot does not identify whether the database process, Service endpoints, port configuration, or a network device caused the refusal.

Gold supporting excerpts:

- `log-2`: connection refused; startup aborted, exiting with code 1

- `termination-1`: Container api attempt 1 terminated: reason=Error, exitCode=1


Read-only expected checks:

- Inspect the configured database hostname and port without changing them.

- Inspect the database Service endpoints, target pod readiness, and listener logs for the same time window.


Review checklist:

- [x] Strict schema, evidence references, catalogue split, target identity, and diagnostic timing pass.

  <!-- Completed 2026-11-12, Codex: crash-03 passes tests/test_templates.py and existing JSONL validation; no live cluster execution is claimed. -->

- [x] Gold diagnosis is supported by the cited observations and respects the claim boundaries above.

  <!-- Completed 2026-11-12, Codex: causal assessment and withheld claims for crash-03 recorded above. -->

- [x] Expected checks inspect information without repairs; prompt-visible fields contain no injected gold annotations.

  <!-- Completed 2026-11-12, Codex: inspected the listed checks and observation payloads; PromptInput contains only opaque incident ID and observations. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex, authorized by project owner to accept passing reviews without additional human approval. -->

## crash-04: Mounted-file access denied

File: [crash-04.jsonl](crash-04.jsonl). Split: **validation**. Category: **container_crash**. Status: **reviewed and accepted for future generation**.

Gold root cause: The application exited because opening the mounted file /srv/settings/runtime.ini was denied by file permissions.

Causal assessment: The fatal EACCES log identifies the mounted file, supplied inventory confirms it exists with restrictive permissions, and the same process exits 1.

Claim boundaries: The diagnosis does not assign a specific ACL, security-policy defect, or configuration author; it does not confuse access denial with an absent ConfigMap.

Gold supporting excerpts:

- `log-1`: open /srv/settings/runtime.ini: Permission denied (EACCES)

- `metadata-2`: File runtime.ini exists; owner uid=0 gid=0 mode=0600; application uid=1000 gid=1000

- `termination-1`: Container api attempt 1 terminated: reason=Error, exitCode=1


Read-only expected checks:

- Inspect the supplied file ownership/mode and the container user/group configuration.

- Inspect the volume mount and applicable file-access policy without changing permissions or restarting the workload.


Review checklist:

- [x] Strict schema, evidence references, catalogue split, target identity, and diagnostic timing pass.

  <!-- Completed 2026-11-12, Codex: crash-04 passes tests/test_templates.py and existing JSONL validation; no live cluster execution is claimed. -->

- [x] Gold diagnosis is supported by the cited observations and respects the claim boundaries above.

  <!-- Completed 2026-11-12, Codex: causal assessment and withheld claims for crash-04 recorded above. -->

- [x] Expected checks inspect information without repairs; prompt-visible fields contain no injected gold annotations.

  <!-- Completed 2026-11-12, Codex: inspected the listed checks and observation payloads; PromptInput contains only opaque incident ID and observations. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex, authorized by project owner to accept passing reviews without additional human approval. -->

## crash-05: Required Python module unavailable

File: [crash-05.jsonl](crash-05.jsonl). Split: **test**. Category: **container_crash**. Status: **reviewed and accepted for future generation**.

Gold root cause: The Python worker exited because importing the required module parcel_codec failed with ModuleNotFoundError.

Causal assessment: log-1 shows the import; log-2 identifies ModuleNotFoundError; the successful pull event and exit 1 distinguish import failure from image retrieval failure.

Claim boundaries: The diagnosis does not decide whether dependency packaging, the selected image, or the import path introduced the missing-module error.

Gold supporting excerpts:

- `log-2`: ModuleNotFoundError: No module named 'parcel_codec'

- `termination-1`: Container worker attempt 1 terminated: reason=Error, exitCode=1


Read-only expected checks:

- Inspect the deployed image reference and its dependency manifest for parcel_codec.

- Inspect the worker import path and startup traceback without installing packages or rebuilding the image.


Review checklist:

- [x] Strict schema, evidence references, catalogue split, target identity, and diagnostic timing pass.

  <!-- Completed 2026-11-12, Codex: crash-05 passes tests/test_templates.py and existing JSONL validation; no live cluster execution is claimed. -->

- [x] Gold diagnosis is supported by the cited observations and respects the claim boundaries above.

  <!-- Completed 2026-11-12, Codex: causal assessment and withheld claims for crash-05 recorded above. -->

- [x] Expected checks inspect information without repairs; prompt-visible fields contain no injected gold annotations.

  <!-- Completed 2026-11-12, Codex: inspected the listed checks and observation payloads; PromptInput contains only opaque incident ID and observations. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex, authorized by project owner to accept passing reviews without additional human approval. -->

## crash-06: Native process receives SIGSEGV

File: [crash-06.jsonl](crash-06.jsonl). Split: **test**. Category: **container_crash**. Status: **reviewed and accepted for future generation**.

Gold root cause: The renderer process terminated after receiving SIGSEGV (signal 11); the underlying code defect is not established.

Causal assessment: The supplied process crash diagnostic names SIGSEGV; matching termination details record signal 11 and exit 139 for the same attempt.

Claim boundaries: The record has no stack trace identifying a code defect; neither exit 139 alone nor a guessed library bug is used as the diagnosis.

Gold supporting excerpts:

- `log-1`: Fatal signal 11 (SIGSEGV)

- `termination-1`: Container renderer attempt 1 terminated: reason=Error, exitCode=139


Read-only expected checks:

- Inspect the captured native stack trace or core-dump metadata, if available.

- Compare the deployed binary/library versions with the last working release without changing the deployment.


Review checklist:

- [x] Strict schema, evidence references, catalogue split, target identity, and diagnostic timing pass.

  <!-- Completed 2026-11-12, Codex: crash-06 passes tests/test_templates.py and existing JSONL validation; no live cluster execution is claimed. -->

- [x] Gold diagnosis is supported by the cited observations and respects the claim boundaries above.

  <!-- Completed 2026-11-12, Codex: causal assessment and withheld claims for crash-06 recorded above. -->

- [x] Expected checks inspect information without repairs; prompt-visible fields contain no injected gold annotations.

  <!-- Completed 2026-11-12, Codex: inspected the listed checks and observation payloads; PromptInput contains only opaque incident ID and observations. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex, authorized by project owner to accept passing reviews without additional human approval. -->

## oom-01: Ordinary Job OOM termination

File: [oom-01.jsonl](oom-01.jsonl). Split: **train**. Category: **oom_killed**. Status: **reviewed and accepted for future generation**.

Gold root cause: The selected archiver Job container attempt was terminated with reason OOMKilled; the allocation mechanism and whether its configured limit caused the kill are not established.

Causal assessment: termination-1 directly records OOMKilled for the selected one-shot Job container. No restart loop is required.

Claim boundaries: The configured memory limit is context only. No cgroup or allocation measurements establish a limit breach, cache growth, or leak.

Gold supporting excerpts:

- `termination-1`: Container archiver attempt 1 terminated: reason=OOMKilled, exitCode=137


Read-only expected checks:

- Inspect the selected attempt termination details and time-aligned memory measurements, if available.

- Inspect the Job memory limit and any supplied cgroup or node OOM diagnostics without changing resource settings.


Review checklist:

- [x] Strict schema, evidence references, catalogue split, target identity, and diagnostic timing pass.

  <!-- Completed 2026-11-12, Codex: oom-01 passes tests/test_templates.py and existing JSONL validation; no live cluster execution is claimed. -->

- [x] Gold diagnosis is supported by the cited observations and respects the claim boundaries above.

  <!-- Completed 2026-11-12, Codex: causal assessment and withheld claims for oom-01 recorded above. -->

- [x] Expected checks inspect information without repairs; prompt-visible fields contain no injected gold annotations.

  <!-- Completed 2026-11-12, Codex: inspected the listed checks and observation payloads; PromptInput contains only opaque incident ID and observations. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex, authorized by project owner to accept passing reviews without additional human approval. -->

## oom-02: Cache growth with supplied cgroup evidence

File: [oom-02.jsonl](oom-02.jsonl). Split: **train**. Category: **oom_killed**. Status: **reviewed and accepted for future generation**.

Gold root cause: Growth of the in-memory cache exhausted the container memory allowance and the cache process was OOM-killed.

Causal assessment: Cache growth from 160 to 220 MiB plus 30 MiB other resident memory and a requested 16 MiB increase exceeds the 256 MiB allowance. The same cgroup reaches that limit and its local OOM/kill counters increase, followed by OOMKilled.

Claim boundaries: All measurements are explicitly supplied fictional diagnostics, not automatic LogMind collection. Cache growth is supported; a memory leak is not established.

Gold supporting excerpts:

- `log-1`: cache_bytes=167772160, other_resident_bytes=31457280

- `log-2`: cache_bytes=230686720, other_resident_bytes=31457280; request to grow cache by 16777216 bytes

- `log-3`: memory.max=268435456 memory.peak=268435456; memory.events.local oom increased 0->1 and oom_kill increased 0->1

- `termination-1`: Container cache attempt 1 terminated: reason=OOMKilled, exitCode=137


Read-only expected checks:

- Inspect the supplied cache-size and cgroup memory measurements for the selected attempt.

- Inspect cache bounds, allocation behavior, and the configured memory limit without changing settings.


Review checklist:

- [x] Strict schema, evidence references, catalogue split, target identity, and diagnostic timing pass.

  <!-- Completed 2026-11-12, Codex: oom-02 passes tests/test_templates.py and existing JSONL validation; no live cluster execution is claimed. -->

- [x] Gold diagnosis is supported by the cited observations and respects the claim boundaries above.

  <!-- Completed 2026-11-12, Codex: causal assessment and withheld claims for oom-02 recorded above. -->

- [x] Expected checks inspect information without repairs; prompt-visible fields contain no injected gold annotations.

  <!-- Completed 2026-11-12, Codex: inspected the listed checks and observation payloads; PromptInput contains only opaque incident ID and observations. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex, authorized by project owner to accept passing reviews without additional human approval. -->

## oom-03: Recovered service, selected previous OOM attempt

File: [oom-03.jsonl](oom-03.jsonl). Split: **validation**. Category: **oom_killed**. Status: **reviewed and accepted for future generation**.

Gold root cause: The explicitly selected previous api container attempt was terminated with reason OOMKilled; the current attempt is running and ready.

Causal assessment: metadata-1 selects attempt 2; lastState records its OOMKilled termination. status-1 separately identifies running, ready attempt 3 after that termination.

Claim boundaries: The gold answer does not call the recovered service currently down and does not assert a cause for the historical OOM beyond the termination reason.

Gold supporting excerpts:

- `status-1`: current api attempt 3 started at 2026-10-23T09:00:05Z and is ready

- `termination-1`: Container api attempt 2 terminated: reason=OOMKilled, exitCode=137


Read-only expected checks:

- Inspect memory diagnostics for attempt 2 and its termination time rather than assigning them to the current attempt.

- Inspect resource settings and memory trends without inferring a current outage or changing the running container.


Review checklist:

- [x] Strict schema, evidence references, catalogue split, target identity, and diagnostic timing pass.

  <!-- Completed 2026-11-12, Codex: oom-03 passes tests/test_templates.py and existing JSONL validation; no live cluster execution is claimed. -->

- [x] Gold diagnosis is supported by the cited observations and respects the claim boundaries above.

  <!-- Completed 2026-11-12, Codex: causal assessment and withheld claims for oom-03 recorded above. -->

- [x] Expected checks inspect information without repairs; prompt-visible fields contain no injected gold annotations.

  <!-- Completed 2026-11-12, Codex: inspected the listed checks and observation payloads; PromptInput contains only opaque incident ID and observations. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex, authorized by project owner to accept passing reviews without additional human approval. -->

## oom-04: Memory-backed temporary-file growth

File: [oom-04.jsonl](oom-04.jsonl). Split: **validation**. Category: **oom_killed**. Status: **reviewed and accepted for future generation**.

Gold root cause: Memory-backed temporary-file growth exhausted the exporter container memory allowance and the exporter was OOM-killed.

Causal assessment: The exclusive emptyDir Memory mount and correlated volume/shmem growth from 32 to 100 MiB identify the allocation source. With 20 MiB anonymous memory and a requested 16 MiB write, the 128 MiB allowance is exhausted; local cgroup OOM/kill evidence and OOMKilled agree.

Claim boundaries: Volume and cgroup measurements are supplied diagnostics with timestamps and target identity. No node-pressure eviction, disk-full condition, or memory leak is asserted.

Gold supporting excerpts:

- `metadata-2`: emptyDir with medium=Memory, mounted at /work/tmp

- `log-1`: used_bytes=33554432, cgroup shmem_bytes=33554432

- `log-2`: used_bytes=104857600, cgroup shmem_bytes=104857600, anon_bytes=20971520; next buffered file write=16777216 bytes

- `log-3`: memory.max=134217728 memory.peak=134217728; memory.events.local oom increased 0->1 and oom_kill increased 0->1

- `termination-1`: Container exporter attempt 1 terminated: reason=OOMKilled, exitCode=137


Read-only expected checks:

- Inspect the supplied temporary-volume usage and cgroup shmem measurements for the selected attempt.

- Inspect the temporary-file workload, volume medium, and container limit without deleting files or changing resources.


Review checklist:

- [x] Strict schema, evidence references, catalogue split, target identity, and diagnostic timing pass.

  <!-- Completed 2026-11-12, Codex: oom-04 passes tests/test_templates.py and existing JSONL validation; no live cluster execution is claimed. -->

- [x] Gold diagnosis is supported by the cited observations and respects the claim boundaries above.

  <!-- Completed 2026-11-12, Codex: causal assessment and withheld claims for oom-04 recorded above. -->

- [x] Expected checks inspect information without repairs; prompt-visible fields contain no injected gold annotations.

  <!-- Completed 2026-11-12, Codex: inspected the listed checks and observation payloads; PromptInput contains only opaque incident ID and observations. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex, authorized by project owner to accept passing reviews without additional human approval. -->

## oom-05: Init-container OOM delays application startup

File: [oom-05.jsonl](oom-05.jsonl). Split: **test**. Category: **oom_killed**. Status: **reviewed and accepted for future generation**.

Gold root cause: The latest prepare-index init-container attempt was terminated with reason OOMKilled, leaving the application waiting for initialization.

Causal assessment: The selected init container has an OOMKilled last termination and is awaiting retry; the main api container is separately waiting with PodInitializing and has not started.

Claim boundaries: The kill is not assigned to the main application, and no allocation mechanism or configured-limit breach is inferred from status alone.

Gold supporting excerpts:

- `status-1`: application api is waiting with reason PodInitializing and has not started

- `termination-1`: Container prepare-index attempt 1 terminated: reason=OOMKilled, exitCode=137


Read-only expected checks:

- Inspect initContainerStatuses for prepare-index and the selected attempt timestamps.

- Inspect init-container memory settings and available memory diagnostics without attributing the kill to the application container.


Review checklist:

- [x] Strict schema, evidence references, catalogue split, target identity, and diagnostic timing pass.

  <!-- Completed 2026-11-12, Codex: oom-05 passes tests/test_templates.py and existing JSONL validation; no live cluster execution is claimed. -->

- [x] Gold diagnosis is supported by the cited observations and respects the claim boundaries above.

  <!-- Completed 2026-11-12, Codex: causal assessment and withheld claims for oom-05 recorded above. -->

- [x] Expected checks inspect information without repairs; prompt-visible fields contain no injected gold annotations.

  <!-- Completed 2026-11-12, Codex: inspected the listed checks and observation payloads; PromptInput contains only opaque incident ID and observations. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex, authorized by project owner to accept passing reviews without additional human approval. -->

## oom-06: JVM growth under an oversized heap ceiling

File: [oom-06.jsonl](oom-06.jsonl). Split: **test**. Category: **oom_killed**. Status: **reviewed and accepted for future generation**.

Gold root cause: JVM memory growth exhausted the container memory allowance while the maximum heap was configured above that allowance, and the JVM process was killed by the container cgroup OOM handler.

Causal assessment: The configured 512 MiB heap ceiling exceeds the 256 MiB container allowance. Heap growth from 160 to 220 MiB plus 32 MiB non-heap memory and a requested 16 MiB allocation aligns with the same cgroup reaching its limit, local OOM/kill counter increases, and OOMKilled.

Claim boundaries: The final measured heap alone is below the container limit. The claim concerns total container memory exhaustion, not proof of a heap-only overflow, a Java OutOfMemoryError, or a leak.

Gold supporting excerpts:

- `metadata-2`: maximum heap is 536870912 bytes. Container memory limit is 268435456 bytes

- `log-1`: heap_used_bytes=167772160, nonheap_resident_bytes=33554432

- `log-2`: heap_used_bytes=230686720, nonheap_resident_bytes=33554432; next committed heap allocation=16777216 bytes

- `log-3`: memory.max=268435456 memory.peak=268435456; memory.events.local oom increased 0->1 and oom_kill increased 0->1

- `termination-1`: Container jvm attempt 1 terminated: reason=OOMKilled, exitCode=137


Read-only expected checks:

- Inspect JVM maximum-heap settings alongside the container limit and supplied heap/cgroup measurements.

- Inspect the allocation profile and non-heap overhead without asserting a memory leak or changing runtime flags.


Review checklist:

- [x] Strict schema, evidence references, catalogue split, target identity, and diagnostic timing pass.

  <!-- Completed 2026-11-12, Codex: oom-06 passes tests/test_templates.py and existing JSONL validation; no live cluster execution is claimed. -->

- [x] Gold diagnosis is supported by the cited observations and respects the claim boundaries above.

  <!-- Completed 2026-11-12, Codex: causal assessment and withheld claims for oom-06 recorded above. -->

- [x] Expected checks inspect information without repairs; prompt-visible fields contain no injected gold annotations.

  <!-- Completed 2026-11-12, Codex: inspected the listed checks and observation payloads; PromptInput contains only opaque incident ID and observations. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex, authorized by project owner to accept passing reviews without additional human approval. -->

## Reference semantics

- [Kubernetes container resource management](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)

- [Linux cgroup v2 memory controller](https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html)

- [Kubernetes init containers](https://kubernetes.io/docs/concepts/workloads/pods/init-containers/)
