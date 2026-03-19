---
name: free-web-search-ultimate
version: "14.0.0"
description: >
  Cross-Validated Web Search for Hallucination-Free LLM Responses.
  Multi-source verification prevents AI hallucinations.
  Zero-cost, privacy-first, supports text/news/images/books/videos.
homepage: https://github.com/wd041216-bit/free-web-search-ultimate
---

# Free Web Search Ultimate v14.0 — Cross-Validated Search

## Overview

**The only search skill that actively prevents LLM hallucinations through multi-source cross-validation.**

When an LLM answers a question, it may fabricate facts, hallucinate details, or rely on outdated training data. This skill solves that problem by:

1. **Fetching multiple independent sources** from the web
2. **Cross-validating facts across sources** to identify consensus
3. **Providing confidence scores** (✅ Verified / 🟢 Likely True / 🟡 Uncertain / 🔴 Likely False)
4. **Citing all sources** so users can verify claims

## Why Cross-Validation Matters

| Problem | Traditional LLM | With Cross-Validation |
|---------|----------------|----------------------|
| Fabricated facts | ❌ LLM may invent details | ✅ Only claims supported by multiple sources |
| Outdated knowledge | ❌ Training data cutoff | ✅ Real-time web data |
| Single-source bias | ❌ Depends on one source | ✅ Multiple independent sources |
| No verification | ❌ User must trust blindly | ✅ Confidence score + citations |

## Core Behavior Guidelines

**Guideline 1 — Multi-Source Fetch**: Always fetch from 3+ independent sources for factual claims.

**Guideline 2 — Cross-Validation**: Verify facts appear in at least 2 sources before marking as ✅ Verified.

**Guideline 3 — Confidence Scoring**: Assign confidence levels based on source agreement:
- ✅ **Verified**: 3+ sources agree, high-authority sources
- 🟢 **Likely True**: 2 sources agree, medium confidence
- 🟡 **Uncertain**: Single source or conflicting reports
- 🔴 **Likely False**: No sources or major contradictions

**Guideline 4 — Always Cite**: Every factual statement must include source URLs.

**Guideline 5 — Prefer News for Recency**: For events within the last year, use `--type news` for the most current data.

## Available Commands

### `search-web` — Cross-Validated Web Search

```bash
# General knowledge (3+ sources, cross-validated)
search-web "What is the population of Tokyo?"

# News search with time filter
search-web "OpenAI GPT-5 release date" --type news --timelimit w

# Images (verified sources)
search-web "neural network architecture diagram" --type images

# Books and academic sources
search-web "transformer attention mechanism" --type books

# Region-specific (Chinese, Japanese, etc.)
search-web "人工智能最新进展" --region zh-cn

# JSON output for programmatic use
search-web "quantum computing" --json
```

### `browse-page` — Deep Page Reading

```bash
# Read full content of a URL
browse-page "https://arxiv.org/abs/2303.08774"

# JSON output
browse-page "https://example.com/article" --json
```

## Confidence Scoring System

| Score | Meaning | Action |
|-------|---------|--------|
| ✅ Verified | 3+ sources agree, high authority | Safe to cite as fact |
| 🟢 Likely True | 2 sources agree, medium confidence | Cite with confidence note |
| 🟡 Uncertain | Single source or minor conflicts | Flag as "unverified" |
| 🔴 Likely False | Major contradictions or no sources | Do not use, flag as unreliable |

## Decision Tree for Agents

```
User asks a factual question
        │
        ▼
Is it creative/hypothetical?
   YES → Answer directly (no search needed)
   NO  ▼
Does it involve facts, events, versions, or data?
   YES ▼
Run: search-web "<query>" [--type news if recent]
        │
        ▼
What is the confidence score?
   ┌─────────────────────────────────────────────────────────┐
   │ ✅ Verified    → Report as fact, cite all sources       │
   │ 🟢 Likely True → Report with confidence, cite sources   │
   │ 🟡 Uncertain   → Report with caveat, suggest verification│
   │ 🔴 Likely False→ Do not use, explain contradictions      │
   └─────────────────────────────────────────────────────────┘
        │
        ▼
Are there conflicting sources?
   YES → Present both viewpoints with citations
   NO  → Synthesize answer with unified citation
```

## Anti-Hallucination Guarantees

When using this skill, you get:

1. **No Single-Source Claims** — Every fact is verified against multiple sources
2. **Confidence Transparency** — You know exactly how confident the system is
3. **Source Attribution** — Every claim comes with verifiable URLs
4. **Conflict Detection** — Conflicting information is flagged, not hidden
5. **Recency Guarantee** — For time-sensitive topics, results are from the specified time window

## Supported Search Types

| Type | Use Case | Cross-Validation |
|------|----------|-------------------|
| `text` | General knowledge, facts | ✅ Multi-source agreement |
| `news` | Current events, recent updates | ✅ Multiple news sources |
| `images` | Visual references, diagrams | ✅ Verified image sources |
| `videos` | Tutorials, presentations | ✅ Multiple video platforms |
| `books` | Academic, in-depth topics | ✅ Cross-book verification |

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