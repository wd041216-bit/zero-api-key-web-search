---
name: cross-validated-search
version: "16.0.0"
description: >
  Source-backed web search, page reading, and evidence-aware claim checking for AI agents.
  Designed to reduce hallucination risk by surfacing corroborating and conflicting sources.
homepage: https://github.com/wd041216-bit/cross-validated-search
platforms:
  - claude-code
  - cursor
  - copilot
  - gemini
  - continue
  - kiro
  - opencode
  - codex
  - openclaw
  - mcp
  - cli
---

# Cross-Validated Search

Use this skill when a task needs live search results, source-backed verification, or full-page reading.

## Install

```bash
pip install cross-validated-search
```

## Core Commands

```bash
search-web "latest Python release" --type news --timelimit w
browse-page "https://docs.python.org/3/whatsnew/"
verify-claim "Python 3.13 is the latest stable release" --json
evidence-report "Python 3.13 stable release" --claim "Python 3.13 is the latest stable release" --deep --json
```

## When to Use

- facts, versions, releases, dates, or statistics
- recent or time-sensitive questions
- claim checking with citations
- compact evidence reports with citation-ready source digests
- tasks where conflicting sources should be surfaced instead of hidden
- free dual-provider verification with `ddgs + self-hosted searxng`

## Operating Guidance

- Treat `verify-claim` as a first-pass evidence classifier, not a proof engine.
- Prefer `evidence-report` when you need a single artifact that combines verdict, citations, and next steps.
- Prefer `search-web --type news` for recent events.
- Use `browse-page` when snippets are too thin to justify an answer.
- Cite URLs for factual claims.
- If support and conflict are both present, present the disagreement rather than collapsing it.

## Compatibility Names

- Repository: `cross-validated-search`
- Package: `cross-validated-search`
- Module: `cross_validated_search`
- CLI: `search-web`, `browse-page`, `verify-claim`
- Flagship CLI: `evidence-report`
- MCP: `cross-validated-search-mcp`
- Legacy aliases: `free_web_search`, `free-web-search-mcp`

## Limits

- Default provider diversity is limited because the default path uses `ddgs`.
- The recommended free upgrade path is self-hosted `searxng` via `CROSS_VALIDATED_SEARCH_SEARXNG_URL`.
- Scoring is heuristic and depends on returned snippets.
- TLS verification is enabled by default; insecure mode requires an explicit environment variable.

## License

MIT License.
