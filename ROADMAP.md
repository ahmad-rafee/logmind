# Implementation roadmap

Checked items are complete; unchecked items remain open. Each completed item has an HTML comment recording its completion evidence, visible in the Markdown source.

## Phase 0: runnable baseline (complete)

### 1. Package and contracts

- [x] Create an installable Python package using a `src/` layout and Python 3.12.
  <!-- Completed 2026-11-12: pyproject.toml and src/logmind provide CLI/module entry points; wheel and source distribution builds verified. Included in commit ea90ed6. -->
- [x] Pin runtime and development dependencies.
  <!-- Completed 2026-11-12: uv.lock records exact dependency versions; locked setup verified. Included in commit ea90ed6. -->
- [x] Define strict incident, prompt-input, prediction, run-manifest, and prediction-record schemas.
  <!-- Completed 2026-11-12: src/logmind/schemas.py rejects extra fields and incorrect types, separates prompt-visible input, checks evidence references, and preserves invalid raw outputs. Covered by schema tests; included in commit ea90ed6. -->
- [x] Implement UTF-8 JSONL reading/writing and validation commands.
  <!-- Completed 2026-11-12: src/logmind/jsonl.py and cli.py validate records, duplicate IDs, scenario split isolation, and prediction references; fixture validation verified. Included in commit ea90ed6. -->
- [x] Add focused tests for contracts, JSONL utilities, and CLI behavior.
  <!-- Completed 2026-11-12: 30 tests pass; coverage includes invalid types, missing fields, evidence references, prompt-input separation, and split leakage. Included in commit ea90ed6. -->
- [x] Document setup and developer commands in README and Makefile.
  <!-- Completed 2026-11-12: Makefile provides help, setup, checks, formatting, builds, schema export, validation, and CLI help; README documents targets and overrides. Ruff checks, tests, build, export, and fixture validation verified. Included in commit ea90ed6. -->

### 2. Synthetic data generation (complete)

- [x] Draft the causal scenario catalogue, labeling policy, and proposed split/variant counts.
  <!-- Completed 2026-11-12: data/scenarios/README.md defines 36 answerable scenarios, six insufficient-evidence scenarios, proposed split assignments, and a 150-record plan. Human review, executable templates, generation, and frozen artifacts remain pending. -->
- [x] Implement seeded generation for all six incident classes.
  <!-- Completed 2026-11-12: src/logmind/generation.py and logmind generate produce baseline/wording/noisy/long variants from the 42 reviewed templates using local seeded RNGs; make generate provides the documented entry point. tests/test_generation.py verifies byte reproducibility, seed effects, and output protection. -->
- [x] Review and accept the five design policies for split limitations, probes, configuration labels, OOM claims, and diagnostic reason codes.
  <!-- Completed 2026-11-12: project owner accepted these decisions and requested closure; data/scenarios/README.md records each decision with completion evidence. Concrete causal-template review remains open. -->
- [x] Review all 42 baseline templates and record reviewer/method; six scenarios per class and six insufficient-evidence scenarios, with two of each per split.
  <!-- Completed 2026-11-12, Codex under project-owner authorization: all 42 baselines reviewed with bounded diagnoses/information gaps, gold excerpts, read-only checks, and dated per-template acceptance evidence linked in data/scenarios/templates/README.md. No independent human review or live-cluster replay is claimed. -->
- [x] Review crash-01 and create, validate, and review crash-02.
  <!-- Completed 2026-11-12: project owner authorized accepting passing agent reviews; templates/README.md records Codex assessments and completion evidence for both migration-conflict templates. Both are assigned to train; remaining templates and generator are pending. -->
- [x] Create and review crash-03 through crash-06 and all six OOM templates.
  <!-- Completed 2026-11-12, Codex under project-owner authorization: ten fictional records added, with per-template evidence, read-only checks, withheld claims, and completion comments in templates/CRASH_AND_OOM_REVIEW.md. tests/test_templates.py verifies schema, catalogue split, identity/timing, recovery/init attribution, and enriched OOM measurements. -->
