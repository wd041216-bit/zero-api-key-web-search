# Agent Search Controls

Zero-API-Key Web Search now exposes three agent-facing controls inspired by production search APIs:

- provider profiles for explicit cost/reliability choices
- LLM context mode for citation-ready prompt context
- Goggles-lite for local reranking and filtering

## Provider Profiles

| Profile | Providers | Use when |
| --- | --- | --- |
| `free` | `ddgs` | You want the default zero-setup path. |
| `free-verified` | `ddgs`, `searxng` | You want free cross-validation and have SearXNG configured. |
| `production` | `brightdata` | You want production-grade reliability, structured SERP data, or geo-targeting. |
| `max-evidence` | `ddgs`, `searxng`, `brightdata` | You want the broadest provider diversity. |

Explicit `--provider` flags override `--profile`.

```bash
zero-search "Python release" --profile free-verified
zero-report "AI regulation news" --profile production --json
```

## LLM Context Mode

`zero-context` returns compact Markdown for agents and RAG flows:

```bash
zero-context "FastAPI lifespan docs" --goggles docs-first
zero-search "FastAPI lifespan docs" --context --json
```

The context pack includes retrieval metadata, provider usage, optional evidence read, source quality, freshness, and citation-ready links.

## Goggles-lite

Built-in presets:

| Preset | Behavior |
| --- | --- |
| `docs-first` | Boost docs, API, support, release-note, and official-looking sources. |
| `research` | Boost academic, institutional, paper, and study-oriented sources. |
| `news-balanced` | Boost reporting/analysis signals and demote low-context aggregators. |

You can also pass a JSON file:

```json
{
  "boost_domains": ["docs.python.org", "github.com"],
  "block_domains": ["pinterest.com"],
  "boost_title_terms": ["documentation", "release notes"],
  "boost": 0.35,
  "demote": 0.25
}
```

```bash
zero-search "python pathlib" --goggles ./goggles.json
```
