---
name: cross-validated-search
version: "15.0.0"
description: >
  OpenClaw skill for source-backed web search, page reading, and evidence-aware claim checking.
  Use it to verify factual answers with live search results and explicit source handling.
homepage: https://github.com/wd041216-bit/cross-validated-search
---

# Cross-Validated Search for OpenClaw

This skill gives OpenClaw a practical verification workflow:

- `search-web` for live search results
- `browse-page` for reading the full content of a source
- `verify-claim` for support/conflict classification
- `evidence-report` for a citation-ready summary with next steps

## Install

```bash
pip install free-web-search-ultimate
```

## Minimum verification

```bash
search-web "OpenAI API pricing" --type news --timelimit w
verify-claim "Python 3.13 is the latest stable release" --deep --max-pages 2 --json
evidence-report "Python 3.13 stable release" --claim "Python 3.13 is the latest stable release" --deep --json
```

## Recommended flow

1. Run `search-web` for factual or recent questions.
2. Use `browse-page` on the most relevant source when snippets are not enough.
3. Use `verify-claim` when a concrete claim needs a support/conflict summary.
4. Use `evidence-report` when you want a compact evidence package with citations and next steps.
5. Use `--deep` when the claim matters enough to justify page-aware verification.
6. Cite the returned URLs in the final answer.

## What success looks like

- the verdict is explicit
- the result includes support and conflict scores
- `page_aware` is true when deep verification ran
- the recommended free path is `ddgs + self-hosted searxng`
- source URLs are ready to cite

## Limits

- `verify-claim` is heuristic and evidence-aware, not a proof engine.
- The default provider path is `ddgs`.
- The recommended free upgrade path is self-hosted `searxng` via `CROSS_VALIDATED_SEARCH_SEARXNG_URL`.
- Conflicting sources are surfaced, not automatically reconciled.

## License

MIT License.
