# Launch Kit

Short copy for sharing Zero-API-Key Web Search.

## One-liner

Search infrastructure for AI agents: free by default, MCP-ready, LLM-context aware, and production-grade when you opt in.

## Short Post

I built `zero-api-key-web-search`: a local search and evidence layer for AI agents.

- `zero-context` returns citation-ready context for LLMs
- `zero-verify` checks claims as supported, contested, or under-evidenced
- `zero-mcp` gives Claude/Cursor/Codex/Gemini-style clients live search tools
- no API key required by default
- optional SearXNG and Bright Data providers for stronger coverage

```bash
pip install zero-api-key-web-search
zero-context "FastAPI lifespan docs" --goggles docs-first
```

GitHub: https://github.com/wd041216-bit/zero-api-key-web-search

## Hacker News / Reddit Title Ideas

- Show HN: Zero-key web search infrastructure for AI agents
- I built an MCP-ready search and claim-verification layer for local agents
- Free-by-default web search for agents, with citation-ready LLM context

## Directory Submission Blurb

Zero-API-Key Web Search is a Python/MCP tool that gives AI agents live web search, page browsing, LLM-ready context packs, and evidence-aware claim verification. It works without API keys by default, supports free self-hosted SearXNG, and can opt into Bright Data for production-grade search.

## Demo Commands

```bash
zero-search providers
zero-context "latest Python stable release" --goggles docs-first
zero-verify "Python 3.13 is the latest stable release" --deep --json
zero-report "AI regulation news" --profile production --json
```
