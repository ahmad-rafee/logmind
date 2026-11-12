# Baseline experiments

The deterministic rules baseline uses CPU only and requires no cluster or model. It consumes `PromptInput` (incident ID and observations), not labels, scenario IDs, gold evidence, or expected actions. It uses explicit termination/events and matched application-error/exit evidence, honors supplied container/attempt selection, and abstains for missing, conflicting, or multi-container evidence. It does not execute recommended checks.

Development used frozen v1 train/validation. Phase 0 is now complete: source/configuration hashes were fixed before both baselines ran on the same held-out test set. See [the report](PHASE0_REPORT.md), [reproduction commands](PHASE0_REPRODUCE.md), and [raw evidence](reports/phase0/). Do not tune against held-out outputs or overwrite this baseline archive.

```bash
make rules
make evaluate
# New runs need a fresh directory; existing runs are never overwritten:
make rules RULE_SPLIT=train RUN_DIR=experiments/runs/rules-v1-train
# Equivalent CLI:
uv run --locked logmind predict-rules --dataset data/frozen/v1 --split validation --output experiments/runs/another-validation-run
```

`make rules` defaults to `RULE_SPLIT=validation` and `RUN_DIR=experiments/runs/rules-v1-validation`. The run verifies the frozen release before prediction and writes:

| File | Meaning |
| --- | --- |
| records.jsonl | Authoritative PredictionRecord envelopes, including raw responses, errors, timing, and run metadata. |
| predictions.jsonl | Parsed prediction convenience export; **never use this valid-only file as the evaluation denominator**. |
| run.json | Dataset checksum/version/split, exact rules source hash, environment, and no-model/no-prompt settings. |
| rules.py, evaluation.py, pipeline.py, schemas.py | Captured source for reviewing the run and metric behavior. |
| metrics.json | Full-denominator classification, validity, abstention, and automatic-flag counts. |
| review-sample.jsonl | Unfilled review worksheet selected by the policy in REVIEW_PROTOCOL.md. |

Each record's elapsed_seconds includes prompt-input construction, rules, serialization, and parsing; it is not the repeated cold/warm benchmark required later. Run IDs identify the rules revision and input checksum; separate executions can have the same configuration ID but different timings. Run outputs are ignored by Git; retain/copy relevant reports deliberately when publishing results.

The evaluate CLI re-parses raw_response instead of trusting a stored parsed prediction. Unknown/duplicate IDs, mixed runs, or mismatched dataset checksums are errors. Missing incident outputs stay in N and count as incorrect, including when records.jsonl is empty. Malformed model text belongs inside a structurally valid PredictionRecord; malformed envelope JSONL is an artifact error and aborts evaluation. No invalid response is repaired or substituted.

Headline accuracy requires a schema/reference-valid exact category match. Macro-F1 averages the six answerable classes, with undefined per-class precision/recall/F1 set to zero. An insufficient_evidence prediction on an answerable case is a false negative; a class prediction on an insufficient-evidence case is a false positive. Invalid/missing outputs enter the invalid confusion-matrix column and are false negatives for their answerable gold class. Zero-support classes still enter the six-class mean as zero; report supports with the metric.

Validity rates use all N incidents as denominator: JSON parse, strict schema, and complete reference validity are separate. The full valid-output rate requires all three; unknown evidence IDs and wrong incident IDs invalidate classification even if the category matches. Answerable accuracy and correct abstention rates are reported separately, including missing_diagnostics versus target_ambiguity support.

Automatic flags cover nonexistent evidence IDs, explicitly quoted resource names absent from the input, and explicit exitCode/restartCount claims inconsistent with supplied selected-attempt numeric fields. This deliberately narrow detector can miss unsupported prose, unquoted names, and temporal contradictions. Flags may need contextual review; zero flags is not a measured zero hallucination rate. `reviewed_hallucination_rate` remains null until a completed review provides numerator/denominator. See [review protocol](REVIEW_PROTOCOL.md).

The raw run metrics retain null reviewed rates; separate published *-test-metrics-reviewed.json files join completed, validated single-agent reviews. Rules had 0/14 and the model 9/14 sampled predictions with unsupported factual claims. Classification and benchmark artifacts remain unchanged by review. Optional GPU commands are make model-setup, download-model, model, and phase0-benchmark; see the reproduction guide for fresh run paths and all settings.
