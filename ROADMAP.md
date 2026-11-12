# Implementation roadmap

## Phase 0: runnable baseline

1. **Complete:** Create a small Python package with pinned dependencies and strict input/output schemas. Includes validation CLI, JSONL utilities, prompt-input separation, and focused tests; see README for runnable commands.
2. Implement seeded synthetic scenario generation for all six classes. Review each causal template and preserve scenario IDs through variants and splits.
3. Implement deterministic rules, JSONL output, schema checks, metrics, and a minimal test suite. This proves the pipeline before model downloads.
4. Inspect WSL hardware and select one open small instruction model and a supported local runtime. Pin exact model and tokenizer revisions. Use a fixed zero-shot prompt and decoding settings.
5. Evaluate both baselines on one frozen held-out set and benchmark the model. Publish N, accuracy, macro-F1, validity, reviewed hallucination rate, median/p95 latency, and memory, alongside configuration files.

Done means another person can regenerate the data and rerun both baselines and metrics from documented commands. The rules baseline should work on CPU without a live Kubernetes cluster.

## Phase 1: prompts and context reduction

Compare raw zero-shot input with structured status/events/logs and a selector that retains termination reasons, warnings, errors, and nearby context. Measure evidence retention, input tokens, accuracy, hallucinations, and latency. Use the same model revision and test set.

## Phase 2: LoRA or QLoRA

Train only after Phase 0 works. Train on train scenarios, select on validation, and evaluate once on held-out test. Use the same JSON output schema. Record adapter settings, epochs, batch size, sequence length, seed, checkpoints, hardware, and peak memory. Choose LoRA or QLoRA based on measured VRAM. Near-duplicate synthetic variants may inflate performance, so distinct held-out scenarios are essential.

## Phase 3: quantization and combined system

Compare supported precisions on identical inputs and settings. Measure accuracy, hallucinations, latency, and memory; do not assume 4-bit inference is faster. If runtime changes, report that confound. Combine adaptation, context selection, and quantization only after individual effects are measured.

## Course scope

A CLI and JSONL artifacts are sufficient; a web UI is optional. Controlled fault injection is optional and should run only in an isolated disposable cluster. One model family and a few carefully measured configurations are more realistic than a broad search. Check actual course deadlines and available compute before promising dates or the 300-500-record target.
