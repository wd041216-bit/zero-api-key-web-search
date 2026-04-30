# Abstract

Zero-API-Key Web Search is a local-first, MCP-native search and evidence-verification toolkit for AI agents. It provides live web search, LLM-optimized context extraction, claim verification with weighted evidence scoring, and citation-ready evidence reports — all without requiring an API key by default. The verification model (`evidence-aware-heuristic-v3`) classifies sources as supporting, conflicting, or neutral using keyword overlap, domain-quality heuristics, freshness, and optional page-aware rescoring. This project does not perform fact-level proof or logical entailment; it is a signal amplifier for agent grounding decisions.

**Research Question**: Can heuristic evidence scoring and source-quality weighting reduce ungrounded agent outputs compared to raw search retrieval?

**Key Result**: The heuristic model achieves 98/98 regression tests passing across 5 verdict families (supported, likely_supported, contested, likely_false, insufficient_evidence), outperforming both majority-vote and keyword-count baselines on contested and likely_false claims where source quality weighting differentiates.