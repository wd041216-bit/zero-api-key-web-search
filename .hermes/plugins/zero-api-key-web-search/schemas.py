"""Tool schemas for zero-api-key-web-search Hermes plugin.

These schemas describe the tools available via the MCP server.
Hermes uses these for tool discovery when the MCP server is not reachable.
"""

SEARCH_WEB = {
    "name": "search_web",
    "description": "Search the web for real-time information, news, images, books, or videos.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query."},
            "type": {"type": "string", "enum": ["text", "news", "images", "videos", "books"], "description": "Type of search. Default: text."},
            "region": {"type": "string", "description": "Region code (default: wt-wt)."},
            "timelimit": {"type": "string", "enum": ["d", "w", "m", "y", ""], "description": "Time limit for results."},
            "providers": {"type": "array", "items": {"type": "string"}, "description": "Provider list, e.g. ['ddgs', 'searxng', 'brightdata']."},
            "profile": {"type": "string", "enum": ["free", "default", "free-verified", "production", "max-evidence"]},
            "goggles": {"type": "string", "description": "Goggles preset for reranking."},
        },
        "required": ["query"],
    },
}

BROWSE_PAGE = {
    "name": "browse_page",
    "description": "Fetch and extract content from a URL. Returns Markdown by default.",
    "parameters": {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "The URL to read."},
            "max_chars": {"type": "integer", "description": "Max characters to extract (default: 50000)."},
            "format": {"type": "string", "enum": ["markdown", "text"], "description": "Output format (default: markdown)."},
            "prompt": {"type": "string", "description": "Optional extraction hint for the agent's LLM."},
        },
        "required": ["url"],
    },
}

VERIFY_CLAIM = {
    "name": "verify_claim",
    "description": "Evaluate whether a factual claim is supported, contested, or under-evidenced.",
    "parameters": {
        "type": "object",
        "properties": {
            "claim": {"type": "string", "description": "The factual claim to verify."},
            "region": {"type": "string", "description": "Region code (default: wt-wt)."},
            "timelimit": {"type": "string", "enum": ["d", "w", "m", "y", ""]},
            "providers": {"type": "array", "items": {"type": "string"}},
            "profile": {"type": "string", "enum": ["free", "default", "free-verified", "production", "max-evidence"]},
            "goggles": {"type": "string"},
            "with_pages": {"type": "boolean", "description": "Fetch top pages for deeper analysis."},
            "deep": {"type": "boolean", "description": "Alias for with_pages."},
            "max_pages": {"type": "integer", "description": "Max pages to fetch (default: 3)."},
        },
        "required": ["claim"],
    },
}

EVIDENCE_REPORT = {
    "name": "evidence_report",
    "description": "Generate a citation-ready evidence report combining search, verification, and analysis.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query to gather evidence."},
            "claim": {"type": "string", "description": "Optional explicit claim to verify."},
            "region": {"type": "string"},
            "timelimit": {"type": "string", "enum": ["d", "w", "m", "y", ""]},
            "providers": {"type": "array", "items": {"type": "string"}},
            "profile": {"type": "string"},
            "goggles": {"type": "string"},
            "with_pages": {"type": "boolean"},
            "deep": {"type": "boolean"},
            "max_pages": {"type": "integer"},
            "max_sources": {"type": "integer", "description": "Max sources in report digest (default: 5)."},
        },
        "required": ["query"],
    },
}

LLM_CONTEXT = {
    "name": "llm_context",
    "description": "Build compact, citation-ready Markdown context for LLMs.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query to ground."},
            "type": {"type": "string", "enum": ["text", "news", "images", "videos", "books"]},
            "region": {"type": "string"},
            "timelimit": {"type": "string"},
            "providers": {"type": "array", "items": {"type": "string"}},
            "profile": {"type": "string"},
            "goggles": {"type": "string"},
            "max_sources": {"type": "integer", "description": "Max sources (default: 8)."},
            "include_verification": {"type": "boolean", "description": "Include evidence verification (default: true)."},
        },
        "required": ["query"],
    },
}

LIST_PROVIDERS = {
    "name": "list_providers",
    "description": "List available search providers, profiles, goggles presets, and cache stats.",
    "parameters": {"type": "object", "properties": {}},
}

CLEAR_CACHE = {
    "name": "clear_cache",
    "description": "Clear the response cache for fresh results.",
    "parameters": {"type": "object", "properties": {}},
}