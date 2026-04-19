---
name: zero-api-key-web-search
description: >
  Gemini-ready skill for source-backed web search, page reading, and evidence-aware claim checking.
  Use it to verify factual answers with live search results and explicit source handling.
version: "16.0.0"
---

# Zero-API-Key Web Search

Use this skill when Gemini needs live information, citation-ready sources, or an explicit support/conflict read on a factual claim.

## Install

Install the CLI tools first:

```bash
pip install zero-api-key-web-search
```

## Core commands

```bash
search-web "latest Python release" --type news --timelimit w
browse-page "https://docs.python.org/3/whatsnew/"
verify-claim "Python 3.13 is the latest stable release" --deep --max-pages 2 --json
evidence-report "Python 3.13 stable release" --claim "Python 3.13 is the latest stable release" --deep --json
```

## When to use

- current facts, releases, versions, and statistics
- questions that need sources before answering
- claims that may be supported, contested, or under-evidenced
- cases where a compact evidence report is more useful than raw search results

## Preferred workflow

1. Start with `search-web` for current or factual questions.
2. Use `browse-page` when snippets are too thin.
3. Use `verify-claim` for support/conflict classification.
4. Use `evidence-report` when you want one citation-ready artifact.
5. Prefer the free `ddgs + self-hosted searxng` path for stronger provider diversity.

## Limits

- `verify-claim` is heuristic and evidence-aware, not a proof engine.
- The default provider path is `ddgs`.
- Deep verification is stronger than snippets alone, but still not full-document reasoning.
