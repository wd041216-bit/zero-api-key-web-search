# Why Not Just Search?

Plain search wrappers usually stop at returning links or snippets.

Cross-Validated Search goes further in four ways:

## 1. It treats search as evidence input, not final output

- `search-web` returns ranked, deduplicated sources
- `verify-claim` turns those sources into a verdict-oriented evidence summary

## 2. It exposes conflict instead of hiding it

The project does not collapse conflicting sources into fake certainty. It keeps support and conflict visible through separate scores, source lists, and the higher-level `evidence-report` rationale layer.

## 3. It can read pages when snippets are too thin

With `verify-claim --deep`, the verifier reads top sources and re-scores the evidence using page text.

## 4. It is being structured for real multi-provider verification

The provider abstraction is now in place so the project can evolve from single-provider search into real provider-aware cross-validation.

## Current limits

- the default path is still `ddgs`
- deep verification is still heuristic, not entailment
- confidence is not yet benchmark-calibrated

## Why that matters for ecosystem collection

This repository is aiming to be an evidence-aware verification layer for agent runtimes, not just a convenience wrapper around search.
