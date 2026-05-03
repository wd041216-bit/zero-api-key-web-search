# v22.0.0 Feature Coverage

This document maps each domain coverage axis to the features that address it, ensuring full traceability from axes to implementation.

## Coverage Axes

### 1. web-search
Multi-provider web search via DuckDuckGo (free), SearXNG (self-hosted), and Bright Data (production).
- `UltimateSearcher.search()` and `UltimateSearcher.asearch()`
- `search_web` MCP tool
- Provider profiles: free, default, free-verified, production, max-evidence

### 2. mcp-integration
Full MCP server exposure via stdio, with 7 tools (search_web, browse_page, verify_claim, evidence_report, llm_context, list_providers, clear_cache).
- `zero_api_key_web_search/mcp_server.py`
- Entry points: `zero-mcp`, `cross-validated-search-mcp`, `free-web-search-mcp`
- Compatible with Claude Code, Cursor, Codex, Continue, OpenClaw, Hermes, Nanobot

### 3. claim-verification
Evidence-based claim verification with decomposition, source classification, conflict detection, and page-aware augmentation.
- `UltimateSearcher.verify_claim()`
- `verify_claim` MCP tool
- Multilingual conflict markers (EN, ES, FR, DE, ZH)
- Verdict logic: supported, likely_supported, contested, likely_false, insufficient_evidence

### 4. evidence-reports
Combined search + verification with executive summary, stance buckets, source digest, and next steps.
- `UltimateSearcher.evidence_report()`
- `evidence_report` MCP tool
- Baseline comparisons: majority-vote and keyword-count

### 5. llm-context
Compact Markdown-formatted context optimized for LLM prompts with source quality and freshness badges.
- `UltimateSearcher.llm_context()`
- `llm_context` MCP tool
- Configurable max_sources and include_verification flag

### 6. provider-diversity
Cross-validation across providers: URLs appearing in multiple providers are flagged and ranked first.
- `UltimateSearcher` cross-validation logic in `search()`
- Provider profiles for different diversity levels
- Circuit breaker per provider with 3-failure threshold and 60s reset

### 7. source-quality
Domain trust tiers (gov/edu, org, com), official marker detection, snippet richness scoring, and quality text markers.
- `_estimate_source_quality()` in `core.py`
- `Source.extra["verification"]` dict with evidence_strength, classification, overlap_ratio

### 8. freshness-scoring
Time-decay scoring in 30-day buckets, date parsing across multiple formats, freshness contribution to evidence strength.
- `_estimate_freshness()` in `core.py`
- `timelimit` parameter for day/week/month/year windows
- Date normalization across 7+ formats

### 9. response-caching (NEW v22.0.0)
LRU response cache with 15-minute TTL, 50MB size cap, lazy eviction, and hit/miss/eviction statistics.
- `zero_api_key_web_search/cache.py` — `ResponseCache` class
- Cache keys for browse (URL-based) and search (query+params hash)
- `clear_cache` MCP tool for manual invalidation
- Cache stats exposed via `list_providers`
- `from_cache` flag in `browse_page` responses

### 10. markdown-extraction (NEW v22.0.0)
HTML-to-Markdown conversion preserving headings, lists, code blocks, and link structure.
- `extract_markdown()` in `browse_page.py` using `markdownify`
- `format` parameter on `browse_page` MCP tool (`markdown` default, `text` fallback)
- Both `markdown` and `text` fields always returned for backward compatibility
- Regex fallback when markdownify is not installed

### 11. redirect-safety (NEW v22.0.0)
Cross-host redirect blocking to prevent silent redirection to untrusted hosts, with max 10 same-host hops.
- `_SafeRedirectHandler` in `browse_page.py`
- `_CrossHostRedirect` exception with original_url, redirect_url, status_code
- Returns structured redirect result: `{"status": "redirect", "original_url": "...", "redirect_url": "...", "status_code": N}`
- Allows www prefix variations on same host

### 12. domain-filtering (NEW v22.0.0)
Configurable domain allowlist and blocklist via environment variables.
- `ZERO_SEARCH_ALLOW_DOMAINS` — comma-separated allowlist (if set, ONLY these domains)
- `ZERO_SEARCH_BLOCK_DOMAINS` — comma-separated blocklist
- Domain check supports subdomain matching (e.g., blocking `example.com` also blocks `sub.example.com`)
- Returns structured blocked result: `{"status": "blocked", "domain": "...", "reason": "..."}`

### 13. multi-agent-integration (NEW v22.0.0)
First-class configuration for Hermes Agent, OpenClaw, and Nanobot frameworks.
- `.hermes/plugins/zero-api-key-web-search/` — Hermes plugin with schema definitions
- `.hermes/mcp-servers.yaml` — Hermes MCP server config
- `.openclaw/skills/zero-api-key-web-search/SKILL.md` — OpenClaw skill with YAML frontmatter
- `.openclaw/openclaw.json` — OpenClaw MCP server config
- `.nanobot/nanobot.yaml` — Nanobot MCP server config + agent definition
- `.nanobot/agents/researcher.md` — Nanobot research agent with system prompt
- All frameworks connect via stdio MCP (`command: "zero-mcp"`)

### 14. pdf-extraction (NEW v22.0.0)
Optional PDF text extraction via pypdf, with graceful fallback when not installed.
- Optional dependency: `pip install zero-api-key-web-search[pdf]`
- `_extract_pdf_text()` in `browse_page.py`
- Detects `application/pdf` content type
- Returns install instruction message when pypdf is unavailable
- Page-by-page extraction with newline separation