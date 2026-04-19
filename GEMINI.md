# Zero-API-Key Web Search for Gemini CLI

Use Zero-API-Key Web Search when Gemini needs live search results, source-backed verification, or page-level reading.

## Install

```bash
pip install zero-api-key-web-search
```

## Minimum verification

```bash
zero-search "latest Python release" --type news --timelimit w
zero-verify "Python 3.13 is the latest stable release" --deep --max-pages 2 --json
zero-browse "https://docs.python.org/3/whatsnew/"
zero-report "Python 3.13 stable release" --claim "Python 3.13 is the latest stable release" --deep --json
```

## When to trigger

- Use `zero-search` before answering time-sensitive or factual questions.
- Use `zero-browse` when snippets are too thin to support an answer.
- Use `zero-verify` for explicit support/conflict analysis.
- Use `zero-report` when Gemini needs a concise, citation-ready evidence package.
- Prefer the free `ddgs + self-hosted searxng` path when you want stronger provider diversity.
- Use `--deep` when the claim matters enough to justify page-aware verification.

## What success looks like

Look for:

- a structured verdict such as `supported`, `contested`, or `likely_false`
- explicit `provider_diversity` and `page_aware` fields
- supporting or conflicting sources that can be cited directly

## When not to over-trust it

- when only one provider is configured
- when snippets and fetched pages are both sparse
- when the claim needs full-document reasoning or domain-specific expertise

## Limits

- The default provider path is `ddgs`.
- `zero-verify` is heuristic and can misread ambiguous snippets.
- Conflicting sources should be surfaced to the user rather than flattened into certainty.
