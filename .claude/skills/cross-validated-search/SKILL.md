---
name: cross-validated-search
description: >
  Claude Code-compatible skill for source-backed web search, page reading, and evidence-aware claim checking.
  Use it when an answer depends on current facts, live sources, or explicit support/conflict handling.
version: "16.0.0"
---

# Cross-Validated Search for Claude Code

Use this skill when Claude Code needs current information, supporting citations, or a compact evidence report before answering.

## Install

```bash
pip install cross-validated-search
```

## Core Commands

```bash
search-web "latest Python release" --type news --timelimit w
browse-page "https://docs.python.org/3/whatsnew/"
verify-claim "Python 3.13 is the latest stable release" --deep --max-pages 2 --json
evidence-report "Python 3.13 stable release" --claim "Python 3.13 is the latest stable release" --deep --json
```

## When to Use

- time-sensitive questions about releases, dates, people, or statistics
- factual claims that should be checked before being stated confidently
- workflows where conflicting evidence should be surfaced instead of hidden
- research tasks that benefit from one citation-ready artifact

## Guidance

- Start with `search-web` for live facts and recent changes.
- Use `browse-page` when snippets are too thin to justify an answer.
- Use `verify-claim` for support/conflict classification.
- Use `evidence-report` when you want one compact output with verdict, citations, and next steps.
- Prefer the free `ddgs + self-hosted searxng` path for stronger provider diversity.

## Limits

- `verify-claim` is heuristic and evidence-aware, not a proof engine.
- The default path still starts with `ddgs`.
- Deep verification is stronger than snippets alone, but still not full-document reasoning.

## License

MIT License.
