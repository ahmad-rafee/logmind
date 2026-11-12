# Generated candidate datasets

`v1-seed42/` contains the first candidate generated from the 42 reviewed fictional baselines. Regenerate from the repository root with `make generate`. A different seed can be generated with `make generate SEED=43`; use a separate output directory for any changed templates or generator source.

| Artifact | Records | Distinct scenarios |
| --- | --- | --- |
| incidents.jsonl | 150 | 42 |
| train.jsonl | 50 | 14 |
| validation.jsonl | 50 | 14 |
| test.jsonl | 50 | 14 |

Each split has eight records for each of the six incident classes plus two insufficient-evidence records. Each answerable class has six causal scenarios and 24 records overall. There are 42 baseline records, 36 conservative wording variants, 36 noisy variants, and 36 long variants. Five abstentions represent missing diagnostics; one represents target ambiguity. Counts of variants are not counts of independent incidents.

Wording substitutions only change allowlisted framing in metadata/status observations. Diagnostic events, log strings, termination facts, structured details, and labels remain fixed; any affected gold excerpt is transformed consistently. Noise adds 2–4 irrelevant supplied workload notes; long inputs add 32. No new containers, nodes, failure events, or application logs are invented. Seeded observation ordering changes where evidence occurs while retaining every original observation. Abstention records receive no additional diagnostic information.

`manifest.json` records generator version/source hash, an aggregate hash of ordered template filenames and bytes, seed, category/split/scenario/variant counts, and each JSONL file's SHA-256 checksum. Hashes describe the candidate bytes; they do not assert independent review or a frozen evaluation set. Reproducibility tests compare outputs byte-for-byte across directories and validate those hashes. Existing identical outputs are reused; differing outputs are rejected without overwriting.

Status: **candidate retained unchanged**. Its seed-42 bytes are also preserved in [frozen v1](../frozen/README.md), used in the completed Phase 0 baseline evaluation. Generation checks cover schema validity, gold references, fact retention, scenario isolation, and prompt boundaries. The 50 held-out records were evaluated and a preregistered prediction sample received case-by-case agent review; no independent human linguistic review was performed. The conservative variants do not establish production realism. Never tune on the frozen held-out test split.
