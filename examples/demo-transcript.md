# Demo Transcript

Use this as a copy/paste demo for README snippets, launch posts, and quick videos.

## LLM Context

```bash
$ zero-context "FastAPI lifespan docs" --goggles docs-first

# Search context: FastAPI lifespan docs

## Retrieval
- Search type: text
- Confidence: MEDIUM
- Providers used: ddgs
- Provider profile: default
- Goggles: applied (boosted=2, blocked=0)

## Evidence read
- Verdict: likely_supported
- Confidence: MEDIUM
- Support score: 0.91
- Conflict score: 0.00
- Domain diversity: 2

## Sources
1. [FastAPI lifespan docs](https://fastapi.tiangolo.com/advanced/events/)
   - quality=high | freshness=unknown | cite-ready URL
2. [Application events reference](https://fastapi.tiangolo.com/)
   - docs-first reranked technical docs above generic pages

## Use guidance
- Cite sources directly for factual claims.
- Treat low provider or domain diversity as a reason to hedge.
- Surface conflict explicitly when support and conflict are both meaningful.
```

## Provider Discovery

```bash
$ zero-search providers

Available providers

ddgs         ready            free default        Zero-setup DuckDuckGo-backed search.
searxng      not_configured   free self-hosted    Free second provider for cross-validation.
brightdata   not_configured   production optional Production-grade SERP provider.

Profiles
- free: ddgs
- free-verified: ddgs, searxng
- production: brightdata
- max-evidence: ddgs, searxng, brightdata
```

## MCP

```bash
$ zero-mcp
```

Then configure your MCP client with:

```json
{
  "mcpServers": {
    "zero-api-key-web-search": {
      "command": "zero-mcp"
    }
  }
}
```
