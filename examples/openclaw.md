# OpenClaw Example

Install the package:

```bash
pip install free-web-search-ultimate
```

The OpenClaw entry point is bundled at `free_web_search/skills/SKILL.md`.

Minimal flow:

```bash
search-web "latest Python release" --type news --timelimit w
verify-claim "Python 3.13 is the latest stable release" --deep --max-pages 2 --json
browse-page "https://docs.python.org/3/whatsnew/"
evidence-report "Python 3.13 stable release" --claim "Python 3.13 is the latest stable release" --deep --json
```

Typical output shape:

```json
{
  "verdict": "supported",
  "coverage_warnings": [],
  "analysis": {
    "report_model": "evidence-report-v2",
    "page_aware": true,
    "provider_diversity": 1
  }
}
```

Recommended behavior:

- search first for factual or recent questions
- use `verify-claim` for explicit claim checks
- use `evidence-report` when OpenClaw needs a compact evidence package with citations and next steps
- self-host `SearXNG` and set `CROSS_VALIDATED_SEARCH_SEARXNG_URL` for the recommended free dual-provider path
- use `--deep` when the claim is important enough to inspect source pages
- cite URLs instead of collapsing uncertainty
