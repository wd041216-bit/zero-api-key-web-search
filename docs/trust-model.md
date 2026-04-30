# Trust Model

Zero-API-Key Web Search is an evidence-aware verification helper for agent workflows. It improves the odds that an answer is grounded in live sources, but it does not eliminate uncertainty.

## What the project does

- `search-web` fetches live results and deduplicates corroborated URLs.
- `browse-page` extracts readable content from a selected URL.
- `verify-claim` classifies returned snippets as supporting, conflicting, or neutral and computes weighted evidence scores.
- `evidence-report` packages the result into a reviewer-facing artifact with rationale, stance summaries, and coverage warnings.

## Current verification model

The current model is `evidence-aware-heuristic-v3`.

Signals used:

- keyword overlap between the claim and returned snippets
- contradiction markers such as `false`, `incorrect`, and `fact check`
- source quality heuristics from domain shape and snippet language
- source freshness when result dates are available
- domain diversity across the evidence set
- optional page content from fetched top sources
- optional provider diversity when self-hosted `searxng` is configured

Returned analysis includes:

- support score
- conflict score
- net signal
- domain diversity
- provider diversity
- per-source quality and freshness metadata

## What the project does not guarantee

- It does not perform fact-level parsing or logical proof.
- It does not reconcile conflicting sources automatically.
- It does not guarantee authority just because a result appears high in search.
- It does not provide strong provider diversity on the default path, because the default provider is `ddgs` unless you add self-hosted `searxng`.
- It can misread ambiguous or weak snippets.

## Secure defaults

- TLS verification is enabled by default for `browse-page`.
- Insecure TLS is only available through explicit opt-in:
  - `ZERO_SEARCH_INSECURE_SSL=1`
  - `FREE_WEB_SEARCH_INSECURE_SSL=1`

## Recommended usage

1. Use `search-web` for factual or time-sensitive questions.
2. Use `browse-page` on the most relevant source when snippets are insufficient.
3. Use `verify-claim` when a concrete statement needs a support/conflict view.
4. Keep citations and uncertainty visible in the final answer.

## Current extension points

- add self-hosted `searxng` by setting `ZERO_SEARCH_SEARXNG_URL`
- enable page-aware verification with `verify-claim --with-pages`

## Semantic Oracle Boundary

The verification model operates at the **snippet keyword** level. It does not perform:

- Natural language inference or textual entailment
- Semantic similarity beyond exact keyword overlap
- Coreference resolution across sources
- Logical consistency checking between claims

The boundary between "syntactic signal" (keyword overlap, conflict markers) and "semantic signal" (source quality heuristics, domain trust) is at `_classify_source_against_claim` in `core.py`. Everything above that line is scoring arithmetic; everything below is string matching. The system is reliable inside this boundary and unreliable outside it.

### Operating Boundaries

The heuristic model is designed for:
- Factual claims about verifiable entities (software versions, release dates, public events)
- English-language claims (conflict markers exist for ES/FR/DE/ZH but are not calibrated)
- Claims where at least 3-5 search results are returned

It is **not** designed for:
- Subjective or normative claims
- Claims requiring domain-specific expertise (medical, legal, financial)
- Claims with no web footprint
- Multilingual claims where conflict markers may not fire

## Extension points

- provider weighting and scoring calibration via regression data (`tests/` fixtures)
- page-aware verification beyond keyword heuristics (`--deep` / `--with-pages`)
- benchmark dataset for confidence tracking (`benchmarks/`)
