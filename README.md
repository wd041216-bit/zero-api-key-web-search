<div align="center">
  <h1>ZeroSieve</h1>
  <p><strong>Zero-key web search for AI agents — with a System-1 sieve.</strong></p>
  <p><em>Batch-filter, rerank and verify evidence locally at 100+ decisions/sec. Free by default, MCP-ready, production-grade when you opt in.</em></p>

  <br>

  ![Python](https://img.shields.io/badge/python-3.10%2B-blue)
  ![MCP](https://img.shields.io/badge/MCP-Ready-0f766e.svg)
  ![License](https://img.shields.io/badge/license-MIT-green.svg)
</div>

---

## Why ZeroSieve

An agent that searches the raw web pays for everything it reads: context tokens, latency, and attention spread over SEO noise. ZeroSieve puts a **sieve between search and the agent**:

1. **Search** the web with zero API keys (DuckDuckGo by default, self-hosted SearXNG for cross-validation, optional Bright Data for production SERP + Web Unlocker).
2. **Sieve** the results through [Laya](https://huggingface.co/convaiinnovations/laya) — an open-weight (Apache-2.0), non-autoregressive *decision model* that scores every result for relevance in a **single forward pass (~35 ms on GPU, 100–330 questions/sec batched)** with calibrated probabilities. It never generates text, so there is nothing to parse and nothing to hallucinate.
3. **Verify** claims with probabilistic stance classification (support / conflict / neutral per source) instead of pure keyword matching, then emit citation-ready evidence reports.

Every stage degrades gracefully: no Laya installed? The pipeline falls back to the lexical heuristic verifier and still works — Laya is an accelerant, not a dependency.

```
 query ──► providers ──► cross-validate ──► ┌─────────┐ ──► LLM context pack
                                           │  LAYA   │      (citations only)
                                           │  SIEVE  │
                 noise ───────────────────►└─────────┘ ──► verify_claim
                 (dropped pre-context)                    (probabilistic stance)
```

## 30-Second Setup

```bash
pip install zerosieve          # free search, no API key, no model download

zs-search "Python 3.13 release" --json
zs-verify "Python 3.13 is the latest stable release" --deep --json
zs-report "Python 3.13 stable release" --claim "Python 3.13 is the latest stable release" --json
```

Legacy `zero-*` command names from the upstream project keep working.

## Add the Sieve (Optional, ~800 MB, Fully Local)

```bash
pip install "zerosieve[laya]"   # pulls laya + torch

# Relevance-filter every search result before it reaches your agent
zs-search "react state management" --laya --laya-threshold 0.6 --json

# Probabilistic stance verification (laya-stance-v1 model)
zs-verify "Python 3.13 is the latest stable release" --laya --json

# Both, in the flagship evidence report
zs-report "gpt-5 release" --claim "GPT-5 is released" --laya --deep --json
```

On Apple Silicon it runs on MPS; on NVIDIA GPUs on CUDA; anywhere on CPU (slower but works).
Behind a network that can't reach Hugging Face? `export HF_ENDPOINT=https://hf-mirror.com`.

### What Laya does inside the pipeline

| Stage | Question asked (one forward pass per item) | Effect |
| --- | --- | --- |
| `--laya` on search/context | *"Is this result relevant and informative for the query?"* | drops noise **before** it burns context tokens |
| `--laya` on verify/report | *"Does this text support the claim?"* + *"Does it state or imply the claim is false?"* | replaces regex conflict markers and keyword-overlap cutoffs with calibrated probabilities |

The verification blend becomes `0.55 × neural stance + 0.35 × source quality + 0.10 × freshness` (vs. the lexical model's `0.45 × keyword overlap + …`). The result payload keeps the full lexical sidecar so you can compare both classifiers on your own data.

### Checkpoints

| Subfolder | Backbone | Best at |
| --- | --- | --- |
| root (default) | ModernBERT-large 421M | English text |
| `multilingual` | mmBERT-base 322M | 100+ languages, ~2× faster |
| `typed-decisions` | ModernBERT-large 421M | workflow-tuned decisions |

```bash
zs-verify "..." --laya --laya-subfolder multilingual   # non-English claims
```

## MCP Server (8 tools)

```json
{
  "mcpServers": {
    "zerosieve": {
      "command": "zs-mcp",
      "args": []
    }
  }
}
```

`search_web`, `llm_context`, `browse_page`, `verify_claim`, `evidence_report`, `list_providers`, `clear_cache`, `setup_providers` — the first four accept `"laya": true` and `"laya_threshold"` so a Claude/Cursor/any-MCP agent can opt into the sieve per call.

## Provider Paths: Free to Production

**Path 1 — Free (zero configuration).** DuckDuckGo, no account:

```bash
zs-search "Python 3.13 release" --json
```

**Path 2 — Free cross-validated.** Self-hosted SearXNG for dual-provider corroboration (see [docs/searxng-self-hosted.md](docs/searxng-self-hosted.md)):

```bash
./scripts/start-searxng.sh
export ZERO_SEARCH_SEARXNG_URL="http://127.0.0.1:8080"
zs-search "AI regulation" --profile free-verified --json
```

**Path 3 — Production SERP.** [Bright Data](https://get.brightdata.com/h21j9xz4uxgd) for 7 engines (Google, Bing, DuckDuckGo, Yandex, Baidu, Yahoo, Naver), geo-targeting, structured results:

```bash
zs-setup   # interactive wizard
zs-search "news" --provider brightdata --engine google --type news --region us-en --json
```

**Path 4 — Production + Web Unlocker.** 403/429/CAPTCHA/geo-blocked pages auto-retried through the Web Unlocker on `zs-browse`.

## Engineering

- **Circuit breaker** per provider (3 consecutive failures → 60 s cooldown)
- **Response cache** for searches and pages, `clear_cache` included
- **Async + threaded** provider fan-out; goggles-style reranking presets (`docs-first`, `research`, `news-balanced`)
- **Claim decomposition** for compound statements, sub-claim verdicts
- **Page-aware verification** (`--deep`): fetch top pages and re-score
- **Graceful degradation** everywhere: Laya missing → lexical verifier; provider down → next provider; page blocked → unlocker; unlocker off → snippet-only
- 111 tests passing (`python -m pytest tests/ -q`)

## Honest Limits

Read [docs/trust-model.md](docs/trust-model.md) before trusting any verdict. The short version:

- The lexical verifier (`evidence-aware-heuristic-v3`) is pattern-matching, not entailment — it is transparent and fast, and blind to paraphrase, negation scope, and mismatched numbers. Laya mode (`laya-stance-v1`) fixes the *class* of failure, not the *possibility* of failure.
- **Laya ships over-confident.** Upstream measured mean ECE 0.466 → 0.081 only *after* per-domain temperature refitting. Our defaults (threshold 0.5) are reasonable, not calibrated — sweep `--laya-threshold` against a small labeled set from your domain before production use.
- **Laya's base checkpoints are a fast base to specialise, not a zero-shot oracle** (upstream's own typed-decisions benchmark: 0.362 zero-shot vs 0.766 fine-tuned; XNLI-style tasks are much stronger). For high-stakes domains, fine-tune the open checkpoint on your workflow and drop it in via `--laya-model` / `--laya-subfolder`.
- High-cardinality option sets (>20 options per question) are Laya's weak spot; ZeroSieve only asks 1–2-option yes/no questions per item, which stays in its comfort zone.
- Verification quality still depends on what search returns: no web footprint → `insufficient_evidence`, by design.

## Attribution

ZeroSieve is built on [zero-api-key-web-search](https://github.com/wd041216-bit/zero-api-key-web-search) (MIT) by wd041216-bit — the provider abstraction, verification pipeline, MCP server and CLI surface are its work. The Laya sieve integration and rebrand are the delta. [Laya](https://huggingface.co/convaiinnovations/laya) is by Convai Innovations (Apache-2.0).

## License

MIT — see [LICENSE](LICENSE).
