# Claim Ledger

Public claims about Zero-API-Key Web Search, their evidence, and current status.

| Claim | Evidence | Status |
|-------|----------|--------|
| Verdict classification improves on raw search retrieval | `tests/test_verify_claim.py` regression suite, 5 verdict families | Partial — regression-only, not open-web calibrated |
| Cross-validation improves evidence quality | `core.py:_cross_validate` deduplication logic | Implemented, no benchmark fixture yet |
| Source quality heuristics correlate with trustworthiness | `core.py:_estimate_source_quality` domain-suffix + text signals | Heuristic, not empirically validated |
| Sub-claim decomposition improves compound claim accuracy | `core.py:decompose_claim` semicolon splitting | Implemented, no separate benchmark for compound vs. atomic claims |
| Zero-key default provides useful results | `providers/ddgs.py` DuckDuckGo backend | Works for common English queries; relies on upstream availability |
| MCP server exposes 5 tools | `mcp_server.py` tool definitions | All 5 tools functional: search_web, llm_context, browse_page, verify_claim, evidence_report |
| Provider profiles route to correct backends | `core.py` profile resolution | Verified for `free`, `free-verified`, `production`, `max-evidence` profiles |