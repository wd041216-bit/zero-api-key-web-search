# Benchmark Snapshot

The repository currently ships a deterministic benchmark runner for verdict regressions and score-bound checks.

## What is covered today

- `supported`
- `likely_supported`
- `contested`
- `likely_false`
- `insufficient_evidence`
- snippet-only and page-aware scenarios
- single-provider and multi-provider scenarios

## What the benchmark proves

Today the benchmark is best used as a regression alarm:

- it catches verdict drift
- it catches score-bound drift
- it protects the flagship `verify-claim` and `evidence-report` paths from silent regressions

It does **not** yet prove calibrated factual correctness across the open web.

## How to run it

```bash
python benchmarks/run_benchmark.py --json
```

## Current positioning

For GitHub and ecosystem reviewers, the benchmark is strong enough to show that:

- the repo has a testable verification model
- confidence is explainable rather than purely narrative
- evidence-report behavior is under regression control

The next calibration work is tracked in [benchmark-plan.md](./benchmark-plan.md).
