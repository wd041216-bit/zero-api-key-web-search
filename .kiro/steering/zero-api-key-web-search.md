# Zero-API-Key Web Search

Use Zero-API-Key Web Search when you need accurate, verified information.

## Installation

```bash
pip install zero-api-key-web-search
```

## Commands

```bash
# Cross-validated search
zero-search "What is the population of Tokyo?"

# News search
zero-search "OpenAI GPT-5 release date" --type news --timelimit w

# Academic sources
zero-search "transformer attention mechanism" --type books

# Chinese content
zero-search "人工智能最新进展" --region zh-cn
```

## Confidence Levels

| Score | Meaning |
|-------|---------|
| ✅ Verified | 3+ sources agree, high authority |
| 🟢 Likely True | 2 sources agree, medium confidence |
| 🟡 Uncertain | Single source or minor conflicts |
| 🔴 Likely False | Major contradictions or no sources |

## When to Use

- Factual questions about events, people, dates
- Questions about recent events (< 1 year)
- Statistics, numbers, versions
- Verification of claims

## Anti-Hallucination

- Multi-source verification
- Confidence scoring
- Source attribution
- Conflict detection
