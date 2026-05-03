---
name: zero-api-key-web-search
description: Free web search with evidence verification and source citations for AI agents
version: 22.0.0
url: https://github.com/wd041216-bit/zero-api-key-web-search
user-invocable: true
command-dispatch: tool
command-tool: search_web
metadata: {"openclaw":{"emoji":"\U0001F50D","requires":{"bins":["zero-mcp"]}}}
---

# Zero-API-Key Web Search

Free web search for AI agents. No API keys required for default usage (DuckDuckGo).

## Available Tools

### search_web
Search the web for real-time information, news, images, books, or videos.
- `query` (required): The search query
- `type`: text, news, images, videos, books (default: text)
- `region`: Region code (default: wt-wt)
- `timelimit`: d (day), w (week), m (month), y (year)
- `providers`: Optional provider list: ddgs, searxng, brightdata
- `profile`: free, default, free-verified, production, max-evidence
- `goggles`: Reranking preset: docs-first, research, news-balanced

### browse_page
Fetch and extract content from a URL. Returns Markdown by default.
- `url` (required): The URL to read
- `max_chars`: Max characters to extract (default: 50000)
- `format`: markdown or text (default: markdown)
- `prompt`: Optional extraction hint for focused retrieval

### verify_claim
Evaluate whether a factual claim is supported, contested, or under-evidenced.
- `claim` (required): The claim to verify
- `with_pages` / `deep`: Fetch top pages for deeper analysis
- `max_pages`: Max pages to fetch (default: 3)

### evidence_report
Generate a citation-ready evidence report combining search + verification.
- `query` (required): Search query to gather evidence
- `claim`: Optional explicit claim to verify
- `max_sources`: Max sources in digest (default: 5)

### llm_context
Build compact, citation-ready Markdown context for LLMs.
- `query` (required): Search query to ground
- `max_sources`: Max sources (default: 8)
- `include_verification`: Include evidence verification (default: true)

### list_providers
List available search providers, profiles, and cache statistics.

### clear_cache
Clear the response cache for fresh results.

## Setup

```bash
pip install zero-api-key-web-search
```

For PDF extraction support:
```bash
pip install zero-api-key-web-search[pdf]
```

## MCP Configuration

Add to your OpenClaw config (`openclaw.json`):

```json
{
  "mcp": {
    "servers": {
      "zero-search": {
        "command": "zero-mcp",
        "args": []
      }
    }
  }
}
```

## Confidence Levels

| Tool | High Confidence | Medium Confidence | Low Confidence |
|------|---------------|-------------------|---------------|
| search_web | Multiple sources agree | Single authoritative source | Single weak source |
| verify_claim | supported/likely_supported | contested | likely_false/insufficient_evidence |
| browse_page | Official docs, well-structured pages | Blog posts, forums | User-generated, no attribution |