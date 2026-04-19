# OpenClaw Example

Install the package:

```bash
pip install zero-api-key-web-search
```

The OpenClaw entry point is bundled at `zero_api_key_web_search/skills/SKILL.md`.

Minimal flow:

```bash
zero-search "latest Python release" --type news --timelimit w
zero-verify "Python 3.13 is the latest stable release" --deep --max-pages 2 --json
zero-browse "https://docs.python.org/3/whatsnew/"
zero-report "Python 3.13 stable release" --claim "Python 3.13 is the latest stable release" --deep --json
```

Typical output shape:

```json
{
  "verdict": "supported",
  "coverage_warnings": [],
  "analysis": {
    "report_model": "zero-report-v2",
    "page_aware": true,
    "provider_diversity": 1
  }
}
```

Recommended behavior:

- search first for factual or recent questions
- use `zero-verify` for explicit claim checks
- use `zero-report` when OpenClaw needs a compact evidence package with citations and next steps
- self-host `SearXNG` and set `ZERO_SEARCH_SEARXNG_URL` for the recommended free dual-provider path
- use `--deep` when the claim is important enough to inspect source pages
- cite URLs instead of collapsing uncertainty
