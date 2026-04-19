---
name: zero-api-key-web-search
description: >
  Zero-API-Key Web Search for AI agents.
  Use multi-source search, confidence scoring, and citations for factual queries.
version: "18.0.0"
---

# Zero-API-Key Web Search for Continue

Work like a researcher: verify factual claims with multiple sources before answering.

## Installation

```bash
pip install zero-api-key-web-search
```

## Commands

```bash
zero-search "What is the population of Tokyo?"
zero-search "OpenAI GPT-5 release date" --type news --timelimit w
zero-search "neural network architecture diagram" --type images
zero-search "人工智能最新进展" --region zh-cn
zero-browse "https://arxiv.org/abs/2303.08774"
```

## When to Use

- Factual questions about events, people, dates, releases, or statistics
- Recent information that may have changed since model training
- Claims that need citations or cross-checking
- Questions where conflicting sources should be surfaced instead of hidden

## Confidence Levels

| Score | Meaning | Action |
|-------|---------|--------|
| ✅ Verified | 3+ sources agree, high authority | Safe to cite as fact |
| 🟢 Likely True | 2 sources agree, medium confidence | Cite with a confidence note |
| 🟡 Uncertain | Single source or conflicting reports | Flag as unverified |
| 🔴 Likely False | Major contradictions or no support | Do not present as fact |

## License

MIT License.
