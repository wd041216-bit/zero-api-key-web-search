<div align="center">
  <h1>Zero-API-Key Web Search</h1>
  <p><strong>Search infrastructure for AI agents.</strong></p>
  <p><em>Free by default. MCP-ready. LLM-context aware. Production-grade when you opt in.</em></p>

  [![PyPI](https://img.shields.io/pypi/v/zero-api-key-web-search?label=pypi&cache=20260503)](https://pypi.org/project/zero-api-key-web-search/)
  [![Python](https://img.shields.io/pypi/pyversions/zero-api-key-web-search?cache=20260503)](https://python.org)
  [![MCP](https://img.shields.io/badge/MCP-Ready-0f766e.svg)](https://modelcontextprotocol.io/)
  [![Tests](https://img.shields.io/badge/tests-98%20passing-22c55e.svg)](./tests)
  [![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

  <br><br>
  <img src="assets/agent-search-pipeline.svg" alt="AI-agent search pipeline" width="920">
</div>

---

## What It Does

Zero-API-Key Web Search is a local-first, MCP-native search and evidence-verification toolkit for AI agents. It gives your agent live web search, LLM-optimized context extraction, claim verification with weighted evidence scoring, and citation-ready evidence reports — all without requiring an API key by default.

The verification model (`evidence-aware-heuristic-v3`) classifies sources as supporting, conflicting, or neutral using keyword overlap, domain-quality heuristics, freshness, and optional page-aware rescoring. This project does not perform fact-level proof or logical entailment; it is a signal amplifier for agent grounding decisions.

## 30-Second Setup

```bash
pip install zero-api-key-web-search

# Search the web — no API key needed
zero-search "Python 3.13 release" --json

# Build citation-ready LLM context
zero-context "Python 3.13 stable release" --goggles docs-first

# Read a page
zero-browse "https://docs.python.org/3/whatsnew/" --json

# Verify a claim
zero-verify "Python 3.13 is the latest stable release" --deep --json

# Full evidence report
zero-report "Python 3.13 stable release" \
  --claim "Python 3.13 is the latest stable release" --deep --json
```

Legacy CLI aliases (`search-web`, `browse-page`, `verify-claim`, `evidence-report`) also work.

## Your Agent Gets

| Agent job | Command | What the agent gets |
| --- | --- | --- |
| Ground an answer | `zero-context "FastAPI lifespan docs"` | compact Markdown context with citations |
| Verify a claim | `zero-verify "Python 3.13 is the latest stable release"` | supported / contested / likely false verdict |
| Build an evidence report | `zero-report "AI regulation news"` | rationale, source digest, warnings, next steps |
| Read a blocked page | `zero-browse "https://geo-restricted-site.com"` | page content, auto-unlocked if Web Unlocker is configured |
| Search with a specific engine | `zero-search "news" --engine bing --type news` | Bing SERP results via Bright Data |
| Serve an MCP client | `zero-mcp` | 8 tools for Claude Code, Cursor, Copilot, and any MCP-compatible runtime |

<p align="center">
  <img src="assets/terminal-demo.svg" alt="zero-context terminal demo" width="860">
</p>

## Provider Paths: Free to Production

Start free, scale when you're ready. Every path works out of the box — no configuration required for the default.

### Path 1: Free (Zero Configuration)

Works immediately after `pip install`. Uses DuckDuckGo — no API key, no account.

```bash
zero-search "Python 3.13 release" --json
```

### Path 2: Free Cross-Validated

Add a self-hosted SearXNG instance for dual-provider cross-validation — still free, no API key.

```bash
# Start SearXNG locally
./scripts/start-searxng.sh
export ZERO_SEARCH_SEARXNG_URL="http://127.0.0.1:8080"

zero-search "AI regulation" --profile free-verified --json
```

Or with Docker Compose:

```bash
cp .env.searxng.example .env
docker compose -f docker-compose.searxng.yml up -d
```

Full guide: [docs/searxng-self-hosted.md](docs/searxng-self-hosted.md).

### Path 3: Production SERP

[Bright Data](https://get.brightdata.com/h21j9xz4uxgd) provides professional-grade search across 7 engines with structured results, LLM-friendly markdown output, AI Overviews, mobile device emulation, and geo-targeting for 195 countries. New users get 5,000 free credits.

```bash
# Interactive setup wizard — tests your key and zone
zero-setup

# Or set environment variables directly
export ZERO_SEARCH_BRIGHTDATA_API_KEY="your-key"
export ZERO_SEARCH_BRIGHTDATA_ZONE="serp_api1"

# Search across different engines
zero-search "news" --provider brightdata --engine google --type news --region us-en --json
zero-search "news" --provider brightdata --engine bing --type news --region gb-en --json
zero-search "news" --provider brightdata --engine yandex --region ru-ru --json
```

Supported engines: `google`, `bing`, `duckduckgo`, `yandex`, `baidu`, `yahoo`, `naver`.

### Path 4: Production + Web Unlocker

Access blocked, CAPTCHA-protected, or geo-restricted pages. Uses the same Bright Data API key — just create a Web Unlocker zone.

```bash
# Setup wizard handles zone creation guidance
zero-setup

# Or set the zone manually
export ZERO_SEARCH_BRIGHTDATA_API_KEY="your-key"
export ZERO_SEARCH_BRIGHTDATA_ZONE="serp_api1"
export ZERO_SEARCH_BRIGHTDATA_UNLOCKER_ZONE="web_unlocker1"

# Browse automatically falls back to Web Unlocker on 403/429
zero-browse "https://protected-site.com/article" --json

# Or force Web Unlocker
zero-browse "https://protected-site.com/article" --use-unlocker always --json
```

### Path 5: Maximum Evidence

All providers active — DDGS, SearXNG, Bright Data, and Web Unlocker — for the strongest cross-validated evidence.

```bash
export ZERO_SEARCH_BRIGHTDATA_API_KEY="your-key"
export ZERO_SEARCH_SEARXNG_URL="http://127.0.0.1:8080"

zero-report "AI regulation news" --profile max-evidence --deep --json
```

## Provider Profiles

| Profile | Providers | Best for |
| --- | --- | --- |
| `free` | `ddgs` | Zero-setup local search |
| `free-verified` | `ddgs`, `searxng` | Free cross-validation |
| `production` | `brightdata` | Production reliability and geo-targeting |
| `production-unlock` | `brightdata`, `web_unlocker` | Production SERP + access blocked pages |
| `max-evidence` | `ddgs`, `searxng`, `brightdata` | Maximum provider diversity |

```bash
zero-search "FastAPI lifespan docs" --profile free-verified --goggles docs-first
zero-context "FastAPI lifespan docs" --profile free --goggles docs-first
zero-report "AI regulation news" --profile production-unlock --json
```

## MCP Server

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

For npm/npx-based MCP launchers:

```json
{
  "mcpServers": {
    "zero-api-key-web-search": {
      "command": "npx",
      "args": ["zero-api-key-web-search", "zero-mcp"]
    }
  }
}
```

Eight tools exposed:

| Tool | What it does |
| --- | --- |
| `list_providers` | Show provider status, profiles, goggles, and setup hints |
| `search_web` | Live web search with engine selection and region targeting |
| `llm_context` | Compact, citation-ready Markdown context for LLMs |
| `browse_page` | Fetch and extract page content (auto-unlocks blocked pages) |
| `verify_claim` | Evaluate whether a claim is supported, contested, or under-evidenced |
| `evidence_report` | Full evidence report with rationale, source digest, and next steps |
| `clear_cache` | Clear the response cache |
| `setup_providers` | Check provider status, test API keys, and get setup instructions |

### MCP Tool Parameters

`search_web` key parameters:
- `query` (required) — search query
- `type` — `text`, `news`, `images`, `videos`, `books` (default: `text`)
- `engine` — `google`, `bing`, `duckduckgo`, `yandex`, `baidu`, `yahoo`, `naver` (Bright Data only)
- `region` — region code, e.g. `us-en`, `zh-cn`, `wt-wt` (default: `wt-wt`)
- `profile` — provider profile name
- `goggles` — built-in reranking preset

`browse_page` key parameters:
- `url` (required) — page URL
- `format` — `markdown` or `text` (default: `markdown`)
- `use_unlocker` — `auto` (default), `always`, or `never`
- `max_chars` — max content length (default: 50000)

`setup_providers` key parameters:
- `test_brightdata_key` — test a Bright Data API key
- `test_brightdata_zone` — SERP zone name (default: `serp_api1`)
- `test_brightdata_unlocker_zone` — Web Unlocker zone name
- `test_searxng_url` — test a SearXNG instance URL

## Interactive Setup Wizard

The `zero-setup` command guides you through provider configuration, validates API keys and zones, and writes `.env` files:

```bash
# Interactive wizard
zero-setup

# Quick status check
zero-setup --status

# Test a Bright Data API key
zero-setup --test-brightdata YOUR_API_KEY

# Test a Bright Data Web Unlocker zone
zero-setup --test-brightdata-unlocker YOUR_API_KEY --unlocker-zone web_unlocker1

# Test a SearXNG instance
zero-setup --test-searxng http://localhost:8080
```

## Bright Data Integration

[Bright Data](https://get.brightdata.com/h21j9xz4uxgd) powers two production-grade capabilities:

### SERP API — Multi-Engine Search

Professional-grade search across 7 engines with structured results, LLM-friendly markdown output, AI Overviews, mobile device results, and geo-targeting for 195 countries.

```python
from zero_api_key_web_search.providers import BrightDataProvider

provider = BrightDataProvider(api_key="your-key", zone="serp_api1")

# Google (default)
results = provider.search("Python 3.13", search_type="text", region="us-en")

# Bing, Yandex, Baidu, Yahoo, Naver, DuckDuckGo
results = provider.search("AI regulation", search_type="news", engine="bing")

# Markdown output for LLM consumption
results = provider.search("climate change", data_format="markdown")
```

### Web Unlocker — Access Blocked Pages

Automatically handles CAPTCHAs, anti-bot protection, IP rotation, and JavaScript rendering. Access pages that return 403, require login, or are geo-restricted.

```python
from zero_api_key_web_search.providers import WebUnlockerProvider

provider = WebUnlockerProvider(api_key="your-key", zone="web_unlocker1")

# Get page content as markdown
result = provider.unlock("https://protected-site.com/article", data_format="markdown")
print(result["content"])  # Clean markdown of the page

# With country targeting
result = provider.unlock("https://geo-restricted.com", country="us")
```

### Auto-Fallback in browse_page

When Web Unlocker is configured, `browse_page` automatically retries blocked pages (403/429) through the unlocker:

```python
from zero_api_key_web_search.browse_page import browse

# Auto-fallback (default) — try direct, then unlocker on 403/429
result = browse("https://protected-site.com/article")

# Always use Web Unlocker
result = browse("https://protected-site.com/article", use_unlocker=True)

# Never use Web Unlocker
result = browse("https://protected-site.com/article", use_unlocker=False)
```

New Bright Data users can sign up with 5,000 free credits: <https://get.brightdata.com/h21j9xz4uxgd>

## Why This Over a Plain Search Wrapper?

| Feature | Plain search | Zero-API-Key Web Search |
| --- | --- | --- |
| Live search results | ✅ | ✅ |
| Multi-engine SERP (7 engines) | ❌ | ✅ (Bright Data) |
| News / images / videos / books | ❌ | ✅ |
| Region & time filtering | ❌ | ✅ |
| Blocked page unlocking | ❌ | ✅ (Web Unlocker) |
| Full-page text extraction | ❌ | ✅ |
| Claim verification with evidence scores | ❌ | ✅ |
| Supporting vs. conflicting evidence | ❌ | ✅ |
| Citation-ready evidence reports | ❌ | ✅ |
| Dual-provider cross-validation | ❌ | ✅ |
| API key required | Often | **Never by default** |
| Cost | Sometimes | **Free by default** |

## How Verification Works

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

This is a heuristic evidence classifier, not a proof engine. See [docs/trust-model.md](docs/trust-model.md) for details and limitations, [docs/verification-model.md](docs/verification-model.md) for signal definitions, and [docs/benchmarks.md](docs/benchmarks.md) for regression results.

## Built-in Goggles Presets

| Goggles | Effect |
| --- | --- |
| `docs-first` | Boosts docs, API, support, release-note, and official-looking sources |
| `research` | Boosts academic, institutional, paper, and study-oriented sources |
| `news-balanced` | Boosts reporting/analysis signals and demotes low-context aggregators |

You can also pass a JSON file to `--goggles` with `boost_domains`, `block_domains`, `demote_domains`, and `boost_title_terms`.

Full guide: [docs/agent-search-controls.md](docs/agent-search-controls.md).

## Platform Support

| Platform | Status | Entry point |
| --- | --- | --- |
| **CLI** | Ready | `zero-search`, `zero-context`, `zero-browse`, `zero-verify`, `zero-report`, `zero-setup` |
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

## Architecture

```
zero_api_key_web_search/
  core.py              # UltimateSearcher — search, verify, report engine
  browse_page.py       # Readability-style page extraction + Web Unlocker fallback
  mcp_server.py        # MCP server (8 tools)
  provider_setup.py    # Interactive setup wizard (zero-setup)
  cache.py             # Response caching
  transport.py         # SSL/TLS helpers
  search_web.py        # CLI: zero-search
  context.py            # CLI: zero-context
  verify_claim.py       # CLI: zero-verify
  evidence_report.py    # CLI: zero-report
  providers/
    base.py             # SearchProvider protocol (sync + async)
    ddgs.py             # DuckDuckGo provider (free, zero-config)
    searxng.py          # SearXNG provider (free, self-hosted)
    brightdata.py        # Bright Data SERP — 7 engines, markdown, AI Overviews
    web_unlocker.py      # Bright Data Web Unlocker — blocked/CAPTCHA/geo pages
  skills/
    SKILL.md            # Bundled OpenClaw skill
```

Key engineering features:

- **Circuit breaker**: Trips after 3 consecutive provider failures, auto-resets after 60s
- **Async support**: `asearch()` for concurrent provider calls via `asyncio.gather`
- **Auto-fallback**: `browse_page` retries 403/429 pages via Web Unlocker automatically
- **Multi-engine SERP**: 7 search engines (Google, Bing, DuckDuckGo, Yandex, Baidu, Yahoo, Naver)
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
python -m pytest tests/ -q           # 98 tests
ruff check zero_api_key_web_search/ tests/
pyright zero_api_key_web_search/     # 0 errors
coverage report --fail-under=80       # 85% coverage
```

## Evidence Report Example

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

## Verification for Ecosystem Reviewers

1. `zero-report "Python 3.13 stable release" --claim "Python 3.13 is the latest stable release" --deep --json`
2. [docs/ecosystem-readiness.md](docs/ecosystem-readiness.md)
3. [docs/gemini-submission-checklist.md](docs/gemini-submission-checklist.md)
4. [docs/trust-model.md](docs/trust-model.md)

## License

MIT License.