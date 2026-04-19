<div align="center">
  <h1>Zero-API-Key Web Search</h1>
  <p><strong>Free web search, browsing & claim verification for AI agents.</strong></p>
  <p><em>No API keys. No accounts. No limits. 100% free.</em></p>

  [![PyPI](https://img.shields.io/pypi/v/zero-api-key-web-search?label=pypi)](https://pypi.org/project/zero-api-key-web-search/)
  [![Python](https://img.shields.io/pypi/pyversions/zero-api-key-web-search)](https://python.org)
  [![MCP](https://img.shields.io/badge/MCP-Ready-0f766e.svg)](https://modelcontextprotocol.io/)
  [![Tests](https://img.shields.io/badge/tests-86%20passing-22c55e.svg)](./tests)
  [![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
</div>

---

## What is this?

A single `pip install` gives your AI agent live web search, full-page reading, and evidence-aware claim verification — all without any API key, account, or paid service.

- **Search**: Live results from DuckDuckGo (free) + optional SearXNG (self-hosted, free)
- **Browse**: Extract clean text from any URL, stripping boilerplate automatically
- **Verify**: Classify claims as supported / contested / likely false with evidence scores
- **Report**: Generate citation-ready evidence reports with rationale and next steps

## Quick start

```bash
pip install zero-api-key-web-search

# Search the web
zero-search "Python 3.13 release" --json

# Read a page
zero-browse "https://docs.python.org/3/whatsnew/" --json

# Verify a claim
zero-verify "Python 3.13 is the latest stable release" --deep --json

# Full evidence report
zero-report "Python 3.13 stable release" \
  --claim "Python 3.13 is the latest stable release" --deep --json
```

Legacy CLI aliases (`search-web`, `browse-page`, `verify-claim`, `evidence-report`) also work.

## Why this over a plain search wrapper?

| Feature | Plain search | Zero-API-Key Web Search |
| --- | --- | --- |
| Live search results | ✅ | ✅ |
| News / images / videos / books | ❌ | ✅ |
| Region & time filtering | ❌ | ✅ |
| Full-page text extraction | ❌ | ✅ |
| Claim verification with evidence scores | ❌ | ✅ |
| Supporting vs. conflicting evidence | ❌ | ✅ |
| Citation-ready evidence reports | ❌ | ✅ |
| Dual-provider cross-validation | ❌ | ✅ |
| API key required | Often | **Never** |
| Cost | Sometimes | **Free** |

## MCP server

Works with Claude Code, Cursor, Copilot, and any MCP-compatible agent:

```json
{
  "mcpServers": {
    "zero-api-key-web-search": {
      "command": "zero-mcp"
    }
  }
}
```

Four tools exposed: `search_web`, `browse_page`, `verify_claim`, `evidence_report`.

## Platform support

| Platform | Status | Entry point |
| --- | --- | --- |
| **CLI** | Ready | `zero-search`, `zero-browse`, `zero-verify`, `zero-report` |
| **MCP** | Ready | `zero-mcp` |
| **Claude Code** | Ready | `.claude/skills/zero-api-key-web-search/SKILL.md` |
| **Gemini** | Ready | `GEMINI.md` + `.gemini/SKILL.md` |
| **Cursor** | Ready | `.cursor/rules/zero-api-key-web-search.md` |
| **Copilot** | Ready | `.github/copilot/instructions.md` |
| **Codex** | Ready | `.codex/SKILL.md` |
| **Continue** | Ready | `.continue/skills/zero-api-key-web-search/SKILL.md` |
| **Manus** | Ready | Root `SKILL.md` + `docs/manus.md` |
| **Kiro** | Ready | `.kiro/steering/zero-api-key-web-search.md` |
| **OpenClaw** | Ready | `zero_api_key_web_search/skills/SKILL.md` |

## How verification works

`zero-verify` uses the **evidence-aware heuristic v3** model:

1. Search for the claim across available providers
2. Score each source on keyword overlap, source quality, freshness
3. Classify as supporting, conflicting, or neutral
4. Optionally fetch top pages for deeper page-aware analysis
5. Render a verdict with confidence and evidence breakdown

| Verdict | Meaning |
| --- | --- |
| `supported` | Strong evidence, low conflict |
| `likely_supported` | Leans positive, not decisive |
| `contested` | Support and conflict both meaningful |
| `likely_false` | Conflict strong, support weak |
| `insufficient_evidence` | Too weak for any firmer verdict |

This is a heuristic evidence classifier, not a proof engine. See [docs/trust-model.md](docs/trust-model.md) for details and limitations.

## Free dual-provider setup

Default install uses DuckDuckGo. For stronger cross-validated evidence, add a free self-hosted SearXNG:

```bash
./scripts/start-searxng.sh
export ZERO_SEARCH_SEARXNG_URL="http://127.0.0.1:8080"
./scripts/validate-free-path.sh
```

Or with Docker Compose:

```bash
cp .env.searxng.example .env
docker compose -f docker-compose.searxng.yml up -d
```

Full guide: [docs/searxng-self-hosted.md](docs/searxng-self-hosted.md).

## Evidence report example

```json
{
  "verdict": "contested",
  "confidence": "MEDIUM",
  "executive_summary": "Evidence is split...",
  "verdict_rationale": ["Source A supports...", "Source B contradicts..."],
  "coverage_warnings": ["Single-provider evidence path."],
  "source_digest": [
    {"title": "...", "url": "...", "classification": "supporting", "evidence_strength": 3}
  ],
  "next_steps": ["Add a second provider for cross-validation."]
}
```

## Architecture

```
zero_api_key_web_search/
  core.py              # UltimateSearcher — search, verify, report engine
  browse_page.py       # Readability-style page text extraction
  mcp_server.py        # MCP server (4 tools)
  transport.py         # SSL/TLS helpers
  search_web.py        # CLI: zero-search
  browse_page.py       # CLI: zero-browse
  verify_claim.py      # CLI: zero-verify
  evidence_report.py   # CLI: zero-report
  providers/
    base.py            # SearchProvider protocol (sync + async)
    ddgs.py            # DuckDuckGo provider
    searxng.py         # SearXNG provider
  skills/
    SKILL.md           # Bundled OpenClaw skill
```

Key engineering features:

- **Circuit breaker**: Trips after 3 consecutive provider failures, auto-resets after 60s
- **Async support**: `asearch()` for concurrent provider calls via `asyncio.gather`
- **Structured logging**: Configurable logging at search/verify/report entry points
- **Readability heuristic**: Semantic HTML5 + ARIA roles + text density scoring
- **Baseline comparison**: Majority-vote and keyword-count baselines in reports
- **Sub-claim decomposition**: Targeted sub-queries for independent evidence gathering

## Installation

```bash
pip install zero-api-key-web-search
```

Python 3.10+ required. No API keys, no accounts, no configuration needed.

## Development

```bash
pip install -e ".[dev]"
python -m pytest tests/ -x           # 86 tests
ruff check zero_api_key_web_search/ tests/
pyright zero_api_key_web_search/     # 0 errors
coverage report --fail-under=80       # 85% coverage
```

## Verification for ecosystem reviewers

1. `zero-report "Python 3.13 stable release" --claim "Python 3.13 is the latest stable release" --deep --json`
2. [docs/ecosystem-readiness.md](docs/ecosystem-readiness.md)
3. [docs/gemini-submission-checklist.md](docs/gemini-submission-checklist.md)
4. [docs/trust-model.md](docs/trust-model.md)

## License

MIT License.