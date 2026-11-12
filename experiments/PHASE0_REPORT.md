# Phase 0 baseline report
Status: **complete**. Measurements and case-by-case agent reviews recorded 2026-11-12.
The deterministic rules baseline outperformed this fixed, unmodified Qwen3-1.7B zero-shot configuration on frozen v1. This establishes a reproducible baseline, not production reliability or a best-achievable score for the model family. No prompt, rule, or decoding changes were selected using held-out results.
## Dataset and fixed configurations
Frozen v1 contains 150 synthetic records across 42 scenarios. Train/validation/test each contain 50 records across 14 scenarios. Test support is eight records per answerable class plus two insufficient-evidence cases. Variants from a scenario never cross splits. These are template/context holdouts: OOM and missing-resource mechanisms are shared across splits; variants are correlated and not independent incidents.
Both held-out runs use test.jsonl SHA-256 `80ee3bf10203c44a11f8afdb61c226d18f47cd30e9e1289b3404b02d97084c86`. The frozen release manifest pin is `c60c7ebcdbcee390c571627dc1e2b444eb380e6197f64304eb42bc3d17b04d87`. No live cluster is needed. All model inputs are the full PromptInput JSON with gold annotations excluded.
- Rules: deterministic direct-event/termination matching with scoped container/attempt selection and conservative abstention; CPU only. Exact source revision appears in the archived run.json.
- Model: [Qwen/Qwen3-1.7B](https://huggingface.co/Qwen/Qwen3-1.7B), model and tokenizer commit `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`; PyTorch 2.7.1+cu128, Transformers 4.57.6, BF16 CUDA, SDPA, four CPU threads, seed 42, greedy generation, thinking disabled, 512 output-token maximum, 16,384-token input ceiling. No truncation, repair, training, quantization, or few-shot examples.
experiments/configs/phase0-evaluation-lock.json fixed model/prompt/rule/evaluator/benchmark source hashes before held-out predictions. The prompt, config, raw responses, parser/reference errors, source snapshots, token/memory telemetry, environment versions, and dependency lockfile are preserved under reports/phase0.
## Held-out quality
| Metric | Rules | Qwen3-1.7B |
| --- | ---: | ---: |
| N / scenarios | 50 / 14 | 50 / 14 |
| Accuracy, all outputs | 100.0% | 50.0% |
| Answerable-case accuracy (N=48) | 100.0% | 52.1% |
| Six-class macro-F1 | 1.0000 | 0.4821 |
| JSON parse / strict schema / reference-valid outputs | 100% / 100% / 100% | 90% / 90% / 90% |
| Correct abstentions (N=2) | 2 / 2 | 0 / 2 |
| Unsupported factual claims in reviewed sample | 0/14 (0%) | 9/14 (64.3%) |

Invalid outputs remain in the denominator. All five invalid model responses were Markdown-fenced JSON and were not repaired; there were zero inference/runtime failures. The model never chose insufficient_evidence, including both deliberately ambiguous cases. An uncertain=true flag on another category is not an abstention under the declared metric. Full supports/confusion matrices are in the archived metric files.
| Answerable class (support 8 each) | Model recall | Model F1 |
| --- | ---: | ---: |
| container_crash | 1.000 | 0.593 |
| oom_killed | 0.500 | 0.400 |
| image_pull_failure | 0.375 | 0.500 |
| probe_failure | 0.250 | 0.400 |
| missing_config | 0.000 | 0.000 |
| scheduling_failure | 1.000 | 1.000 |

The model often labeled probe/configuration failures as container_crash and sometimes invented OOM for image-pull failures. Good JSON validity or an existing evidence ID does not establish factual support. Rules expose direct cues in intentionally discriminative synthetic templates; their 100% score should not be extrapolated to unobserved production failures.
## Reviewed factual support and recommendations
The preregistered evaluator policy samples two cases per answerable class, preferring invalid/abstained outputs when present, plus one per ambiguity group in deterministic hash order (seed 42). Fourteen predictions were reviewed per backend. Source samples and completed worksheets are unchanged except the explicit rating fields; review.py validates sample completeness and preserved facts.
Reviewer: **Codex, one agent reviewer**. This is not two independent reviewers or independent human review. Rules: 14 supported; 0/14 with unsupported factual claims; relevant/safe checks 14/14. Model: 3 supported, 9 partially supported, 2 unsupported; 9/14 with unsupported factual claims; relevant checks 12/14 and no explicit repair directives in 14/14. Ambiguous “ensure” recommendations were interpreted as verification, not permission to change resources. This small unweighted stratified sample intentionally includes invalid outputs and correlated variants; its rate is descriptive, not an unbiased population estimate.
Examples with case-level notes:
- `case-89acecb0a1bd852655e6ed6a`: model asserts an image-pull failure triggered an OOM kill, although the container never started.
- `case-d21a231cc9578109c935d8f8`: model uses attempt-1 historical OOM to support a cause for selected attempt 3 without current termination evidence.
- `case-f675c76d0733799914603359`: root reverses the missing image platform despite an otherwise correct mismatch explanation.
- Invalid Markdown fences are classification failures, but are not themselves factual hallucinations. Case notes separately identify factual overclaims. Taxonomy/scope mistakes with factually correct prose are distinguished from invented events.

The narrow automatic flags found zero flagged test predictions in both runs; the agent review found nine model outputs with unsupported claims. Zero automatic flags is therefore not a measured zero hallucination rate. Original metrics keep the reviewed rate null; separate *-test-metrics-reviewed.json files join the explicit review numerator/denominator without altering raw results.
## Latency and memory
Machine: WSL2 Linux, Intel i9-13900H (8 logical CPUs exposed), approximately 31 GiB RAM, NVIDIA RTX 5060 Laptop GPU (8151 MiB), driver 621.14. GPU is shared with host/display activity. Runtime/environment and complete CPU details are in hardware.json and each run manifest.
Seven matched held-out inputs (one per category) were hash-selected independent of scores; three repetitions per input/configuration give 21 cold and 21 warm observations per backend. Each cold observation starts a fresh Python process/model and includes imports/model load/first prediction from worker entry; interpreter startup, OS file-cache flushing, and downloads are excluded. Warm uses one loaded process, one discarded warm-up, and three full repetitions. Inputs and every raw measured response are retained.
| Backend / mode | N | Median seconds | p95 seconds | Peak RSS GiB | GPU allocated / reserved GiB |
| --- | ---: | ---: | ---: | ---: | ---: |
| rules / cold | 21 | 0.125268 | 0.135431 | 0.039 | n/a |
| rules / warm | 21 | 0.000290 | 0.000375 | 0.031 | n/a |
| model / cold | 21 | 19.004963 | 23.188224 | 4.031 | 3.509 / 3.559 |
| model / warm | 21 | 10.144099 | 12.776017 | 1.672 | 3.508 / 3.598 |

Model benchmark inputs contain 591–1864 tokens (median 1275); generated outputs 156–300 tokens (median 245). Median generated tokens per end-to-end second: 13.07 cold and 24.72 warm. Rules have no token-generation throughput. All 21 cold/warm measured outputs per backend are valid; that subset validity does not replace the full-test 90% model validity.
Latency includes prompt assembly, inference, parsing, and instrumentation; p95 uses linear interpolation. Cold RSS is process-lifetime peak; warm RSS is sampled every 10ms. GPU values are PyTorch allocator peaks, not whole-device usage. Benchmarks run sequentially with no overlapping LogMind inference, but host activity/thermal state/file caches remain confounds.
The seven selected inputs contain no long variant and do not represent the longest-context performance. Separately, the full model test used 591–4111 input tokens, with peak GPU allocated/reserved 3.859/4.148 GiB and process-lifetime peak RSS 4.034 GiB. A development smoke reached 4179 input tokens. The configured 16,384-token ceiling is not a claim that every such input fits this shared GPU.
## Reproduction and artifacts
Follow [PHASE0_REPRODUCE.md](PHASE0_REPRODUCE.md). [phase0-summary.json](reports/phase0/phase0-summary.json) combines measured quality/review/benchmark data. [Archived evidence](reports/phase0/) includes all held-out raw records, fixed config/source/dependency inputs, original/completed review samples, every cold/warm measurement, environment, and a standalone reproduction bundle. Copy reproduction/ to a writable directory before executing it; do not install environments or bytecode inside the sealed archive.

Reproduction was exercised from a writable copy with a fresh core-only environment: all generated data/manifest bytes matched, frozen integrity passed, CPU rules reproduced 50/50, and captured model metrics recomputed unchanged. After optional model setup, GPU inference ran from that captured package/config without runtime error (1302 input / 259 output tokens). This was a development-case smoke, not an additional held-out model selection run. Evidence is in reproduction-check.json and reproduced-model-smoke.json.
Verify the archive from the repository root:

```bash
cd experiments/reports/phase0
sha256sum --check SHA256SUMS
```

Frozen v1 is unchanged. The observed baseline gap is a starting point for validation-selected prompt/context experiments; it does not establish whether adaptation or quantization will help. No inferential confidence intervals are claimed from correlated synthetic variants and a single small template holdout. Phase 0 is complete without a UI, live cluster, training, or model-response repairs.

Archive SHA256SUMS SHA-256 pin:

```text
b0283eb6c34bd9401a2ae13d76cb074588f7fb4cc990ed5ffda5990f931202eb
```

Final verification: 181 tests passed; Ruff lint/format checks passed; source/wheel builds succeeded; the frozen manifest pin and all 217 archived artifact checksums verified. Captured-bundle reproduction checks are recorded above. No Phase 1 experiments were run as part of this baseline closure.
