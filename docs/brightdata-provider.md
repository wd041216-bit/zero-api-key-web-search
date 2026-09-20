# Bright Data Provider

Zero-API-Key Web Search remains free and zero-key by default. Bright Data is an optional production provider for agents that need higher reliability, structured SERP data, geo-targeted results, or stronger evidence diversity.

## Setup

```bash
export ZERO_SEARCH_BRIGHTDATA_API_KEY="..."
# Optional if your Bright Data SERP zone is not named web_search:
export ZERO_SEARCH_BRIGHTDATA_ZONE="web_search"

zero-search providers
```

New Bright Data users can sign up at <https://get.brightdata.com/h21j9xz4uxgd>.

## Usage

```bash
zero-search "AI regulation news" \
  --provider brightdata \
  --type news \
  --region us-en \
  --json

zero-report "Tesla Q1 2026 deliveries" \
  --claim "Tesla deliveries increased year over year" \
  --provider ddgs \
  --provider brightdata \
  --deep \
  --json
```

## Environment Variables

| Variable | Purpose |
| --- | --- |
| `ZERO_SEARCH_BRIGHTDATA_API_KEY` | Bright Data API key. Alias env vars: `BRIGHTDATA_API_KEY`, `BRIGHT_DATA_API_KEY`. |
| `ZERO_SEARCH_BRIGHTDATA_ZONE` | Bright Data SERP zone. Defaults to `web_search`. Alias env vars: `BRIGHTDATA_SERP_ZONE`, `BRIGHT_DATA_SERP_ZONE`. |
| `ZERO_SEARCH_BRIGHTDATA_COUNTRY` | Optional explicit two-letter country code for geo-targeting. |
| `ZERO_SEARCH_BRIGHTDATA_API_URL` | Optional override for the Bright Data request endpoint. |

## Behavior

- Bright Data is not used unless it is configured or explicitly requested with `--provider brightdata`.
- If the provider is requested without an API key, the tool returns a setup hint instead of silently falling back.
- `zero-search providers` and MCP `list_providers` show Bright Data alongside the free providers.
- Evidence reports recommend Bright Data only when provider diversity, geo-targeting, or production reliability would strengthen the result.
