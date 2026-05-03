"""Hermes tool handlers for zero-api-key-web-search.

Delegates all calls to the MCP server via the hermes MCP integration.
When running through Hermes, tools are auto-discovered from the MCP server
configured in .hermes/mcp-servers.yaml. This module provides fallback
handlers for direct invocation.
"""

import json


def search_web(args: dict, **kwargs) -> str:
    """Search the web. Delegates to MCP server."""
    # When running through Hermes MCP, tools are auto-discovered.
    # This handler is a fallback for direct plugin invocation.
    from zero_api_key_web_search.core import UltimateSearcher
    searcher = UltimateSearcher()
    answer = searcher.search(
        query=args["query"],
        search_type=args.get("type", "text"),
        region=args.get("region", "wt-wt"),
        timelimit=args.get("timelimit"),
        providers=args.get("providers"),
        profile=args.get("profile"),
        goggles=args.get("goggles"),
    )
    return json.dumps({
        "query": answer.query,
        "answer": answer.answer,
        "sources": [{"title": s.title, "url": s.url, "snippet": s.snippet} for s in answer.sources[:10]],
    }, ensure_ascii=False)


def browse_page(args: dict, **kwargs) -> str:
    """Browse a page. Delegates to MCP server."""
    from zero_api_key_web_search.browse_page import browse
    result = browse(
        url=args["url"],
        max_chars=args.get("max_chars", 50000),
        format=args.get("format", "markdown"),
        prompt=args.get("prompt"),
    )
    return json.dumps(result, ensure_ascii=False)


def verify_claim(args: dict, **kwargs) -> str:
    """Verify a claim. Delegates to MCP server."""
    from zero_api_key_web_search.core import UltimateSearcher
    searcher = UltimateSearcher()
    v = searcher.verify_claim(
        claim=args["claim"],
        region=args.get("region", "wt-wt"),
        timelimit=args.get("timelimit"),
        providers=args.get("providers"),
        profile=args.get("profile"),
        goggles=args.get("goggles"),
        include_pages=args.get("with_pages", False) or args.get("deep", False),
        deep=args.get("deep", False),
        max_pages=args.get("max_pages", 3),
    )
    return json.dumps({
        "claim": v.claim,
        "verdict": v.verdict,
        "confidence": v.confidence,
        "summary": v.summary,
    }, ensure_ascii=False)