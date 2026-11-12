# LogMind

LogMind is a read-only Kubernetes incident diagnosis project for the MSGAI course. It will turn a supplied snapshot of pod status, events, logs, and workload metadata into a structured diagnosis. Phase 0 item 1 is implemented: an installable Python package, strict schemas, JSONL utilities, and validation commands. Scenario generation, rules, inference, evaluation, and benchmarking are not implemented yet.

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
| `make schemas` | Export the five JSON Schema contracts to `schemas/`. |
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

## Stack and hardware

The core uses Python 3.12, Typer, and Pydantic v2; development checks use pytest and Ruff. Model dependencies will be added separately after a compatibility smoke test. The selected initial model/runtime is Qwen3-1.7B with thinking disabled, using PyTorch and Transformers; exact model/tokenizer revisions remain to be pinned in Phase 0 item 4.

Inspection on 2026-11-12 found WSL2, an Intel i9-13900H (8 logical CPUs exposed), 31 GiB RAM, and an NVIDIA RTX 5060 Laptop GPU with 8 GB VRAM. GPU visibility is confirmed through `nvidia-smi`; PyTorch execution and model memory requirements have not yet been verified. The package uses uv-managed Python 3.12.13 rather than the shell's system Python 3.10.12. The initial MVP needs no live cluster.

## Six incident labels

1. container_crash: application exits repeatedly / CrashLoopBackOff;
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
      tests/
        fixtures/incident.jsonl
        test_schemas.py
        test_jsonl.py
        test_cli.py

`schemas.py` defines incidents, prompt-visible inputs, predictions, run manifests, and prediction envelopes that retain invalid raw outputs. `Incident.to_prompt_input()` explicitly selects only incident ID and observations. Future prompt builders must consume this input type. Observation text/details must contain only information available at diagnosis time.

The fixture is a fictional contract example, not a generated or evaluated dataset. Future steps will add generation, rules, inference, prompts, evaluation, benchmarking, and configuration modules, along with `data/` and `experiments/` artifacts.

## Boundaries

The tool should never change a cluster or execute repairs. Use fictional names and credentials in synthetic records. Real workplace logs require approval and redaction before use. Synthetic-data scores will not establish production reliability.
