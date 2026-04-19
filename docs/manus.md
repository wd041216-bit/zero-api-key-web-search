# Manus Setup

`zero-api-key-web-search` is compatible with Manus-style Agent Skills and CLI-first workflows.

## Install

```bash
pip install zero-api-key-web-search
```

## Skill surface

Use the repository root [SKILL.md](../SKILL.md) as the canonical skill definition.

The skill is designed for tasks where an agent should:

- search before answering recent or factual questions
- verify claims with supporting and conflicting evidence
- browse full pages when snippets are too thin
- produce citation-ready evidence summaries

## Suggested workflow

```bash
search-web "latest Python release" --type news --timelimit w
browse-page "https://docs.python.org/3/whatsnew/"
verify-claim "Python 3.13 is the latest stable release" --deep --json
evidence-report "Python 3.13 stable release" --claim "Python 3.13 is the latest stable release" --deep --json
```

## Notes

- `verify-claim` is heuristic and evidence-aware, not a proof engine.
- The default provider path starts with `ddgs`.
- For stronger free evidence diversity, configure self-hosted SearXNG via `ZERO_SEARCH_SEARXNG_URL`.
