# LogMind

LogMind is a read-only Kubernetes incident diagnosis project for the MSGAI course. It will turn a supplied snapshot of pod status, events, logs, and workload metadata into a structured diagnosis. The package, strict schemas, JSONL validation, 42 reviewed baseline templates, seeded generation, and the frozen 150-record v1 dataset are implemented. Rules, inference, evaluation, and benchmarking are not implemented yet.

## Setup and commands

Install [uv](https://docs.astral.sh/uv/) and GNU Make, then run these commands from the project root:

```bash
make setup
make check
make validate
make cli
```

Python 3.12 is selected by `.python-version`; exact dependencies are pinned in `uv.lock`. Setup and Python execution targets use `--locked` to reject stale lockfiles. `make setup` runs `uv sync --locked`, including development dependencies. `make build` runs `uv build`, which resolves its isolated build dependencies from `[build-system]` separately from the runtime lockfile. A core-only installation uses `uv sync --locked --no-dev`. Without Make, run the underlying `uv` commands shown in [Makefile](Makefile). `uv run --locked python -m logmind` also exposes the CLI.

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

## Stack and hardware

The core uses Python 3.12, Typer, and Pydantic v2; development checks use pytest and Ruff. Model dependencies will be added separately after a compatibility smoke test. The selected initial model/runtime is Qwen3-1.7B with thinking disabled, using PyTorch and Transformers; exact model/tokenizer revisions remain to be pinned in Phase 0 item 4.

Inspection on 2026-11-12 found WSL2, an Intel i9-13900H (8 logical CPUs exposed), 31 GiB RAM, and an NVIDIA RTX 5060 Laptop GPU with 8 GB VRAM. GPU visibility is confirmed through `nvidia-smi`; PyTorch execution and model memory requirements have not yet been verified. The package uses uv-managed Python 3.12.13 rather than the shell's system Python 3.10.12. The initial MVP needs no live cluster.

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
      tests/
        fixtures/incident.jsonl
        test_schemas.py
        test_jsonl.py
        test_cli.py
        test_generation.py
        test_freezing.py
        test_templates.py

`schemas.py` defines incidents, prompt-visible inputs, predictions, run manifests, and prediction envelopes that retain invalid raw outputs. `Incident.to_prompt_input()` explicitly selects only incident ID and observations. Future prompt builders must consume this input type. Observation text/details must contain only information available at diagnosis time.

The test fixture is a fictional contract example. The [scenario catalogue](data/scenarios/README.md) defines the dataset design, and [template review notes](data/scenarios/templates/README.md) cover all 42 reviewed fictional baselines: six per incident class plus six insufficient-evidence cases, with 14 baselines per split. The [frozen v1 manifest](data/frozen/v1/manifest.json) records the release and its reproduction artifacts; the [seed-42 candidate](data/generated/v1-seed42/manifest.json) remains unchanged. `make test` checks templates, generation, evidence retention, class/split balance, audits, and change detection. No model/rules evaluation has been performed. Future steps will add rules, inference, prompts, evaluation, benchmarking, and configuration modules.

## Boundaries

The tool should never change a cluster or execute repairs. Use fictional names and credentials in synthetic records. Real workplace logs require approval and redaction before use. Synthetic-data scores will not establish production reliability.
