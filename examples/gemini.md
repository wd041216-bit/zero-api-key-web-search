# Gemini Example

Install the package:

```bash
pip install zero-api-key-web-search
```

Use it for factual or recent queries:

```bash
search-web "OpenAI API pricing" --type news --timelimit w
verify-claim "Python 3.13 is the latest stable release" --deep --max-pages 2 --json
evidence-report "Python 3.13 stable release" --claim "Python 3.13 is the latest stable release" --deep --json
```

Typical output shape:

```json
{
  "verdict": "contested",
  "coverage_warnings": [
    "Single-provider evidence path. Add another provider when possible."
  ],
  "analysis": {
    "report_model": "evidence-report-v2",
    "provider_diversity": 1,
    "page_aware": true,
    "support_score": 1.42,
    "conflict_score": 0.61
  }
}
```

How to interpret it:

- search before answering time-sensitive questions
- browse the top source when snippets are too thin
- use `evidence-report` when Gemini needs a citation-ready summary instead of raw signals
- self-host `SearXNG` and set `ZERO_SEARCH_SEARXNG_URL` if you want a stronger free provider mix
- present uncertainty when support and conflict both appear
