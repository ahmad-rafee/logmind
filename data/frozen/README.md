# Frozen datasets

Version **v1** fixes the seed-42 candidate at 150 records across 42 distinct scenarios. Train, validation, and test each contain 50 records across 14 scenarios. Each split has eight records per answerable class plus two insufficient-evidence cases. Only template/context holdout is claimed; variants are not independent incidents and the shared failure mechanisms remain a limitation.

Creation audits strict schemas, gold references, IDs, counts, scenario split isolation, split membership, and byte-for-byte reproduction from the current generator and reviewed templates before copying any release files. The original candidate is left unchanged. No rules or model outputs were used to select this dataset.

## Verify

```bash
make verify-dataset
uv run --locked logmind verify-dataset data/frozen/v1
```

`v1/manifest.json` contains release metadata, candidate settings, audit results, environment versions, and the complete artifact inventory with SHA-256 hashes. `v1/manifest.sha256` records its checksum; an additional copy of the pin is published below after creation. `candidate-manifest.json` preserves the original generator manifest verbatim. Verification rejects changed/missing/extra artifacts, altered manifests, symlinks, inconsistent split membership/counts, and mismatched source/template provenance. It uses the frozen inputs rather than the current working generator/templates.

Published v1 frozen-manifest SHA-256:

```text
c60c7ebcdbcee390c571627dc1e2b444eb380e6197f64304eb42bc3d17b04d87
```

```bash
uv run --locked logmind verify-dataset data/frozen/v1 --expected-sha256 c60c7ebcdbcee390c571627dc1e2b444eb380e6197f64304eb42bc3d17b04d87
```

Frozen versions are not overwritten by these commands. Files remain ordinary files: checksums and version discipline detect changes; they do not prevent every external write or provide digital signatures. Use the published manifest pin for verification against a separately recorded reference. A new dataset needs a new version/path; do not alter v1 to improve evaluation results.

## Reproduce

Copy the captured package/templates to a writable directory. Run the following from the repository root; the task-specific variable names avoid changing system environment variables:

```bash
logmind_repro_dir=$(mktemp -d)
cp -R data/frozen/v1/reproduction/. "$logmind_repro_dir/"
cd "$logmind_repro_dir"
uv run --locked logmind generate --seed 42 --output regenerated
```

Compare the four regenerated JSONL checksums with `candidate.files` in the frozen manifest (or `files` in the candidate manifest). The candidate manifest itself should also match byte-for-byte when using the captured Python/package versions. Do not run installation or Python imports directly inside the sealed reproduction directory, since generated environment/bytecode files would change its inventory. The captured source bundle is for regeneration; it does not include the development test suite or every project document.

Verification evidence (2026-11-12): copied the sealed reproduction inputs into a separate writable temporary directory, installed with `uv run --locked` using Python 3.12.13, and regenerated seed 42. All four JSONL files and the candidate manifest matched the frozen originals byte-for-byte. Frozen verification passed afterward. The project check suite passed 147 tests plus Ruff lint/format checks.

## Evaluation discipline

- Develop on train; select rules, prompts, and thresholds on validation.
- Reserve test for held-out reporting. Do not tune against its labels or outputs.
- Verify the release before a run and record the version and JSONL checksum used.
- Report scenario counts separately from variant counts and disclose synthetic-data and shared-mechanism limitations.

Status: **frozen and evaluated in Phase 0**, with bytes and pins unchanged. See ../../experiments/PHASE0_REPORT.md for both baselines, repeated benchmarks, and single-agent prediction review. All causal review was agent review under project-owner authorization, not independent human linguistic review.
