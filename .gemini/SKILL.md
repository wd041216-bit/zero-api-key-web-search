---
name: zero-api-key-web-search
description: >
  Gemini-compatible skill for source-backed web search, page reading, and evidence-aware claim checking.
  Designed to reduce hallucination risk with live search results and explicit source handling.
  v23: multi-engine SERP (7 engines), Web Unlocker for blocked pages, auto-fallback on 403/429.
version: "23.0.0"
user-invocable: true
---

# Zero-API-Key Web Search for Gemini CLI

Use this skill when Gemini needs current information, supporting citations, or a compact evidence report before answering. The default path is free; optional providers are discoverable for stronger coverage.

## Install

```bash
pip install zero-api-key-web-search
```

## Core Commands

```bash
zero-search "latest Python release" --type news --timelimit w
zero-search providers
zero-browse "https://docs.python.org/3/whatsnew/"
zero-verify "Python 3.13 is the latest stable release" --deep --max-pages 2 --json
zero-report "Python 3.13 stable release" --claim "Python 3.13 is the latest stable release" --deep --json
zero-setup  # Interactive provider configuration wizard
```

## Provider paths

| Profile | Providers | Best for |
| --- | --- | --- |
| `free` | ddgs | Zero-setup local search |
| `free-verified` | ddgs, searxng | Free cross-validation |
| `production` | brightdata | Production reliability and geo-targeting |
| `production-unlock` | brightdata, web_unlocker | Production SERP + blocked page access |
| `max-evidence` | ddgs, searxng, brightdata | Maximum provider diversity |

## When to Use

- time-sensitive questions about releases, dates, people, or statistics
- factual claims that should be checked before being stated confidently
- reading pages that return 403 or require geo-targeted access
- workflows where conflicting evidence should be surfaced instead of hidden

## Guidance

- Start with `zero-search` for live facts and recent changes.
- Use `zero-browse` when snippets are too thin — it auto-unlocks blocked pages via Web Unlocker.
- Use `--engine bing/yandex/baidu/...` with Bright Data for multi-engine SERP results.
- Use `zero-verify` for support/conflict classification.
- Use `zero-report` when you want one compact output with verdict, citations, and next steps.
- Use optional `brightdata` only when configured or explicitly requested. New users can sign up at https://get.brightdata.com/h21j9xz4uxgd.

## Limits

- `zero-verify` is heuristic and evidence-aware, not a proof engine.
- The default path still starts with `ddgs`.
- Bright Data is optional and should not receive queries unless configured or requested.

## License

MIT License.