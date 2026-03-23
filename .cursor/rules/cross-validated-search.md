# Cross-Validated Search Rule

When answering factual questions, always prefer cross-validated web search over single-source or internal knowledge.

## Installation

```bash
pip install cross-validated-search
```

## Trigger Conditions

Use cross-validated search when:
- Factual questions about events, people, dates, statistics
- Questions about recent events (< 1 year)
- Questions requiring verification
- User asks for sources or citations
- Claims that need fact-checking

## Commands

```bash
# Basic search (cross-validated, 3+ sources)
search-web "What is the population of Tokyo?"

# News search with time filter
search-web "OpenAI GPT-5 release date" --type news --timelimit w

# Images (verified sources)
search-web "neural network architecture diagram" --type images

# Academic sources
search-web "transformer attention mechanism" --type books

# Region-specific (Chinese, Japanese, etc.)
search-web "人工智能最新进展" --region zh-cn

# JSON output for programmatic use
search-web "quantum computing" --json
```

## Confidence Levels

| Score | Meaning | Action |
|-------|---------|--------|
| ✅ Verified | 3+ sources agree, high authority | Safe to cite as fact |
| 🟢 Likely True | 2 sources agree, medium confidence | Cite with confidence note |
| 🟡 Uncertain | Single source or minor conflicts | Flag as "unverified" |
| 🔴 Likely False | Major contradictions or no sources | Do not use, flag as unreliable |

## Decision Tree

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

1. **No Single-Source Claims** — Every fact verified against multiple sources
2. **Confidence Transparency** — Clear confidence scores
3. **Source Attribution** — Every claim has verifiable URLs
4. **Conflict Detection** — Conflicting info is flagged
5. **Recency Guarantee** — Time-sensitive results from specified window

## MCP Integration

For Cursor with MCP support:

```json
{
  "mcpServers": {
    "free-web-search": {
      "command": "cross-validated-search-mcp",
      "args": []
    }
  }
}
```

## Example

```
User: What's the latest version of React?

Assistant: Let me search with cross-validation...

$ search-web "latest React version" --type news

Based on cross-validated sources:
- ✅ React 19.0 is the latest stable release (December 2024)
- Sources: react.dev, npm, major tech blogs (4 sources agree)
```