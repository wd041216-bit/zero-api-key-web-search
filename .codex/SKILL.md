---
name: cross-validated-search
description: >
  Codex-compatible skill for source-backed web search, page reading, and evidence-aware claim checking.
  Use it to verify factual answers with live results and explicit source handling.
version: "16.0.0"
---

# Cross-Validated Search for Codex

Use this skill when a response depends on current facts, recent releases, or source-backed verification.

## Install

```bash
pip install cross-validated-search
```

## Commands

```bash
search-web "latest Python release" --type news --timelimit w
verify-claim "Python 3.13 is the latest stable release" --json
browse-page "https://docs.python.org/3/whatsnew/"
```

## Guidance

- Search before answering factual or time-sensitive questions.
- Browse the page when snippets are too thin.
- Treat `verify-claim` as an evidence summary, not a proof certificate.
- Surface conflicts when they appear.

## License

MIT License.
