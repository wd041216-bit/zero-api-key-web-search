---
name: cross-validated-search
description: >
  Gemini-compatible skill for source-backed web search, page reading, and evidence-aware claim checking.
  Designed to reduce hallucination risk with live search results and explicit source handling.
version: "16.0.0"
user-invocable: true
---

# Cross-Validated Search for Gemini CLI

Use this skill when Gemini needs current information, supporting sources, or a quick support/conflict read on a factual claim.

## Install

```bash
pip install cross-validated-search
```

## Core Commands

```bash
search-web "latest Python release" --type news --timelimit w
verify-claim "Python 3.13 is the latest stable release" --json
browse-page "https://docs.python.org/3/whatsnew/"
```

## When to Use

- factual questions about people, companies, dates, versions, or statistics
- recent events or time-sensitive changes
- tasks that require citations
- cases where conflicting sources should be shown explicitly

## Limits

- `verify-claim` is a heuristic first pass, not a fact-level proof engine.
- The default provider path is `ddgs`.
- Conflicts are surfaced, not automatically resolved.

## License

MIT License.
