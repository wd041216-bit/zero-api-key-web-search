# Zero-API-Key Web Search for OpenCode

Use Zero-API-Key Web Search when you need verified facts.

## Installation

```bash
pip install zero-api-key-web-search
```

## Commands

```bash
# Cross-validated search
zero-search "query"

# Search types
zero-search "query" --type text      # General knowledge
zero-search "query" --type news      # Current events
zero-search "query" --type images    # Visual references
zero-search "query" --type books     # Academic sources

# Time filters
zero-search "query" --type news --timelimit w

# Region-specific
zero-search "query" --region zh-cn

# JSON output
zero-search "query" --json

# Read page
zero-browse "https://example.com"
```

## Confidence Levels

| Score | Meaning | Action |
|-------|---------|--------|
| ✅ Verified | 3+ sources agree | Report as fact |
| 🟢 Likely True | 2 sources agree | Cite with note |
| 🟡 Uncertain | Single source | Flag as unverified |
| 🔴 Likely False | Contradictions | Do not use |

## When to Use

- Factual questions about events, people, dates
- Questions about recent events (< 1 year)
- Statistics, numbers, versions
- Verification of claims

## Requirements

- Python 3.10+
- `beautifulsoup4`, `lxml`, `ddgs`, `mcp>=1.1.2`
