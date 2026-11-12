# Reproduce Phase 0

Use a checkout containing the frozen v1 artifacts and uv.lock. The CPU rules baseline needs no cluster or model dependencies. The model configuration uses an NVIDIA CUDA GPU and the optional model extra; the measured machine/configuration and memory requirements are recorded in the Phase 0 report.

## Data and CPU rules

```bash
make setup
make verify-dataset
make generate DATA_DIR=/tmp/logmind-regenerated-seed42
make rules RULE_SPLIT=test RUN_DIR=experiments/runs/reproduced-rules-test
make evaluate RULE_SPLIT=test RUN_DIR=experiments/runs/reproduced-rules-test
```

Compare regenerated JSONL checksums with data/frozen/v1/candidate-manifest.json. The original frozen source/dependency/template bundle remains available for reproducing generator v1 independently of later project changes; see data/frozen/README.md. Do not edit the frozen snapshot or select settings based on held-out performance.

## Local instruction-model baseline

```bash
make model-setup
make download-model
make model MODEL_RUN_DIR=experiments/runs/reproduced-qwen-test
uv run --locked --extra model logmind evaluate data/frozen/v1/test.jsonl experiments/runs/reproduced-qwen-test/records.jsonl --output experiments/runs/reproduced-qwen-test/metrics-recomputed.json
```

The model extra pins PyTorch 2.7.1+cu128 and Transformers 4.57.6, with all transitive versions in uv.lock. The model and tokenizer both use Qwen/Qwen3-1.7B commit 70d244cc86ccca08cf5af4e1e306ecf908b1ad5e. Downloads enter the normal Hugging Face cache; inference uses local cached files and trust_remote_code=false. CPU setup remains separate from the CUDA libraries.

The config at experiments/configs/qwen3-1.7b-zero-shot-v1.json fixes BF16, CUDA, SDPA, four CPU threads, seed 42, greedy generation, 512 maximum generated tokens, and a 16,384-token input ceiling. The runtime never truncates inputs or repairs outputs: inference failures and invalid outputs remain incorrect in the full denominator. Raw responses, input/output token counts, timings, memory measurements, source snapshots, config, and exact model/tokenizer/prompt revisions are retained.

prompts.py supplies a fixed zero-shot instruction and the entire PromptInput JSON. It exposes no ground-truth category/root cause/evidence/action fields. Thinking is disabled in the tokenizer chat template. No training, few-shot examples, selector, or quantization is used. Rule/model/prompt/evaluator/benchmark source hashes were fixed in experiments/configs/phase0-evaluation-lock.json before held-out predictions; results were not used to tune them.

## Matched benchmark

```bash
make phase0-benchmark BENCHMARK_DIR=experiments/runs/reproduced-phase0-benchmark
```

Both backends receive the same seven held-out incidents: one per category, selected by minimum SHA-256 of `42:<incident_id>`, independent of prediction quality. Three repetitions are measured per input/configuration. Cold measurements start a fresh Python process/model for every case/repetition, including imports/load/first prediction from worker entry; interpreter startup and OS file-cache flushing are not included. Warm measurements use a single loaded process, one explicit discarded warm-up, then three complete repetitions. Backends execute sequentially.

The benchmark saves every raw measured output and telemetry, not just aggregates. Median and p95 end-to-end latency include prompt assembly, inference, and parsing; p95 uses linear interpolation. Cold RSS uses process-lifetime peak; warm RSS is sampled every 10ms. PyTorch measures peak allocated/reserved GPU memory. Model token throughput is generated IDs divided by measured end-to-end seconds, including cold initialization for cold measurements; rules have no tokenizer/throughput value. GPU/OS caches and host activity can affect measurements on the shared laptop GPU.

## Review and integrity

Original preregistered worksheets, completed case-by-case ratings, and validated summaries are retained in experiments/reports/phase0. Recompute a published review summary with:

```bash
uv run --locked logmind review-summary experiments/reports/phase0/rules-review-sample.jsonl experiments/reports/phase0/rules-review-completed.jsonl --output /tmp/logmind-rules-review-summary.json
```

Apply the same command to the model files. The validator requires exactly the sampled cases, complete ratings, and unchanged original observations/outputs; it never treats null fields as approvals. Ratings apply to the captured responses: newly generated responses need their own review, not blindly copied ratings. Reviews identify the single reviewer as Codex (agent), not independent human reviewers. The reviewed rate is the fraction with at least one unsupported factual claim among all sampled predictions, including invalid/abstained ones. The small stratified, correlated synthetic sample does not estimate production reliability.

Use fresh output directories/files for reruns: the CLI refuses to overwrite run artifacts. Model weights are not committed to the repository. All core commands and data remain runnable without live Kubernetes access.