- [x] Create and review image-01 through image-06.
  <!-- Completed 2026-11-12, Codex under project-owner authorization: six fictional pull-failure records cover manifest absence, unauthorized access, DNS failure, TLS trust failure, platform mismatch, and rate limiting; templates/IMAGE_PULL_REVIEW.md records causal evidence and completion comments. Authored-template tests verify schema, split, pull identity/timing, platform mismatch evidence, and credential-reference boundaries. -->
- [x] Create and review all six probe, configuration, scheduling, and insufficient-evidence templates.
  <!-- Completed 2026-11-12, Codex under project-owner authorization: 24 baselines added, with individual assessments in PROBE_REVIEW.md, CONFIG_REVIEW.md, SCHEDULING_REVIEW.md, and INSUFFICIENT_EVIDENCE_REVIEW.md. tests/test_templates.py verifies full catalogue coverage, split balance, reference/probe semantics, node exclusions, and preserved information gaps. -->
- [x] Amend the catalogue with migration Job failures and ordinary OOM cases, and create the first concrete baseline template.
  <!-- Completed 2026-11-12: data/scenarios/README.md draft v3 incorporates the agreed amendments; templates/crash-01.jsonl is a fictional duplicate-column migration failure with gold evidence and read-only checks. Existing incident validation passed; human template review and generation remain pending. -->
- [x] Assign baseline splits by scenario_id before variant generation.
  <!-- Completed 2026-11-12: all 42 template IDs match the catalogue; train, validation, and test each contain two baselines for each of seven labels. The full authored-template suite checks assignment and unique incident/scenario IDs. This does not freeze the held-out dataset. -->
- [x] Preserve scenario IDs and split isolation through all generated variants.
  <!-- Completed 2026-11-12: generated records retain baseline scenario_id/split; tests compare all variants with their baselines, enforce a single split per scenario, and verify split JSONL files against the combined dataset. -->
- [x] Generate roughly 120–180 balanced records, including incomplete, noisy, long, and ambiguous cases.
  <!-- Completed 2026-11-12: data/generated/v1-seed42 contains 150 candidate records from 42 scenarios, 50 per split; each answerable class has 24 records plus six incomplete/ambiguous abstention records overall. Manifest records source/template hashes, file checksums, and distinct scenario/variant counts. Dataset is not frozen. -->
- [x] Freeze the held-out set and record dataset checksums and scenario/variant counts.
  <!-- Completed 2026-11-12: audited seed-42 data and froze data/frozen/v1 with 150 records/42 scenarios and 50 records/14 scenarios per split. Frozen manifest preserves candidate hashes/settings and a source/template/dependency bundle; make verify-dataset checks integrity, counts, split membership, and provenance. Reproduction is verified from a writable copy of captured inputs. No rules/model evaluation or test-based tuning has occurred. -->

### 3. Rules baseline and evaluation pipeline (complete)

- [x] Implement deterministic rules that run on CPU without a live cluster.
  <!-- Completed 2026-11-12: src/logmind/rules.py consumes PromptInput only, honors selected attempt/container scope, uses direct diagnostic events/terminations, and abstains for incomplete/conflicting evidence. Tested on train/validation and handcrafted cases; held-out test is not scored. -->
- [x] Save rule predictions as JSONL using the existing schemas and utilities.
  <!-- Completed 2026-11-12: pipeline.py, logmind predict-rules, and make rules save raw PredictionRecord envelopes, valid convenience predictions, revision/data hashes, timings, source copies, metrics, and a blank review worksheet. Existing run directories are protected from overwrite. -->
- [x] Implement accuracy, six-class macro-F1, class support, confusion matrix, validity, and abstention reporting; count invalid predictions as incorrect.
  <!-- Completed 2026-11-12: evaluation.py reparses authoritative raw responses, retains all incidents in denominators, invalidates bad references, rejects duplicate/unknown/mixed-run inputs, and separates ambiguity-group abstentions. logmind evaluate and make evaluate reproduce the validation metrics; reports/rules-v1-validation.json records N=50 and accuracy/macro-F1/validity=1.0. -->
