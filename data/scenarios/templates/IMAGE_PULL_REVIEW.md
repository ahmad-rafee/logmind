# Image-pull template reviews

Reviewer: **Codex**. Date: **2026-11-12**. All six templates are **reviewed and accepted for future generation**, under the project owner's authorization to accept passing reviews without further human approval. This is agent review, not independent human review or live-cluster/registry verification.

These fixed baseline records are fictional. All registry hostnames use example.invalid; no real registry, credential value, production resource name, or raw production log is included. They do not implement variant generation or freeze a dataset.

Each record targets a node-side image-pull attempt. Pod scheduling succeeded, but the application container never started: no process termination or application logs are invented. Pulling, Failed, and BackOff events have consistent image/target identity and ordered timestamps; ImagePullBackOff is the resulting symptom, not the detailed cause.

Validation: `uv run --locked pytest tests/test_templates.py`; individual files also work with `make validate INCIDENTS=data/scenarios/templates/image-01.jsonl` (substitute the filename). Schema checks validate every gold excerpt against an existing observation. Focused image checks cover pull identity/timing, no process execution, direct error evidence, node/index mismatch, and credential references without payloads.

## image-01: Referenced tag manifest unavailable

File: [image-01.jsonl](image-01.jsonl). Split: **train**. Category: **image_pull_failure**.

Gold root cause: The registry reported that the manifest for the referenced dispatch-ui:release-unknown tag was not found, preventing the image pull.

Causal assessment: The Failed event names the requested image/tag and reports manifest unknown for that tag; the selected container has not started and is in ImagePullBackOff.

Claim boundaries: The record establishes the registry response for this request, not why the manifest is missing, whether it once existed, or who published the image.

Gold supporting excerpts:

- `event-2`: manifest unknown: manifest tagged release-unknown is not found

- `status-1`: state.waiting.reason=ImagePullBackOff, started=false, restartCount=0


Read-only expected checks:

- Inspect the exact image repository and tag in the workload specification.

- Inspect the registry tag inventory and build publication records for that repository without pushing images or changing the deployment.


Review checklist:

- [x] Strict schema, evidence references, catalogue assignment, and target/pull chronology pass.

  <!-- Completed 2026-11-12, Codex: image-01 passes authored-template validation and focused image-pull checks in tests/test_templates.py. -->

- [x] The diagnosis uses direct pull evidence and does not invent a process crash or a deeper unsupported cause.

  <!-- Completed 2026-11-12, Codex: image-01 causal assessment and claim boundaries are recorded above. -->

- [x] Recommended checks inspect evidence without repairs; observations preserve authentic diagnostics and omit credentials and gold annotations.

  <!-- Completed 2026-11-12, Codex: inspected the listed actions and raw observations; PromptInput includes only opaque incident ID and observations. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex; accepted under project-owner authorization for passing agent reviews. -->

## image-02: Private-registry pull unauthorized

File: [image-02.jsonl](image-02.jsonl). Split: **train**. Category: **image_pull_failure**.

Gold root cause: The private registry rejected the inventory-api image pull as unauthorized, so the container could not start.

Causal assessment: The current pull fails with explicit 401/UNAUTHORIZED authentication-required evidence. Supplied metadata identifies a private repository and a credential reference without including its values.

Claim boundaries: An existing credential object does not prove credentials are valid or sufficient. Do not assert an incorrect password, expired token, missing Secret, or specific permissions defect. Authentication/pull-access failure belongs to image_pull_failure here.

Gold supporting excerpts:

- `event-2`: 401 Unauthorized: UNAUTHORIZED: authentication required for repository private/inventory-api

- `status-1`: state.waiting.reason=ImagePullBackOff, started=false, restartCount=0


Read-only expected checks:

- Inspect the workload and ServiceAccount imagePullSecrets references and credential-object presence/type without displaying credential values.

- Inspect the registry authentication/authorization failure records and required repository access scope without changing credentials.


Review checklist:

- [x] Strict schema, evidence references, catalogue assignment, and target/pull chronology pass.

  <!-- Completed 2026-11-12, Codex: image-02 passes authored-template validation and focused image-pull checks in tests/test_templates.py. -->

