# Zero-API-Key Web Search for OpenCode

Use cross-validated search when you need verified facts.

## Installation

```bash
pip install zero-api-key-web-search
```

## Commands

```bash
# Cross-validated search
search-web "query"

# Search types
search-web "query" --type text      # General knowledge
search-web "query" --type news      # Current events
search-web "query" --type images    # Visual references
search-web "query" --type books     # Academic sources

# Time filters
search-web "query" --type news --timelimit w

# Region-specific
search-web "query" --region zh-cn

# JSON output
search-web "query" --json

# Read page
browse-page "https://example.com"
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