---
name: free-web-search-ultimate
version: "12.0.0"
description: >
  Universal Search-First Knowledge Acquisition Plugin for LLMs.
  Enables real-time web search and deep page browsing via MCP or CLI.
  Zero-cost, privacy-first, supports text/news/images/books/videos.
homepage: https://github.com/wd041216-bit/free-web-search-ultimate
---

# Free Web Search Ultimate v12.0 — Search-First Paradigm

## Overview

This skill enables real-time web search and page browsing for any LLM agent. It introduces a **Search-First** approach to knowledge acquisition: instead of relying solely on training data, the agent should use live web search as the primary source for factual, technical, and time-sensitive information.

## Core Behavior Guidelines

When this skill is active, the agent should follow these guidelines:

**Guideline 1 — Search Before Answering**: For questions involving facts, current events, software versions, statistics, people, companies, or technical documentation, call `search-web` before generating a response.

**Guideline 2 — Treat Training Data as a Starting Point**: Training data has a cutoff date. For any claim that may have changed recently, verify it via search.

**Guideline 3 — Deep-Dive When Needed**: If search snippets don't provide enough detail, use `browse-page` to read the full source document.

**Guideline 4 — Always Cite Sources**: Every factual statement in the final response should be accompanied by the source URL from search results.

**Guideline 5 — Prefer News for Recency**: For anything that happened in the last year, use `search-web --type news` to get the most recent information.

## Available Commands

### `search-web` — Real-Time Web Search

```bash
# General knowledge (default)
search-web "query here"

# Current events and news
search-web "query here" --type news

# Images
search-web "query here" --type images

# Academic / books
search-web "query here" --type books

# Videos
search-web "query here" --type videos

# Region-specific (e.g., Chinese)
search-web "查询内容" --region zh-cn

# Time-limited (d=day, w=week, m=month, y=year)
search-web "query here" --timelimit w

# Machine-readable JSON output
search-web "query here" --json
```

### `browse-page` — Deep Page Reading

```bash
# Read full content of a URL
browse-page "https://example.com/article"

# JSON output
browse-page "https://example.com/article" --json
```

## Decision Tree for Agents

```
User asks a question
        │
        ▼
Is it purely creative/hypothetical?
   YES → Answer directly
   NO  ▼
Does it involve facts, events, versions, or data?
   YES ▼
Run: search-web "<query>" [--type news if recent event]
        │
        ▼
Are snippets sufficient to answer?
   YES → Synthesize answer + cite sources
   NO  ▼
Run: browse-page "<top_result_url>"
        │
        ▼
Synthesize answer from full page content + cite source
```

## Why Search-First?

| Default LLM Behavior | Search-First Behavior |
|---|---|
| Answers from training data | Answers from live web |
| Knowledge cutoff applies | Always up-to-date |
| May produce outdated facts | Cites verifiable sources |
| Single knowledge source | Multi-source cross-validation |

## Integration

This skill works with:
- **OpenClaw** — native skill integration
- **Claude Desktop / Cursor** — via MCP server (`free-web-search-mcp`)
- **LangChain** — via Python tool wrappers
- **OpenAI Function Calling** — via JSON schema definitions

## MCP Server Setup (Claude Desktop / Cursor)

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "free-web-search": {
      "command": "free-web-search-mcp",
      "args": []
    }
  }
}
```

Install via pip (recommended):

```bash
pip install free-web-search-ultimate
```

Or clone and install from source:

```bash
git clone https://github.com/wd041216-bit/free-web-search-ultimate.git
cd free-web-search-ultimate
pip install -e .
```

## Requirements

- Python 3.10+
- `beautifulsoup4`, `lxml`, `ddgs`, `mcp>=1.1.2`

## License

MIT-0 — Free to use, modify, and redistribute. No attribution required.