- [x] The diagnosis uses direct pull evidence and does not invent a process crash or a deeper unsupported cause.

  <!-- Completed 2026-11-12, Codex: image-02 causal assessment and claim boundaries are recorded above. -->

- [x] Recommended checks inspect evidence without repairs; observations preserve authentic diagnostics and omit credentials and gold annotations.

  <!-- Completed 2026-11-12, Codex: inspected the listed actions and raw observations; PromptInput includes only opaque incident ID and observations. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex; accepted under project-owner authorization for passing agent reviews. -->

## image-03: Registry hostname resolution fails

File: [image-03.jsonl](image-03.jsonl). Split: **validation**. Category: **image_pull_failure**.

Gold root cause: The node could not resolve the registry hostname registry.example.invalid during the portal-ui image pull.

Causal assessment: The current node-side pull reports lookup of the exact registry hostname returning no such host. Scheduled status distinguishes this from failure to place the pod.

Claim boundaries: The evidence does not diagnose CoreDNS, a node resolver defect, network policy, or a misspelled hostname. The resolver address is a fictional documentation-range address.

Gold supporting excerpts:

- `event-2`: dial tcp: lookup registry.example.invalid on 192.0.2.53:53: no such host

- `status-1`: state.waiting.reason=ImagePullBackOff, started=false, restartCount=0


Read-only expected checks:

- Inspect the supplied node resolver configuration and DNS diagnostic records for registry.example.invalid.

- Inspect the configured registry hostname for spelling and expected DNS records without modifying DNS or restarting services.


Review checklist:

- [x] Strict schema, evidence references, catalogue assignment, and target/pull chronology pass.

  <!-- Completed 2026-11-12, Codex: image-03 passes authored-template validation and focused image-pull checks in tests/test_templates.py. -->

- [x] The diagnosis uses direct pull evidence and does not invent a process crash or a deeper unsupported cause.

  <!-- Completed 2026-11-12, Codex: image-03 causal assessment and claim boundaries are recorded above. -->

- [x] Recommended checks inspect evidence without repairs; observations preserve authentic diagnostics and omit credentials and gold annotations.

  <!-- Completed 2026-11-12, Codex: inspected the listed actions and raw observations; PromptInput includes only opaque incident ID and observations. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex; accepted under project-owner authorization for passing agent reviews. -->

## image-04: Registry certificate cannot be verified

File: [image-04.jsonl](image-04.jsonl). Split: **validation**. Category: **image_pull_failure**.

Gold root cause: The node rejected the registry TLS certificate during the labels-api image pull because its issuer was not trusted.

Causal assessment: The Failed pull event reports x509 certificate signed by unknown authority for the selected image. The container remains waiting and has not started.

Claim boundaries: Do not infer an expired certificate, a hostname mismatch, or a specific missing CA. Checks inspect certificate/trust evidence without disabling verification or changing trust settings.

Gold supporting excerpts:

- `event-2`: tls: failed to verify certificate: x509: certificate signed by unknown authority

- `status-1`: state.waiting.reason=ImagePullBackOff, started=false, restartCount=0


Read-only expected checks:

- Inspect the registry certificate chain and the node container-runtime trust configuration.

- Inspect the configured registry hostname and supplied TLS diagnostics without disabling certificate verification or modifying trust settings.


Review checklist:

- [x] Strict schema, evidence references, catalogue assignment, and target/pull chronology pass.

  <!-- Completed 2026-11-12, Codex: image-04 passes authored-template validation and focused image-pull checks in tests/test_templates.py. -->

- [x] The diagnosis uses direct pull evidence and does not invent a process crash or a deeper unsupported cause.

  <!-- Completed 2026-11-12, Codex: image-04 causal assessment and claim boundaries are recorded above. -->

- [x] Recommended checks inspect evidence without repairs; observations preserve authentic diagnostics and omit credentials and gold annotations.

  <!-- Completed 2026-11-12, Codex: inspected the listed actions and raw observations; PromptInput includes only opaque incident ID and observations. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex; accepted under project-owner authorization for passing agent reviews. -->

