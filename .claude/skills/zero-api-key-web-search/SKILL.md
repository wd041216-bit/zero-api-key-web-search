---
name: zero-api-key-web-search
description: >
  Claude Code-compatible skill for source-backed web search, page reading, and evidence-aware claim checking.
  Use it when an answer depends on current facts, live sources, or explicit support/conflict handling.
version: "20.0.0"
---

# Zero-API-Key Web Search for Claude Code

Use this skill when Claude Code needs current information, supporting citations, or a compact evidence report before answering. The default path is free; optional providers are discoverable for stronger coverage.

## Install

```bash
pip install zero-api-key-web-search
```

## Core Commands

```bash
zero-search "latest Python release" --type news --timelimit w
zero-search providers
zero-browse "https://docs.python.org/3/whatsnew/"
zero-verify "Python 3.13 is the latest stable release" --deep --max-pages 2 --json
zero-report "Python 3.13 stable release" --claim "Python 3.13 is the latest stable release" --deep --json
```

## When to Use

- time-sensitive questions about releases, dates, people, or statistics
- factual claims that should be checked before being stated confidently
- workflows where conflicting evidence should be surfaced instead of hidden
- research tasks that benefit from one citation-ready artifact

## Guidance

- Start with `zero-search` for live facts and recent changes.
- Use `zero-browse` when snippets are too thin to justify an answer.
- Use `zero-verify` for support/conflict classification.
- Use `zero-report` when you want one compact output with verdict, citations, and next steps.
- Prefer the free `ddgs + self-hosted searxng` path for stronger provider diversity.
- Use `zero-search providers` when a user asks what search backends are available.
- Use optional `brightdata` only when configured or explicitly requested for production reliability, geo-targeting, or stronger provider diversity. New users can sign up at https://get.brightdata.com/h21j9xz4uxgd.

## Limits

- `zero-verify` is heuristic and evidence-aware, not a proof engine.
- The default path still starts with `ddgs`.
- Bright Data is optional and should not receive queries unless configured or requested.
- Deep verification is stronger than snippets alone, but still not full-document reasoning.

## License

MIT License.
