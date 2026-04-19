# Ecosystem Readiness

This page is the fast audit surface for platform reviewers, skill indexers, and ecosystem maintainers.

## Positioning

Zero-API-Key Web Search is an evidence-aware verification layer for AI agents.

It is not just a search wrapper because it combines:

- live search
- page reading
- claim checking
- a flagship evidence-report workflow
- provider-aware metadata
- optional page-aware verification

## Compatibility names

| Surface | Name |
| --- | --- |
| Repository | `zero-api-key-web-search` |
| PyPI package | `zero-api-key-web-search` |
| Python module | `zero_api_key_web_search` |
| CLI | `search-web`, `browse-page`, `verify-claim`, `evidence-report` |
| MCP server | `zero-api-key-web-search-mcp` |

## Current maturity

- CLI: production-ready
- MCP surface: available and smoke-tested
- Provider model: abstraction in place, `ddgs` active by default, and self-hosted `searxng` is the recommended free second provider
- Claim verification: heuristic but explainable
- Page-aware verification: available as an opt-in path

## Minimum verification flow

```bash
pip install zero-api-key-web-search
search-web "Python 3.13 release" --json
verify-claim "Python 3.13 is the latest stable release" --deep --max-pages 2 --json
evidence-report "Python 3.13 stable release" --claim "Python 3.13 is the latest stable release" --deep --json
zero-api-key-web-search-mcp
```

## Platform entry points

| Platform | Entry |
| --- | --- |
| Gemini | [GEMINI.md](../GEMINI.md), [`.gemini/SKILL.md`](../.gemini/SKILL.md) |
| OpenClaw | [`zero_api_key_web_search/skills/SKILL.md`](../zero_api_key_web_search/skills/SKILL.md) |
| Codex | [`.codex/SKILL.md`](../.codex/SKILL.md) |
| Claude Code | [`.claude-plugin/SKILL.md`](../.claude-plugin/SKILL.md) |
| Copilot | [`.github/copilot/instructions.md`](../.github/copilot/instructions.md) |

## What reviewers should know

- The default provider path is `ddgs`.
- The recommended free upgrade path is self-hosted `searxng` via `ZERO_SEARCH_SEARXNG_URL`.
- `verify-claim` is heuristic and evidence-aware, not a fact-level proof engine.
- `evidence-report` is the recommended reviewer-facing entry point when a platform wants a compact evidence artifact.
- `--deep` enables page-aware verification by reading top evidence sources.
- TLS verification is enabled by default.

## Supporting docs

- [Trust model](./trust-model.md)
- [Evidence report](./evidence-report.md)
- [Self-hosted SearXNG](./searxng-self-hosted.md)
- [Why not just search](./why-not-just-search.md)
- [`scripts/start-searxng.sh`](../scripts/start-searxng.sh)
- [`scripts/validate-free-path.sh`](../scripts/validate-free-path.sh)
- [Benchmark plan](./benchmark-plan.md)
- [Release guide](./release.md)
- [CLI quickstart](../examples/cli-quickstart.md)
- [Gemini example](../examples/gemini.md)
- [OpenClaw example](../examples/openclaw.md)

## Next milestones

1. strengthen multi-provider aggregation and provider-specific tests
2. improve page-aware verification beyond keyword heuristics
3. publish benchmark and regression plans with broader real-world fixtures
4. expose a more stable structured MCP contract around evidence reports