## image-05: No manifest for the selected node platform

File: [image-05.jsonl](image-05.jsonl). Split: **test**. Category: **image_pull_failure**.

Gold root cause: The referenced image index has no linux/arm64 manifest for the selected node, preventing the image pull.

Causal assessment: The pull error explicitly names linux/arm64; supplied node status reports linux/arm64 and the supplied image index lists linux/amd64 only. These observations support the platform-mismatch diagnosis.

Claim boundaries: The image exists for another platform; do not label the repository absent or the image corrupt. The index snapshot is supplied synthetic diagnostic evidence, not a registry query executed by LogMind.

Gold supporting excerpts:

- `event-2`: no match for platform linux/arm64 in manifest: not found

- `status-1`: state.waiting.reason=ImagePullBackOff, started=false, restartCount=0

- `metadata-2`: operatingSystem=linux, architecture=arm64

- `metadata-3`: available platform linux/amd64 only; no other platform descriptors


Read-only expected checks:

- Inspect the selected node operating system and architecture alongside the image index platforms.

- Inspect the build publication metadata for the referenced tag without rebuilding, publishing, or rescheduling workloads.


Review checklist:

- [x] Strict schema, evidence references, catalogue assignment, and target/pull chronology pass.

  <!-- Completed 2026-11-12, Codex: image-05 passes authored-template validation and focused image-pull checks in tests/test_templates.py. -->

- [x] The diagnosis uses direct pull evidence and does not invent a process crash or a deeper unsupported cause.

  <!-- Completed 2026-11-12, Codex: image-05 causal assessment and claim boundaries are recorded above. -->

- [x] Recommended checks inspect evidence without repairs; observations preserve authentic diagnostics and omit credentials and gold annotations.

  <!-- Completed 2026-11-12, Codex: inspected the listed actions and raw observations; PromptInput includes only opaque incident ID and observations. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex; accepted under project-owner authorization for passing agent reviews. -->

## image-06: Registry pull-rate limit exceeded

File: [image-06.jsonl](image-06.jsonl). Split: **test**. Category: **image_pull_failure**.

Gold root cause: The registry rejected the tracking-api image pull with HTTP 429 because its pull rate limit was exceeded.

Causal assessment: The current pull response explicitly combines HTTP 429, TOOMANYREQUESTS, pull rate limit exceeded, and Retry-After. Status shows waiting rather than an application crash.

Claim boundaries: The quota scope, which client consumed it, and whether credentials would change the quota are unknown. Inspect quota/pull history rather than force retries or promise that a retry will succeed.

Gold supporting excerpts:

- `event-2`: 429 Too Many Requests: TOOMANYREQUESTS: pull rate limit exceeded; Retry-After: 120

- `status-1`: state.waiting.reason=ImagePullBackOff, started=false, restartCount=0


Read-only expected checks:

- Inspect the supplied registry rate-limit response, Retry-After value, and applicable pull quota.

- Inspect recent image-pull volume and registry access policy without forcing retries or changing the deployment.


Review checklist:

- [x] Strict schema, evidence references, catalogue assignment, and target/pull chronology pass.

  <!-- Completed 2026-11-12, Codex: image-06 passes authored-template validation and focused image-pull checks in tests/test_templates.py. -->

- [x] The diagnosis uses direct pull evidence and does not invent a process crash or a deeper unsupported cause.

  <!-- Completed 2026-11-12, Codex: image-06 causal assessment and claim boundaries are recorded above. -->

- [x] Recommended checks inspect evidence without repairs; observations preserve authentic diagnostics and omit credentials and gold annotations.

  <!-- Completed 2026-11-12, Codex: inspected the listed actions and raw observations; PromptInput includes only opaque incident ID and observations. -->

- [x] Record reviewer, date, and acceptance basis.

  <!-- Completed 2026-11-12: reviewer Codex; accepted under project-owner authorization for passing agent reviews. -->

## Technical references

- [Kubernetes image pulling](https://kubernetes.io/docs/concepts/containers/images/)

- [CNCF Distribution registry HTTP API](https://distribution.github.io/distribution/spec/api/) (manifest errors, authorization failures, and rate limiting)
