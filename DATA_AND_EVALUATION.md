# Data and evaluation specification

## Incident records

Use UTF-8 JSONL, one object per incident. Required fields: id, scenario_id, split, source, category, root_cause, observations, evidence, expected_actions, and variant_tags. The source is synthetic or controlled_cluster. Observations hold structured status, termination details, Kubernetes events, log excerpts, and relevant workload metadata. Each observation has a stable evidence ID. Evidence lists gold supporting IDs and excerpts. Ground-truth fields must never enter a model prompt.

The implemented observation contract is `{id, kind, text, details}`: kind is status, termination, event, log, or metadata; details is a JSON object for structured fields and defaults to an empty object. Gold evidence entries are `{observation_id, excerpt}`; the ID must exist and the excerpt must occur verbatim in that observation's text. Observation IDs must be unique within each incident. Prompt input contains only incident_id and observations. Ground-truth labels may include insufficient_evidence for deliberately unanswerable cases; evidence and expected_actions may be empty.

Begin with at least two distinct causal scenarios per class, manually reviewed. Split by scenario_id into train, validation, and test before generating wording or noise variants, so variants cannot cross splits. Start with roughly 120-180 balanced records and a frozen held-out test set. The proposal's 300-500 incidents is a later target if time allows. Report distinct scenarios and variants separately. Add incomplete, noisy, long, and ambiguous records deliberately. Controlled-cluster records, if created, should be reported separately from synthetic ones.

To represent every class in all three splits, use at least three distinct scenarios per class. Six per class (two per split) is the recommended starting design; the two-scenario minimum alone is insufficient for that split design.

## Prediction JSON

Required exact fields and types:

    {
      "incident_id": "case-001",
      "category": "missing_config",
      "root_cause": "The pod references an absent ConfigMap.",
      "evidence_ids": ["event-2"],
      "explanation": "The FailedMount event names the absent ConfigMap.",
      "recommended_checks": ["Check the ConfigMap name and namespace."],
      "uncertain": false
    }

Category is one of the six labels or insufficient_evidence. Evidence IDs must occur in the input. Additional fields fail strict validation. Save the raw model response, parse/schema errors, model or backend ID, immutable revision, prompt version, decoding settings, and timing with each prediction. Count invalid outputs as incorrect; do not silently replace them. If a repair prompt is tried, treat it as another measured configuration. The system should express uncertainty where the evidence is incomplete or conflicting.

## Metrics

Primary root-cause accuracy is exact category match over the entire frozen test set. Report separate answerable-case accuracy and abstention behavior on ambiguous cases. Compute macro-F1 as the unweighted mean of six per-class F1 values, with class support and confusion matrix. State explicitly how insufficient_evidence predictions enter the calculation. Report JSON parse and strict-schema success rates. Invalid predictions count as wrong in headline classification metrics.

Automatically flag nonexistent evidence IDs, invented resource names, and claims contradicting explicit observations. These flags are a lower bound on hallucinations. Manually review a preregistered stratified test sample across all classes, including invalid and abstained outputs. Mark each prediction supported, partially supported, or unsupported, and assess whether recommendations are relevant and safe. Hallucination rate is the number of reviewed predictions with at least one unsupported factual claim divided by all reviewed predictions; show numerator and denominator. Prefer two reviewers; otherwise record the single-reviewer rubric and examples. An evidence ID that exists is not necessarily evidence that supports the claim.

Keep the test set untouched when tuning prompts and thresholds. Use validation for selection. Include sample counts and uncertainty intervals when feasible; avoid broad claims from a small synthetic sample.

## Benchmark protocol

Measure end-to-end wall time including prompt assembly, inference, and parsing. Report median and p95 latency, with cold and warm runs separate. Record input/output tokens and generated tokens per second. Use a fixed test subset, warm-up, and at least three repeated measurements per configuration. Record CPU peak RSS and, when available, GPU peak allocated/reserved memory. Capture OS, CPU/GPU, runtime and library versions, model revision, precision, threads, prompt, decoding settings, seed, and dataset checksum. Compare configurations on the same machine and inputs.
