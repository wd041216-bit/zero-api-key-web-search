# Agent Developer Guide

Zero-API-Key Web Search is a local search and evidence layer for AI agents.

Use it when an agent needs current information, citations, page text, provider-aware retrieval, or a quick support/conflict read before answering.

## Install

```bash
pip install zero-api-key-web-search
```

Node-based agent toolchains can use the npm wrapper:

```bash
npm install -g zero-api-key-web-search
npx zero-api-key-web-search zero-context "FastAPI lifespan docs" --goggles docs-first
```

## Choose the Right Command

| Need | Command |
| --- | --- |
| Search links and snippets | `zero-search "query"` |
| Give an LLM grounded context | `zero-context "query"` |
| Read a specific page | `zero-browse "https://example.com"` |
| Check whether a claim is supported | `zero-verify "claim"` |
| Produce a citation-ready evidence artifact | `zero-report "query" --claim "claim"` |
| Serve tools to an MCP client | `zero-mcp` |

## MCP Setup

```json
{
  "mcpServers": {
    "zero-api-key-web-search": {
      "command": "zero-mcp"
    }
  }
}
```

For npm/npx launchers:

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

## Recommended Agent Patterns

### 1. Search-first grounding

Run `zero-context` before answering current, technical, legal, medical, financial, or version-sensitive questions.

```bash
zero-context "latest Python stable release" --goggles docs-first
```

### 2. Claim verification

Use `zero-verify` when the user asks whether something is true or when a generated answer contains a factual claim that might be stale.

```bash
zero-verify "Python 3.13 is the latest stable release" --deep --json
```

### 3. Provider-aware escalation

Start free, then escalate only when the task needs stronger coverage:

```bash
zero-search "AI regulation news" --profile free
zero-search "AI regulation news" --profile free-verified
zero-search "AI regulation news" --profile production
```

## Production Notes

- Default mode uses free upstreams and requires no API key.
- Add SearXNG for free cross-provider validation.
- Add Bright Data for production reliability, geo-targeting, and structured SERP evidence.
- Do not treat heuristic confidence as probability. Use it as a retrieval and evidence-quality signal.
