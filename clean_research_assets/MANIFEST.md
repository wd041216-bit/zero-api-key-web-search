# Clean Research Assets Manifest

This directory contains the complete traceable evidence bundle for Zero-API-Key Web Search.

## Contents

| Asset | Path | Description |
|-------|------|-------------|
| Claim Ledger | `docs/claim-ledger.md` | Maps each public claim to its evidence and status |
| Verification Model | `docs/verification-model.md` | Signal definitions, verdict logic, and current limits |
| Trust Model | `docs/trust-model.md` | Semantic oracle boundary and operating boundaries |
| Evaluation | `docs/evaluation.md` | Research question, method, baselines, and answer |
| Benchmarks | `docs/benchmarks.md` | Regression suite and verdict family coverage |
| Verdict Matrix | `benchmarks/VERDICT_MATRIX.md` | Per-family classification matrix and baseline comparison |
| Abstract | `docs/ABSTRACT.md` | Project abstract with research question and key result |

## Export

Run `scripts/export_artifacts.sh` to produce a single JSON bundle containing all documents and test results.