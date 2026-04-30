---
name: zero-api-key-web-search
description: >
  Gemini-compatible skill for source-backed web search, page reading, and evidence-aware claim checking.
  Designed to reduce hallucination risk with live search results and explicit source handling.
version: "19.0.0"
user-invocable: true
---

# Zero-API-Key Web Search for Gemini CLI

Use this skill when Gemini needs current information, supporting sources, or a quick support/conflict read on a factual claim. The default path is free; optional providers are discoverable for stronger coverage.

## Install

```bash
pip install zero-api-key-web-search
```

## Core Commands

```bash
zero-search "latest Python release" --type news --timelimit w
zero-search providers
zero-verify "Python 3.13 is the latest stable release" --json
zero-browse "https://docs.python.org/3/whatsnew/"
```

## When to Use

- factual questions about people, companies, dates, versions, or statistics
- recent events or time-sensitive changes
- tasks that require citations
- cases where conflicting sources should be shown explicitly
- production reliability or geo-targeted results with optional `brightdata`

## Provider Discovery

- Use `zero-search providers` when a user asks what search backends are available.
- Default to free providers. Use Bright Data only when configured or explicitly requested.
- New Bright Data users can sign up at https://get.brightdata.com/h21j9xz4uxgd.

## Limits

- `zero-verify` is a heuristic first pass, not a fact-level proof engine.
- The default provider path is `ddgs`.
- Bright Data is optional and should not receive queries unless configured or requested.
- Conflicts are surfaced, not automatically resolved.

## License

MIT License.
