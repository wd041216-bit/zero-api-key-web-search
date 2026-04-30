# Verification Model

`verify-claim` uses an evidence-aware heuristic model tuned for agent workflows.
It is designed to help an agent decide whether a claim looks supported,
contested, likely false, or still under-evidenced before presenting it as fact.

## Current Model

Model name: `evidence-aware-heuristic-v3`

Signals combined per source:

- keyword overlap between the claim and the source title/snippet
- contradiction markers such as `false`, `misleading`, `debunked`, or `not`
- source-quality heuristics
- source freshness when a parseable date is available
- domain diversity across the retrieved evidence set
- optional page-aware verification using fetched source content
- optional provider diversity when self-hosted `searxng` is configured

Each source gets a verification payload in `source.extra["verification"]`:

- `classification`
- `keyword_overlap`
- `conflict_markers_detected`
- `source_quality`
- `freshness`
- `evidence_strength`

## Source Quality Heuristics

The quality score is intentionally simple and explainable. It currently rewards:

- institutional domains such as `.gov`, `.edu`, `.mil`
- nonprofit or international domains such as `.org`, `.int`
- official or documentation-like domains such as `docs.*` or `developer.*`
- high-signal language in the title or snippet, for example `official`,
  `documentation`, `release notes`, `research`, or `report`
- corroborated URLs
- richer snippets with enough content to classify

This is not a trust oracle. It is an input signal, not a proof of truth.

## Verdict Logic

The final verdict is based on weighted support and conflict scores:

- `supported`: strong support, little to no conflict, and at least moderate domain diversity
- `likely_supported`: evidence leans positive but is not decisive
- `contested`: both support and conflict have meaningful weight
- `likely_false`: conflict is strong and support is weak
- `insufficient_evidence`: evidence exists but is not strong enough to justify a firmer call

## Intended Use

This model is useful for:

- agent-side preflight checks before answering factual questions
- surfacing conflicting evidence instead of hiding it
- giving users a source-backed confidence signal
- deciding when a deeper page read or manual verification is needed

## Current Limits

This repository **does** provide:

- multi-provider evidence fusion with weighted provider trust scores (via `_cross_validate` in `core.py`)
- optional page-aware verification (`--deep` / `--with-pages`)
- conflict summarization with stance buckets and domain-level breakdowns

It does **not** yet provide:

- fact-level extraction from full documents
- citation-level entailment checking
- domain-specific authority models
- benchmark-driven confidence calibration

The flagship reviewer-facing surface built on top of this model is `evidence-report-v2`, which adds:

- verdict rationale
- stance summaries
- coverage warnings
- citation-ready source digests

## Extension Points

1. fact-level extraction from full documents
2. citation-level entailment checking
3. domain-specific authority models
4. benchmark fixtures and regression scoring

See `docs/trust-model.md` for the semantic oracle boundary and `docs/claim-ledger.md` for the status of each claim.