- [x] Implement automatic hallucination flags and document a manual-review rubric and sample selection.
  <!-- Completed 2026-11-12: automatic flags cover nonexistent evidence IDs, explicitly quoted unobserved resource names, and explicit exit/restart numeric contradictions. experiments/REVIEW_PROTOCOL.md preregisters deterministic class/invalid/abstention sampling and factual/recommendation review. Worksheets remain unfilled and reviewed_hallucination_rate is null; actual reviewed measurement remains in Phase 0 step 5. -->
- [x] Add rules and metric tests, including ambiguous and invalid-output cases.
  <!-- Completed 2026-11-12: test_rules.py, test_evaluation.py, and test_pipeline.py cover gold-field independence, selected-attempt filtering, conflict/137 abstention, hand-calculated F1, malformed/schema/reference/missing outputs, authoritative raw responses, review sampling, and validation CLI roundtrips. -->

### 4. Local model baseline (complete)

- [x] Inspect WSL CPU, RAM, and NVIDIA GPU visibility.
  <!-- Completed 2026-11-12: inspection found i9-13900H with 8 logical CPUs exposed, 31 GiB RAM, and RTX 5060 Laptop GPU with 8 GB VRAM via nvidia-smi. Recorded in README; PyTorch execution remains unverified. -->
- [x] Select an initial small instruction model and runtime stack.
  <!-- Completed 2026-11-12: selected Qwen3-1.7B with thinking disabled, using PyTorch and Transformers. Recorded in README; compatibility, memory fit, and exact revisions remain open below. -->
- [x] Verify CUDA execution and model memory fit with a compatibility smoke test; pin model dependencies.
  <!-- Completed 2026-11-12: CUDA BF16 matrix check and two development-case inference smokes passed, including a 4179-token input. PyTorch 2.7.1+cu128 and Transformers 4.57.6 are pinned in the optional model extra/uv.lock. All 50 held-out inferences completed with zero runtime errors; model-smoke.json and phase0/model-test telemetry retain evidence. -->
- [x] Pin exact model and tokenizer revisions.
  <!-- Completed 2026-11-12: both Qwen/Qwen3-1.7B model/tokenizer revisions are 70d244cc86ccca08cf5af4e1e306ecf908b1ad5e in experiments/configs/qwen3-1.7b-zero-shot-v1.json. Downloads use that commit and inference uses cached files with trust_remote_code=false. -->
- [x] Implement a fixed zero-shot prompt and decoding settings, using only prompt-visible inputs.
  <!-- Completed 2026-11-12: prompts.py builds only PromptInput; thinking=false, greedy decoding, BF16/SDPA, seed 42, four threads, 512 generated-token cap, and no input truncation/repair are fixed. experiments/configs/phase0-evaluation-lock.json pins prompt/model/rule/evaluator/benchmark sources before held-out predictions. -->
- [x] Persist raw responses, validation errors, revisions, prompt version, decoding settings, and timing for every model prediction.
  <!-- Completed 2026-11-12: model_pipeline.py stores all 50 raw PredictionRecord envelopes, token/memory/timing telemetry, config/source snapshots, and exact revisions. Five Markdown-fenced JSON outputs remain invalid and incorrect; no repair or substitution was performed. -->

### 5. Frozen evaluation and benchmarking (complete)

- [x] Evaluate rules and model baselines on the same frozen held-out set.
  <!-- Completed 2026-11-12: both runs use frozen v1 test.jsonl checksum 80ee3bf10203c44a11f8afdb61c226d18f47cd30e9e1289b3404b02d97084c86, N=50 across 14 scenarios. Rules accuracy/macro-F1=1.0/1.0; Qwen accuracy/macro-F1=0.5/0.4820987654 with 90% validity. Archived raw runs and reviewed summaries are in experiments/reports/phase0. No test-driven changes to the locked sources were made. -->
