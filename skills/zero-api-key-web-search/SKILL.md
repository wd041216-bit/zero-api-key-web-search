---
name: zero-api-key-web-search
version: "23.0.0"
description: >
  OpenClaw skill for source-backed web search, page reading, and evidence-aware claim checking.
  No API keys required by default; optional providers can be enabled for stronger coverage.
  v23: multi-engine SERP (7 engines), Web Unlocker for blocked pages, auto-fallback on 403/429.
homepage: https://github.com/wd041216-bit/zero-api-key-web-search
---

# Zero-API-Key Web Search for OpenClaw

This skill gives OpenClaw a practical verification workflow:

- `zero-search` for live search results (7 engines via Bright Data)
- `zero-search providers` for provider discovery
- `zero-browse` for reading pages (auto-unlocks blocked content)
- `zero-verify` for support/conflict classification
- `zero-report` for a citation-ready summary with next steps
- `zero-setup` for interactive provider configuration

## Install

```bash
pip install zero-api-key-web-search
```

## Minimum verification

```bash
zero-search "OpenAI API pricing" --type news --timelimit w
zero-search providers
zero-browse "https://docs.python.org/3/whatsnew/"
zero-verify "Python 3.13 is the latest stable release" --deep --max-pages 2 --json
zero-report "Python 3.13 stable release" --claim "Python 3.13 is the latest stable release" --deep --json
```

## Provider paths

| Profile | Providers | Best for |
| --- | --- | --- |
| `free` | ddgs | Zero-setup local search |
| `free-verified` | ddgs, searxng | Free cross-validation |
| `production` | brightdata | Production reliability and geo-targeting |
| `production-unlock` | brightdata, web_unlocker | Production SERP + blocked page access |
| `max-evidence` | ddgs, searxng, brightdata | Maximum provider diversity |

## Recommended flow

1. Run `zero-search` for factual or recent questions.
2. Use `zero-browse` on the most relevant source when snippets are not enough.
3. Use `zero-verify` when a concrete claim needs a support/conflict summary.
4. Use `zero-report` when you want a compact evidence package with citations and next steps.
5. Use `--deep` when the claim matters enough to justify page-aware verification.
6. Cite the returned URLs in the final answer.
7. Use optional `brightdata` only when configured or explicitly requested.

## Multi-engine search (Bright Data)

```bash
zero-search "AI regulation" --provider brightdata --engine google --region us-en --json
zero-search "AI regulation" --provider brightdata --engine bing --region gb-en --json
zero-search "news" --provider brightdata --engine yandex --region ru-ru --json
```

Supported engines: `google`, `bing`, `duckduckgo`, `yandex`, `baidu`, `yahoo`, `naver`.

## Web Unlocker (blocked pages)

```bash
# Auto-fallback (default) — direct fetch, then unlocker on 403/429
zero-browse "https://protected-site.com/article"

# Force Web Unlocker
zero-browse "https://protected-site.com/article" --use-unlocker always
```

## Optional Bright Data provider

```bash
# Interactive setup wizard
zero-setup

# Or set environment variables
export ZERO_SEARCH_BRIGHTDATA_API_KEY="..."
export ZERO_SEARCH_BRIGHTDATA_ZONE="serp_api1"
export ZERO_SEARCH_BRIGHTDATA_UNLOCKER_ZONE="web_unlocker1"
```

New Bright Data users can sign up at https://get.brightdata.com/h21j9xz4uxgd.

## What success looks like

- the verdict is explicit
- the result includes support and conflict scores
- `page_aware` is true when deep verification ran
- the recommended free path is `ddgs + self-hosted searxng`
- optional production path is `brightdata + web_unlocker` via `ZERO_SEARCH_BRIGHTDATA_API_KEY`
- source URLs are ready to cite

## Limits

- `zero-verify` is heuristic and evidence-aware, not a proof engine.
- The default provider path is `ddgs`.
- The recommended free upgrade path is self-hosted `searxng` via `ZERO_SEARCH_SEARXNG_URL`.
- Bright Data is optional and should not receive queries unless configured or requested.
- Conflicting sources are surfaced, not automatically reconciled.

## License

MIT License.