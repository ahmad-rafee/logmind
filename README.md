# LogMind

LogMind is a read-only Kubernetes incident diagnosis project for the MSGAI course, motivated by ZadAlkhier operations. **Phase 0 is complete:** frozen synthetic data, CPU rules, a pinned local instruction-model baseline, strict prediction artifacts, held-out evaluation, reviewed factual support, and repeated cold/warm latency/memory benchmarks. On 50 held-out synthetic cases, rules achieved 100% accuracy and Qwen3-1.7B 50%. See the [Phase 0 report](experiments/PHASE0_REPORT.md) for results, evidence, and limitations.

Read [Algorithm and code flow](CODE_FLOW.md) for the diagnosis logic, module responsibilities, and end-to-end execution path.

## Setup and commands

Install [uv](https://docs.astral.sh/uv/) and GNU Make, then run these commands from the project root:

```bash
make setup
make check
make validate
make cli
```

Python 3.12.13 is selected by `.python-version`; exact dependencies are pinned in `uv.lock`. Setup and Python execution targets use `--locked` to reject stale lockfiles. `make setup` runs `uv sync --locked`, including development dependencies. `make build` runs `uv build`, which resolves its isolated build dependencies from `[build-system]` separately from the runtime lockfile. A core-only installation uses `uv sync --locked --no-dev`. Without Make, run the underlying `uv` commands shown in [Makefile](Makefile). `uv run --locked python -m logmind` also exposes the CLI.

### Makefile reference

Run `make` or `make help` for the command list. Checks return a nonzero exit code on failure.

| Target | Purpose |
| --- | --- |
| `make setup` | Install locked runtime and development dependencies. |
| `make check` | Run lint, formatting verification, and all tests. |
| `make test` | Run pytest. |
| `make lint` | Run Ruff lint checks. |
| `make format` | Apply Ruff formatting to source and tests. |
| `make format-check` | Check formatting without modifying files. |
| `make build` | Build wheel and source distribution in `dist/`. |
| `make schemas` | Export seven JSON Schema contracts, including candidate/frozen manifests, to `schemas/`. |
| `make generate` | Generate the 150-record candidate dataset and manifest using seed 42. |
| `make freeze` | Audit the candidate and create a frozen version with reproduction inputs. |
| `make verify-dataset` | Verify the frozen data, split membership, provenance, and checksums. |
| `make rules` | Run rules on frozen validation data and save predictions, raw records, metrics, and review sample. |
| `make evaluate` | Recompute metrics from the run's authoritative records.jsonl. |
| `make model-setup` | Install the pinned optional CUDA model runtime. |
| `make download-model` | Download immutable model/tokenizer revisions into the local cache. |
| `make model` | Run the fixed zero-shot model on frozen test data; override MODEL_RUN_DIR for reruns. |
| `make phase0-benchmark` | Repeat matched cold/warm measurements for both backends; override BENCHMARK_DIR for reruns. |
| `make validate` | Validate the example incident fixture or the supplied `INCIDENTS` file. |
| `make validate-predictions` | Validate `PREDICTIONS` against `INCIDENTS`. |
| `make cli` | Show CLI commands and usage. |

Override `INCIDENTS`, `PREDICTIONS`, and `SCHEMA_DIR` with paths appropriate to your run; `UV` overrides the uv executable. `PREDICTIONS` has no default, so its validation target requires a path. These commands operate on paths relative to the project root. For example:

```bash
make validate INCIDENTS=data/generated/incidents.jsonl
make schemas SCHEMA_DIR=dist/schemas
```

To check a prediction JSONL file against an incident dataset:

```bash
make validate-predictions PREDICTIONS=predictions.jsonl INCIDENTS=incidents.jsonl
```

Validation rejects extra fields, incorrect types, blank records, duplicate IDs, invalid evidence references, and scenario IDs shared across splits. Prediction validation reports coverage and permits a subset of incidents; it does not calculate metrics or require complete evaluation coverage. Commands exit nonzero on validation failure.

### Seeded data generation

```bash
make generate
make validate INCIDENTS=data/generated/v1-seed42/incidents.jsonl
make generate SEED=43 DATA_DIR=data/generated/v1-seed43
# Equivalent CLI:
uv run --locked logmind generate --seed 42 --output data/generated/v1-seed42
```

`SEED` defaults to 42; `DATA_DIR` defaults to `data/generated/v1-seed$(SEED)` and `TEMPLATES` to `data/scenarios/templates`. The CLI also derives its default output directory from the chosen seed. Run commands from the repository root so the default template path resolves. A packaged installation needs a local checkout of the template files or an explicit `--templates` path.

The generator requires all 42 baseline files with their reviewed scenario/category/split assignments. It produces `incidents.jsonl` (150 records), `train.jsonl`, `validation.jsonl`, and `test.jsonl` (50 each), plus a strict `manifest.json` with the seed, generator/source and template hashes, file SHA-256 checksums, and separate record/scenario counts. Outputs are **candidates, not a frozen test set**. Identical reruns are accepted without changing files; different contents at the output path cause an error instead of an overwrite.

Answerable scenarios produce baseline, wording, noisy, and long variants. Wording changes only allowlisted snapshot framing; reason codes, raw events/logs, structured facts, names, timestamps, and numerical evidence stay intact. Gold excerpts follow those wording changes and are revalidated. Noisy variants add 2–4 benign supplied workload notes; long variants add 32. Original observations are retained, with seeded ordering to vary evidence position. These are metadata notes, not invented application logs for containers that never started. The six abstention scenarios remain baseline-only with their information gaps preserved.

Reproducibility uses local per-scenario random generators, stable input/output ordering, and opaque seed-derived incident IDs. Reuse Python 3.12, `uv.lock`, identical template bytes, and the recorded generator source for matching artifacts. These conservative variants have limited linguistic diversity and are not new independent causal scenarios. See [candidate dataset notes](data/generated/README.md).

### Frozen dataset v1

Use `data/frozen/v1/train.jsonl` for training/rule development, `validation.jsonl` for selection, and `test.jsonl` only for held-out evaluation. Each contains 50 records across 14 scenarios; combined there are 150 records across 42 scenarios. No baseline has been evaluated yet. Do not tune rules, prompts, or thresholds on test labels or outputs.

```bash
make verify-dataset
# Creation audits the candidate before freezing; identical existing v1 is reused:
make freeze
# Equivalent verification CLI:
uv run --locked logmind verify-dataset data/frozen/v1
```

`DATA_DIR` selects the candidate; `FROZEN_DIR` defaults to `data/frozen/v1` and `DATASET_VERSION` to `v1`. A differing existing release is never overwritten. Frozen JSONL bytes match the candidate, whose manifest is preserved as `candidate-manifest.json`. The frozen manifest records audit checks, seed/counts/checksums, runtime versions, and hashes of every reproduction artifact. Verification checks the recorded manifest hash; `--expected-sha256` accepts an additional externally recorded pin. Checksums detect changes relative to that pin; they are not digital signatures or filesystem write protection.

The `reproduction/` bundle preserves baseline JSONL files, Python source, package metadata, Python version selection, `uv.lock`, README, and Makefile. Copy it to a writable temporary directory before running it so installation/bytecode files do not alter the sealed artifact inventory. See [frozen dataset instructions](data/frozen/README.md) for regeneration and the manifest pin. Ruff excludes `data/frozen` to avoid rewriting captured source during formatting. Later dataset changes require a new version and checksums.

### Rules baseline and evaluation

```bash
make rules
make evaluate
# Change the directory for additional runs; prior artifacts are preserved:
make rules RUN_DIR=experiments/runs/another-validation-run
```

The default is frozen validation (`RULE_SPLIT=validation`); train can be selected with `RULE_SPLIT=train`. Output defaults to `experiments/runs/rules-v1-$(RULE_SPLIT)` and existing runs are not overwritten. `make evaluate` writes a separate `metrics-recomputed.json`; override `EVALUATION_REPORT` for additional evaluations. Held-out test evaluation requires an explicit test split selection and should happen only once rules/settings are fixed.

Rules consume only observations and use explicit event/termination evidence, matched application-error exits, and supplied target selection; missing or conflicting evidence produces insufficient_evidence. Run metadata pins the rules source by SHA-256 and records the exact frozen split checksum. All recommended checks are read-only. Authoritative `records.jsonl` retains raw responses, strict parse/schema/reference errors, and per-incident timing. The valid-only `predictions.jsonl` is a convenience export, not the evaluation denominator.

Metrics include full-N accuracy, answerable accuracy, six-class macro-F1, class support/confusion matrix, parse/schema/reference validity, and abstention behavior by ambiguity group. Invalid/missing outputs count as incorrect. The metrics use explicit standard-library formulas without adding GPU or scientific-library dependencies to the CPU core. Automatic flags identify a narrow subset of unknown references, named resources, and numeric contradictions; reviewed_hallucination_rate remains null until the review worksheet is completed.

The first [validation report](experiments/reports/rules-v1-validation.json) has N=50 across 14 scenarios, accuracy=1.0, macro-F1=1.0, and valid-output rate=1.0. The completed [held-out comparison](experiments/PHASE0_REPORT.md) reports rules accuracy/macro-F1=1.0/1.0 and model=0.5/0.4821, with 90% model validity and no runtime errors. Single-agent review found unsupported factual claims in 0/14 rules and 9/14 model sampled outputs; this is not independent human review or a production rate. Raw evidence, metrics, and environment/configuration metadata are archived. See [reproduction commands](experiments/PHASE0_REPRODUCE.md) and the [review rubric](experiments/REVIEW_PROTOCOL.md).

### Local model and benchmarks

```bash
make model-setup
make download-model
make model MODEL_RUN_DIR=experiments/runs/reproduced-model-test
make phase0-benchmark BENCHMARK_DIR=experiments/runs/reproduced-benchmark
```

The fixed configuration is `experiments/configs/qwen3-1.7b-zero-shot-v1.json`: Qwen3-1.7B and tokenizer commit 70d244cc86ccca08cf5af4e1e306ecf908b1ad5e, BF16 CUDA/SDPA, four CPU threads, seed 42, greedy generation, thinking disabled, 512 output-token cap, no repair/truncation. PyTorch 2.7.1+cu128 and Transformers 4.57.6 are pinned in the optional model extra and uv.lock. Core CPU setup does not install them. Inference uses cached immutable files without remote code execution; weights are not stored in the repository.

Benchmarks use seven score-independent hash-selected inputs, three repetitions, fresh processes for each cold measurement, and an explicit discarded warm-up before warmed repetitions. Model warm median/p95 latency was 10.14/12.78 seconds; rules 0.29/0.38 milliseconds. The subset contains no long variant; the report separately records full-test token/memory maxima and shared-GPU limitations. Review summaries can be recomputed with `logmind review-summary SAMPLE COMPLETED --output NEW_JSON`; it validates sample completeness and unchanged original facts/outputs.

## Stack and hardware

The core uses Python 3.12, Typer, and Pydantic v2; development checks use pytest and Ruff. The optional model runtime uses pinned PyTorch/Transformers, with psutil for RSS measurements. Exact model/tokenizer revisions, prompt/source hashes, dependencies, and benchmark settings are retained in the [Phase 0 evidence archive](experiments/reports/phase0/).

Inspection on 2026-11-12 found WSL2, an Intel i9-13900H (8 logical CPUs exposed), 31 GiB RAM, and an NVIDIA RTX 5060 Laptop GPU with 8 GB VRAM. CUDA BF16 execution, model fit, and repeated inference are verified; the full model test peaked at 3.859 GiB allocated / 4.148 GiB reserved GPU memory. The package uses uv-managed Python 3.12.13 rather than system Python 3.10.12. Benchmarks ran on the shared laptop GPU; no live cluster is needed.

## Six incident labels

1. container_crash: unsuccessful application/process exit, including failed migration Jobs; repeated restarts are not required;
2. oom_killed: container terminated after exceeding memory;
3. image_pull_failure: invalid image, missing registry access, or pull authentication;
4. probe_failure: failing readiness or liveness probe;
5. missing_config: missing ConfigMap or Secret;
6. scheduling_failure: insufficient resources or unsatisfied placement constraints.

Classify the primary cause, not just a secondary status. Allow insufficient_evidence when inputs do not justify a firm cause.

## First implementation milestone

Build a command-line, reproducible baseline before training. A deterministic rules baseline will check the data and evaluation pipeline. Then an unmodified small instruction model will produce JSON using a fixed zero-shot prompt. These are separate baselines; rules are not presented as a language model. Both run on the same frozen held-out incidents.

The implementation should create a versioned synthetic/controlled dataset, schema validation, JSONL prediction files, root-cause accuracy and macro-F1, hallucination review, and latency/memory measurements. The proposal suggests a Qwen instruction model around 1.5B-3B parameters, but the exact model and runtime should be chosen after hardware inspection and pinned by revision.

## Package layout

    logmind/
      README.md
      DATA_AND_EVALUATION.md
      ROADMAP.md
      pyproject.toml
      Makefile
      uv.lock
      .python-version
      src/logmind/
        __init__.py
        __main__.py
        cli.py
        schemas.py
        jsonl.py
        generation.py
        freezing.py
        rules.py
        evaluation.py
        pipeline.py
      tests/
        fixtures/incident.jsonl
        test_schemas.py
        test_jsonl.py
        test_cli.py
        test_generation.py
        test_freezing.py
        test_rules.py
        test_evaluation.py
        test_pipeline.py
        test_templates.py

`schemas.py` defines incidents, prompt-visible inputs, predictions, run manifests, and prediction envelopes that retain invalid raw outputs. `Incident.to_prompt_input()` explicitly selects only incident ID and observations. Future prompt builders must consume this input type. Observation text/details must contain only information available at diagnosis time.

The [scenario catalogue](data/scenarios/README.md) and [template reviews](data/scenarios/templates/README.md) cover all 42 fictional baselines. The [frozen v1 manifest](data/frozen/v1/manifest.json) and candidate bytes remain unchanged. Tests cover data integrity/generation, rules, metrics, model prompt/config boundaries, invalid-output preservation, review validation, and archived evidence. The next roadmap phase is validation-selected prompt/context experiments, keeping the Phase 0 results fixed.

## Boundaries

The tool should never change a cluster or execute repairs. Use fictional names and credentials in synthetic records. Real workplace logs require approval and redaction before use. Synthetic-data scores will not establish production reliability.
