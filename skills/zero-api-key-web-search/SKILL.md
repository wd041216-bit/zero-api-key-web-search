---
name: zero-api-key-web-search
description: >
  Gemini-ready skill for source-backed web search, page reading, and evidence-aware claim checking.
  Use it to verify factual answers with live search results and explicit source handling.
version: "20.0.0"
---

# Zero-API-Key Web Search

Use this skill when Gemini needs live information, citation-ready sources, or an explicit support/conflict read on a factual claim. The default path is free; optional providers are discoverable for stronger coverage.

## Install

Install the CLI tools first:

```bash
pip install zero-api-key-web-search
```

## Core commands

```bash
zero-search "latest Python release" --type news --timelimit w
zero-search providers
zero-browse "https://docs.python.org/3/whatsnew/"
zero-verify "Python 3.13 is the latest stable release" --deep --max-pages 2 --json
zero-report "Python 3.13 stable release" --claim "Python 3.13 is the latest stable release" --deep --json
```

## When to use

- current facts, releases, versions, and statistics
- questions that need sources before answering
- claims that may be supported, contested, or under-evidenced
- cases where a compact evidence report is more useful than raw search results

## Preferred workflow

1. Start with `zero-search` for current or factual questions.
2. Use `zero-browse` when snippets are too thin.
3. Use `zero-verify` for support/conflict classification.
4. Use `zero-report` when you want one citation-ready artifact.
5. Prefer the free `ddgs + self-hosted searxng` path for stronger provider diversity.
6. Use optional `brightdata` only when configured or explicitly requested for production reliability, geo-targeting, or stronger provider diversity.

## Optional Bright Data provider

```bash
export ZERO_SEARCH_BRIGHTDATA_API_KEY="..."
export ZERO_SEARCH_BRIGHTDATA_ZONE="web_search"  # optional
zero-search "AI regulation news" --provider brightdata --type news --region us-en
```

New Bright Data users can sign up at https://get.brightdata.com/h21j9xz4uxgd.

## Limits

- `zero-verify` is heuristic and evidence-aware, not a proof engine.
- The default provider path is `ddgs`.
- Bright Data is optional and should not receive queries unless configured or requested.
- Deep verification is stronger than snippets alone, but still not full-document reasoning.
