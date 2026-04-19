---
name: zero-api-key-web-search
version: "1.0.0"
description: >
  OpenClaw skill for source-backed web search, page reading, and evidence-aware claim checking.
  No API keys required. 100% free.
homepage: https://github.com/wd041216-bit/zero-api-key-web-search
---

# Zero-API-Key Web Search for OpenClaw

This legacy skill path remains available for compatibility. The canonical bundled
skill now lives at `zero_api_key_web_search/skills/SKILL.md`.

This skill gives OpenClaw a practical verification workflow:

- `zero-search` (alias: `search-web`) for live search results
- `zero-browse` (alias: `browse-page`) for reading the full content of a source
- `zero-verify` (alias: `verify-claim`) for support/conflict classification
- `zero-report` (alias: `evidence-report`) for a citation-ready summary with next steps

## Install

```bash
pip install zero-api-key-web-search
```

## Minimum verification

```bash
zero-search "OpenAI API pricing" --type news --timelimit w
zero-verify "Python 3.13 is the latest stable release" --deep --max-pages 2 --json
zero-report "Python 3.13 stable release" --claim "Python 3.13 is the latest stable release" --deep --json
```

## Recommended flow

1. Run `zero-search` for factual or recent questions.
2. Use `zero-browse` on the most relevant source when snippets are not enough.
3. Use `zero-verify` when a concrete claim needs a support/conflict summary.
4. Use `zero-report` when you want a compact evidence package with citations and next steps.
5. Use `--deep` when the claim matters enough to justify page-aware verification.
6. Cite the returned URLs in the final answer.

## What success looks like

- the verdict is explicit
- the result includes support and conflict scores
- `page_aware` is true when deep verification ran
- the recommended free path is `ddgs + self-hosted searxng`
- source URLs are ready to cite

## Limits

- `zero-verify` is heuristic and evidence-aware, not a proof engine.
- The default provider path is `ddgs`.
- The recommended free upgrade path is self-hosted `searxng` via `ZERO_SEARCH_SEARXNG_URL`.
- Conflicting sources are surfaced, not automatically reconciled.

## License

MIT License.