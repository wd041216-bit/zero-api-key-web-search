#!/usr/bin/env python3
"""Zero-API-Key Web Search MCP server.

The canonical MCP command is ``zero-mcp``.
Legacy aliases ``cross-validated-search-mcp`` and ``free-web-search-mcp`` remain available for compatibility.
"""
import asyncio
import logging
import sys

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from zero_api_key_web_search.browse_page import browse
from zero_api_key_web_search.cache import get_cache, clear_cache
from zero_api_key_web_search.core import UltimateSearcher

# Configure logging
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("zero-api-key-web-search-mcp")

app = Server("zero-api-key-web-search")
searcher = UltimateSearcher()

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="list_providers",
            description=(
                "List available search providers, provider profiles, goggles presets, and setup hints."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            }
        ),
        Tool(
            name="search_web",
            description=(
                "Search the web for real-time information, news, images, books, or videos."
                " Always use this to verify facts or get up-to-date information before answering."
                " Optional providers include Bright Data when explicitly configured."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query."
                    },
                    "type": {
                        "type": "string",
                        "enum": ["text", "news", "images", "videos", "books"],
                        "description": "Type of search. Default is 'text'. Use 'news' for current events.",
                        "default": "text"
                    },
                    "region": {
                        "type": "string",
                        "description": (
                            "Region code (e.g., 'wt-wt' for global, 'us-en' for US English,"
                            " 'zh-cn' for China). Default is 'wt-wt'."
                        ),
                        "default": "wt-wt"
                    },
                    "timelimit": {
                        "type": "string",
                        "enum": ["d", "w", "m", "y", ""],
                        "description": (
                            "Time limit for results: 'd' (day), 'w' (week), 'm' (month),"
                            " 'y' (year). Leave empty for no limit."
                        )
                    },
                    "providers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of providers, e.g. ['ddgs', 'searxng', 'brightdata']."
                    },
                    "profile": {
                        "type": "string",
                        "enum": ["free", "default", "free-verified", "production", "max-evidence"],
                        "description": "Provider profile to use when providers is not supplied."
                    },
                    "goggles": {
                        "type": "string",
                        "description": "Built-in goggles preset for reranking/filtering, e.g. docs-first or research."
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="llm_context",
            description=(
                "Build compact, citation-ready Markdown context for LLMs. Prefer this when an agent "
                "needs grounded context rather than raw search results."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query to ground."},
                    "type": {
                        "type": "string",
                        "enum": ["text", "news", "images", "videos", "books"],
                        "description": "Type of search. Default is text.",
                        "default": "text",
                    },
                    "region": {"type": "string", "description": "Region code.", "default": "wt-wt"},
                    "timelimit": {
                        "type": "string",
                        "enum": ["d", "w", "m", "y", ""],
                        "description": "Optional freshness window.",
                    },
                    "providers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional provider list. Overrides profile.",
                    },
                    "profile": {
                        "type": "string",
                        "enum": ["free", "default", "free-verified", "production", "max-evidence"],
                        "description": "Provider profile.",
                    },
                    "goggles": {
                        "type": "string",
                        "description": "Built-in goggles preset, e.g. docs-first, research, or news-balanced.",
                    },
                    "max_sources": {
                        "type": "integer",
                        "description": "Maximum sources in the context pack.",
                        "default": 8,
                    },
                    "include_verification": {
                        "type": "boolean",
                        "description": "Include lightweight support/conflict evidence read.",
                        "default": True,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="browse_page",
            description=(
                "Fetch and extract content from a URL. Returns Markdown by default (use format='text' for plain text)."
                " Supports caching, cross-host redirect detection, domain filtering, and PDF extraction."
                " Use the prompt parameter to specify what information you want from the page."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the webpage to read."
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "Maximum number of characters to extract. Default is 50000.",
                        "default": 50000
                    },
                    "format": {
                        "type": "string",
                        "enum": ["markdown", "text"],
                        "description": "Output format: 'markdown' (default) preserves headings, lists, code blocks; 'text' returns plain text.",
                        "default": "markdown"
                    },
                    "prompt": {
                        "type": "string",
                        "description": "Optional extraction hint describing what information to focus on. The agent's LLM uses this to prioritize relevant content."
                    }
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="verify_claim",
            description=(
                "Evaluate whether a factual claim looks supported, contested, or"
                " under-evidenced based on corroborating search results."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "claim": {
                        "type": "string",
                        "description": "The factual claim to verify."
                    },
                    "region": {
                        "type": "string",
                        "description": "Region code (default: wt-wt).",
                        "default": "wt-wt"
                    },
                    "timelimit": {
                        "type": "string",
                        "enum": ["d", "w", "m", "y", ""],
                        "description": "Optional freshness window for the underlying evidence search."
                    },
                    "providers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of providers, e.g. ['ddgs', 'searxng', 'brightdata']."
                    },
                    "profile": {
                        "type": "string",
                        "enum": ["free", "default", "free-verified", "production", "max-evidence"],
                        "description": "Provider profile to use when providers is not supplied."
                    },
                    "goggles": {
                        "type": "string",
                        "description": "Built-in goggles preset for reranking/filtering."
                    },
                    "with_pages": {
                        "type": "boolean",
                        "description": "Fetch a few top pages and refine the classification using page text."
                    },
                    "deep": {
                        "type": "boolean",
                        "description": "Alias for with_pages. Enables page-aware verification."
                    },
                    "max_pages": {
                        "type": "integer",
                        "description": "Maximum number of pages to fetch when with_pages is true.",
                        "default": 3
                    }
                },
                "required": ["claim"]
            }
        ),
        Tool(
            name="evidence_report",
            description=(
                "Generate a higher-level evidence report that combines search, verification,"
                " citation-ready sources, and recommended next steps."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query used to gather evidence."
                    },
                    "claim": {
                        "type": "string",
                        "description": "Optional explicit claim to verify. Defaults to the query text."
                    },
                    "region": {
                        "type": "string",
                        "description": "Region code (default: wt-wt).",
                        "default": "wt-wt"
                    },
                    "timelimit": {
                        "type": "string",
                        "enum": ["d", "w", "m", "y", ""],
                        "description": "Optional freshness window for the underlying evidence search."
                    },
                    "providers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of providers, e.g. ['ddgs', 'searxng', 'brightdata']."
                    },
                    "profile": {
                        "type": "string",
                        "enum": ["free", "default", "free-verified", "production", "max-evidence"],
                        "description": "Provider profile to use when providers is not supplied."
                    },
                    "goggles": {
                        "type": "string",
                        "description": "Built-in goggles preset for reranking/filtering."
                    },
                    "with_pages": {
                        "type": "boolean",
                        "description": "Fetch a few top pages and refine the classification using page text."
                    },
                    "deep": {
                        "type": "boolean",
                        "description": "Alias for with_pages. Enables page-aware verification."
                    },
                    "max_pages": {
                        "type": "integer",
                        "description": "Maximum number of pages to fetch when with_pages is true.",
                        "default": 3
                    },
                    "max_sources": {
                        "type": "integer",
                        "description": "Maximum number of sources to include in the report digest.",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="clear_cache",
            description="Clear the response cache. Use this when you need fresh results instead of cached data.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute a tool."""
    try:
        if name == "list_providers":
            statuses = searcher.provider_statuses()
            profiles = searcher.provider_profiles()
            goggles = searcher.goggles_presets()
            result_text = "Available providers:\n"
            for item in statuses:
                result_text += (
                    f"- {item['name']}: {item['status']} | {item['kind']} | "
                    f"{item['description']}\n"
                )
                if item["status"] != "ready":
                    result_text += f"  Setup: {item['setup']}\n"
            current = ", ".join(provider.name for provider in searcher.providers)
            result_text += f"\nCurrent default path: {current}\n"
            result_text += "\nProvider profiles:\n"
            for profile_name, item in profiles.items():
                result_text += (
                    f"- {profile_name}: {', '.join(item['providers'])} | "
                    f"{item['description']}\n"
                )
            result_text += "\nGoggles presets:\n"
            for goggles_name, item in goggles.items():
                result_text += f"- {goggles_name}: {item['description']}\n"
            cache_stats = get_cache().stats()
            result_text += f"\nCache: {cache_stats['entries']} entries, {cache_stats['size_bytes'] // 1024}KB / {cache_stats['max_bytes'] // 1024 // 1024}MB | hits={cache_stats['hits']} misses={cache_stats['misses']} evictions={cache_stats['evictions']}\n"
            return [TextContent(type="text", text=result_text)]

        if name == "search_web":
            query = arguments.get("query", "")
            search_type = arguments.get("type", "text")
            region = arguments.get("region", "wt-wt")
            timelimit = arguments.get("timelimit")
            providers = arguments.get("providers")
            profile = arguments.get("profile")
            goggles = arguments.get("goggles")
            if timelimit == "":
                timelimit = None

            logger.info(f"Executing search_web: query='{query}', type='{search_type}', region='{region}'")

            answer = searcher.search(
                query=query,
                search_type=search_type,
                region=region,
                timelimit=timelimit,
                providers=providers,
                profile=profile,
                goggles=goggles,
            )

            # Format the output for the LLM
            result_text = f"Search Query: {answer.query}\n"
            providers_used = ", ".join(answer.metadata.get("providers_used", [])) or "none"
            result_text += f"Providers used: {providers_used}\n"
            result_text += f"Summary:\n{answer.answer}\n\n"
            result_text += "Detailed Sources:\n"
            for i, s in enumerate(answer.sources[:10], 1):
                result_text += f"{i}. {s.title}\n   URL: {s.url}\n   Snippet: {s.snippet}\n"
                if s.date:
                    result_text += f"   Date: {s.date}\n"
                result_text += "\n"

            return [TextContent(type="text", text=result_text)]

        elif name == "llm_context":
            query = arguments.get("query", "")
            search_type = arguments.get("type", "text")
            region = arguments.get("region", "wt-wt")
            timelimit = arguments.get("timelimit")
            providers = arguments.get("providers")
            profile = arguments.get("profile")
            goggles = arguments.get("goggles")
            max_sources = arguments.get("max_sources", 8)
            include_verification = arguments.get("include_verification", True)
            if timelimit == "":
                timelimit = None

            logger.info(f"Executing llm_context: query='{query}', type='{search_type}', region='{region}'")
            context = searcher.llm_context(
                query=query,
                search_type=search_type,
                region=region,
                timelimit=timelimit,
                providers=providers,
                profile=profile,
                goggles=goggles,
                max_sources=max_sources,
                include_verification=include_verification,
            )
            return [TextContent(type="text", text=context.context_markdown)]

        elif name == "browse_page":
            url = arguments.get("url", "")
            max_chars = arguments.get("max_chars", 50000)
            format_type = arguments.get("format", "markdown")
            prompt = arguments.get("prompt")

            logger.info(f"Executing browse_page: url='{url}' format='{format_type}'")

            result = browse(url, max_chars=max_chars, format=format_type, prompt=prompt)

            if result["status"] == "success":
                result_text = f"Title: {result['title']}\n"
                result_text += f"URL: {result['url']}\n"
                if result.get("from_cache"):
                    result_text += "(from cache)\n"
                result_text += f"\nContent:\n{result['content']}\n"
                if result.get('truncated'):
                    result_text += f"\n{result.get('truncation_marker', '')}"
                if result.get("prompt_hint"):
                    result_text += f"\n\n[Extraction focus: {result['prompt_hint']}]"
            elif result["status"] == "redirect":
                result_text = (
                    f"Cross-host redirect detected:\n"
                    f"  Original URL: {result['original_url']}\n"
                    f"  Redirect URL: {result['redirect_url']}\n"
                    f"  Status code: {result['status_code']}\n"
                    f"To follow this redirect, browse the redirect URL directly."
                )
            elif result["status"] == "blocked":
                result_text = f"Domain blocked: {result['domain']} — {result['reason']}"
            else:
                result_text = f"Error fetching {url}: {result.get('error', 'Unknown error')}"

            return [TextContent(type="text", text=result_text)]

        elif name == "verify_claim":
            claim = arguments.get("claim", "")
            region = arguments.get("region", "wt-wt")
            timelimit = arguments.get("timelimit")
            providers = arguments.get("providers")
            profile = arguments.get("profile")
            goggles = arguments.get("goggles")
            with_pages = arguments.get("with_pages", False)
            deep = arguments.get("deep", False)
            max_pages = arguments.get("max_pages", 3)
            if timelimit == "":
                timelimit = None

            logger.info(f"Executing verify_claim: claim='{claim}', region='{region}'")
            verification = searcher.verify_claim(
                claim=claim,
                region=region,
                timelimit=timelimit,
                providers=providers,
                profile=profile,
                goggles=goggles,
                include_pages=with_pages or deep,
                deep=deep,
                max_pages=max_pages,
            )

            result_text = f"Claim: {verification.claim}\n"
            result_text += f"Verdict: {verification.verdict}\n"
            result_text += f"Confidence: {verification.confidence}\n"
            result_text += f"{verification.summary}\n\n"
            result_text += (
                "Evidence Model: "
                f"{verification.analysis['verification_model']['name']} | "
                f"support={verification.analysis['support_score']:.2f} | "
                f"conflict={verification.analysis['conflict_score']:.2f} | "
                f"domains={verification.analysis['domain_diversity']} | "
                f"providers={verification.analysis['provider_diversity']} | "
                f"pages={verification.analysis['page_fetches_succeeded']}/{verification.analysis['page_fetches_attempted']}\n\n"
            )

            if verification.supporting_sources:
                result_text += "Supporting sources:\n"
                for index, source in enumerate(verification.supporting_sources[:5], 1):
                    evidence = source.extra.get("verification", {})
                    result_text += (
                        f"{index}. {source.title}\n"
                        f"   URL: {source.url}\n"
                        f"   Strength: {evidence.get('evidence_strength', 0)}\n"
                    )
                result_text += "\n"

            if verification.conflicting_sources:
                result_text += "Conflicting sources:\n"
                for index, source in enumerate(verification.conflicting_sources[:5], 1):
                    evidence = source.extra.get("verification", {})
                    result_text += (
                        f"{index}. {source.title}\n"
                        f"   URL: {source.url}\n"
                        f"   Strength: {evidence.get('evidence_strength', 0)}\n"
                    )
                result_text += "\n"

            return [TextContent(type="text", text=result_text)]

        elif name == "evidence_report":
            query = arguments.get("query", "")
            claim = arguments.get("claim") or None
            region = arguments.get("region", "wt-wt")
            timelimit = arguments.get("timelimit")
            providers = arguments.get("providers")
            profile = arguments.get("profile")
            goggles = arguments.get("goggles")
            with_pages = arguments.get("with_pages", False)
            deep = arguments.get("deep", False)
            max_pages = arguments.get("max_pages", 3)
            max_sources = arguments.get("max_sources", 5)
            if timelimit == "":
                timelimit = None

            logger.info(f"Executing evidence_report: query='{query}', region='{region}'")
            report = searcher.evidence_report(
                query=query,
                claim=claim,
                region=region,
                timelimit=timelimit,
                providers=providers,
                profile=profile,
                goggles=goggles,
                include_pages=with_pages or deep,
                deep=deep,
                max_pages=max_pages,
                max_sources=max_sources,
            )

            result_text = f"Evidence Report Query: {report.query}\n"
            result_text += f"Claim: {report.claim}\n"
            result_text += f"Verdict: {report.verdict}\n"
            result_text += f"Confidence: {report.confidence}\n"
            result_text += f"{report.executive_summary}\n"
            result_text += f"{report.verification_summary}\n\n"
            result_text += (
                "Report Model: "
                f"{report.analysis['report_model']} | "
                f"search_confidence={report.analysis['search_confidence']} | "
                f"support={report.analysis['support_score']:.2f} | "
                f"conflict={report.analysis['conflict_score']:.2f} | "
                f"providers={report.analysis['provider_diversity']} | "
                f"pages={report.analysis['page_fetches_succeeded']}/{report.analysis['page_fetches_attempted']}\n\n"
            )

            if report.verdict_rationale:
                result_text += "Why this verdict:\n"
                for item in report.verdict_rationale:
                    result_text += f"- {item}\n"
                result_text += "\n"

            if report.coverage_warnings:
                result_text += "Coverage warnings:\n"
                for item in report.coverage_warnings:
                    result_text += f"- {item}\n"
                result_text += "\n"

            if report.stance_summary:
                result_text += "Stance summary:\n"
                for label, bucket in report.stance_summary.items():
                    domains = ", ".join(bucket["top_domains"]) or "none"
                    result_text += (
                        f"- {label}: count={bucket['count']} score={bucket['score']} "
                        f"domains={domains}\n"
                    )
                result_text += "\n"

            if report.source_digest:
                result_text += "Source digest:\n"
                for index, item in enumerate(report.source_digest, 1):
                    result_text += (
                        f"{index}. {item['title']}\n"
                        f"   URL: {item['url']}\n"
                        f"   Class: {item['classification']}\n"
                        f"   Strength: {item['evidence_strength']}\n"
                    )
                result_text += "\n"

            if report.next_steps:
                result_text += "Next steps:\n"
                for step in report.next_steps:
                    result_text += f"- {step}\n"

            return [TextContent(type="text", text=result_text)]

        elif name == "clear_cache":
            clear_cache()
            return [TextContent(type="text", text="Cache cleared successfully.")]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Error executing tool {name}: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    """Run the MCP server."""
    logger.info("Starting Zero-API-Key Web Search MCP Server...")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

def run():
    """Entry point for the console script."""
    asyncio.run(main())

if __name__ == "__main__":
    run()