- [x] Benchmark a fixed subset with warm-up, separate cold/warm measurements, and at least three repetitions per configuration.
  <!-- Completed 2026-11-12: both backends ran the same seven hash-selected test inputs three times per case/mode, yielding 21 cold and 21 warm measurements per backend. Cold uses a fresh process/model per case; warm discards an explicit warm-up. Every measured raw response and input is archived in experiments/reports/phase0/benchmark. OS caches were not flushed. -->
- [x] Record end-to-end median/p95 latency, token counts, throughput, CPU peak RSS, and GPU memory.
  <!-- Completed 2026-11-12: model cold median/p95=19.005/23.188s and warm=10.144/12.776s; rules cold=0.125268/0.135431s and warm=0.000290/0.000375s. Benchmark summary records sampled/lifetime RSS, CUDA allocated/reserved peaks, token counts/throughput, and environment. The report distinguishes the seven short/non-long inputs from the full-test maximum context/memory. -->
- [x] Review the preregistered hallucination sample and publish the numerator, denominator, and reviewer rubric.
  <!-- Completed 2026-11-12: preregistered sample selection yielded 14 records per backend, including invalid/abstained outputs when present. Case-by-case Codex agent review reports unsupported factual claims in 0/14 rules and 9/14 model outputs, with support/relevance/safety ratings and examples. review.py validates unchanged sample facts and complete ratings. This is single-agent review, not independent human review or a production-rate estimate. -->
- [x] Publish N, accuracy, macro-F1, validity, hallucination rate, latency, and memory alongside configurations and environment metadata.
  <!-- Completed 2026-11-12: experiments/PHASE0_REPORT.md and reports/phase0/phase0-summary.json publish all measured results and limits; raw runs, per-class supports/confusions, exact settings/source/dependency pins, hardware, and reviewed numerators/denominators are retained. Reviewed rate is explicitly single-agent assessment, not independent human review or a production estimate. -->
- [x] Verify that another person can regenerate data and rerun both baselines and metrics from documented commands.
  <!-- Completed 2026-11-12: experiments/PHASE0_REPRODUCE.md documents the complete workflow. From a writable copy of reports/phase0/reproduction, a fresh core-only environment regenerated data/manifest byte-for-byte, verified the frozen pin, reproduced rules test accuracy 1.0, and recomputed model metrics accuracy 0.5. Installing the optional pinned runtime then completed GPU inference from the captured source/config without errors. reproduction-check.json and reproduced-model-smoke.json retain evidence; full original GPU runs/benchmarks are archived. -->

Done means another person can regenerate the data and rerun both baselines and metrics from documented commands. The rules baseline should work on CPU without a live Kubernetes cluster.

## Phase 1: prompts and context reduction

- [ ] Compare raw zero-shot input with structured status/events/logs.
- [ ] Implement a context selector retaining termination reasons, warnings, errors, and nearby context.
- [ ] Measure evidence retention, input tokens, accuracy, hallucinations, and latency on the same model revision and test set.

## Phase 2: LoRA or QLoRA

- [ ] Complete Phase 0 before training and choose LoRA or QLoRA based on measured VRAM.
- [ ] Train on train scenarios, select on validation, and evaluate once on held-out test using the same JSON output schema.
- [ ] Record adapter settings, epochs, batch size, sequence length, seed, checkpoints, hardware, and peak memory.
- [ ] Assess results with distinct held-out scenarios; account for inflation from near-duplicate synthetic variants.

## Phase 3: quantization and combined system

- [ ] Compare supported precisions on identical inputs and settings.
- [ ] Measure accuracy, hallucinations, latency, and memory; do not assume 4-bit inference is faster.
- [ ] Report any runtime change as a confound.
- [ ] Combine adaptation, context selection, and quantization only after individual effects are measured.

## Course scope

A CLI and JSONL artifacts are sufficient; a web UI is optional. Controlled fault injection is optional and should run only in an isolated disposable cluster. One model family and a few carefully measured configurations are more realistic than a broad search. Check actual course deadlines and available compute before promising dates or the 300-500-record target.
