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
            name="search_web",
            description=(
                "Search the web for real-time information, news, images, books, or videos."
                " Always use this to verify facts or get up-to-date information before answering."
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
                        "description": "Optional list of providers, e.g. ['ddgs', 'searxng']."
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="browse_page",
            description=(
                "Fetch and extract pure text content from a specific URL."
                " Use this to read the full content of a page found via search_web."
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
                        "description": "Maximum number of characters to extract. Default is 10000.",
                        "default": 10000
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
                        "description": "Optional list of providers, e.g. ['ddgs', 'searxng']."
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
                        "description": "Optional list of providers, e.g. ['ddgs', 'searxng']."
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
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute a tool."""
    try:
        if name == "search_web":
            query = arguments.get("query", "")
            search_type = arguments.get("type", "text")
            region = arguments.get("region", "wt-wt")
            timelimit = arguments.get("timelimit")
            providers = arguments.get("providers")
            if timelimit == "":
                timelimit = None

            logger.info(f"Executing search_web: query='{query}', type='{search_type}', region='{region}'")

            answer = searcher.search(
                query=query,
                search_type=search_type,
                region=region,
                timelimit=timelimit,
                providers=providers,
            )

            # Format the output for the LLM
            result_text = f"Search Query: {answer.query}\n"
            result_text += f"Summary:\n{answer.answer}\n\n"
            result_text += "Detailed Sources:\n"
            for i, s in enumerate(answer.sources[:10], 1):
                result_text += f"{i}. {s.title}\n   URL: {s.url}\n   Snippet: {s.snippet}\n"
                if s.date:
                    result_text += f"   Date: {s.date}\n"
                result_text += "\n"

            return [TextContent(type="text", text=result_text)]

        elif name == "browse_page":
            url = arguments.get("url", "")
            max_chars = arguments.get("max_chars", 10000)

            logger.info(f"Executing browse_page: url='{url}'")

            result = browse(url, max_chars=max_chars)

            if result["status"] == "success":
                result_text = f"Title: {result['title']}\n"
                result_text += f"URL: {result['url']}\n\n"
                result_text += f"Content:\n{result['content']}\n"
                if result.get('truncated'):
                    result_text += f"\n... [Content truncated. Total length: {result['total_length']} chars]"
            else:
                result_text = f"Error fetching {url}: {result.get('error', 'Unknown error')}"

            return [TextContent(type="text", text=result_text)]

        elif name == "verify_claim":
            claim = arguments.get("claim", "")
            region = arguments.get("region", "wt-wt")
            timelimit = arguments.get("timelimit")
            providers = arguments.get("providers")
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
