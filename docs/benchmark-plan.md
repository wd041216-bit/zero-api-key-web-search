# Benchmark Plan

This repository now has a provider-aware and page-aware verification path. The next step is calibration.

## Goal

Measure whether verdicts and confidence signals stay stable as the verifier evolves.

## Dataset shape

The initial fixture format is JSONL:

- `id`
- `claim`
- `expected_verdict`
- `expected_page_aware`
- optional score bounds such as `min_support_score` or `max_conflict_score`
- `notes`

See [../benchmarks/claims.jsonl](../benchmarks/claims.jsonl) and [../benchmarks/run_benchmark.py](../benchmarks/run_benchmark.py).

## Phased plan

1. Start with hand-curated regression claims.
2. Add provider-specific fixtures for `ddgs` and `searxng`.
3. Add page-aware scenarios where snippets are weak but pages are strong.
4. Track score drift for support/conflict weighting with explicit bounds.

## Current deterministic runner

Run the current regression suite with:

```bash
python benchmarks/run_benchmark.py
python benchmarks/run_benchmark.py --json
```

This first pass uses curated fixtures instead of live network calls so it is stable in CI.
It now validates both verdicts and score ranges, so it can catch basic drift in support/conflict weighting.
The current suite also emits grouped summaries for verdict buckets, page-aware cases, and provider-diversity coverage.

## What to measure

- verdict accuracy against expected regression labels
- changes in `support_score` and `conflict_score`
- behavior differences between snippet-only and page-aware runs
- behavior differences across providers
- coverage distribution across verdict families so one regression class does not dominate the suite

## Non-goals for the first benchmark pass

- global factual accuracy claims
- proof-level calibration
- broad statistical guarantees
