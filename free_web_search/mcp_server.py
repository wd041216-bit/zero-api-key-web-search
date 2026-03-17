#!/usr/bin/env python3
"""
Free Web Search Ultimate - MCP Server (Model Context Protocol)
Allows seamless integration with Claude Desktop, Cursor, and other MCP-compatible clients.
"""
import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from free_web_search.search_web import UltimateSearcher
from free_web_search.browse_page import browse

# Configure logging
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("free-web-search-mcp")

app = Server("free-web-search-ultimate")
searcher = UltimateSearcher()

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="search_web",
            description="Search the web for real-time information, news, images, books, or videos. Always use this to verify facts or get up-to-date information before answering.",
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
                        "description": "Region code (e.g., 'wt-wt' for global, 'us-en' for US English, 'zh-cn' for China). Default is 'wt-wt'.",
                        "default": "wt-wt"
                    },
                    "timelimit": {
                        "type": "string",
                        "enum": ["d", "w", "m", "y", ""],
                        "description": "Time limit for results: 'd' (day), 'w' (week), 'm' (month), 'y' (year). Leave empty for no limit."
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="browse_page",
            description="Fetch and extract pure text content from a specific URL. Use this to read the full content of a page found via search_web.",
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
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute a tool."""
    try:
        if name == "search_web":
            query = arguments.get("query")
            search_type = arguments.get("type", "text")
            region = arguments.get("region", "wt-wt")
            timelimit = arguments.get("timelimit")
            if timelimit == "":
                timelimit = None
                
            logger.info(f"Executing search_web: query='{query}', type='{search_type}', region='{region}'")
            
            answer = searcher.search(
                query=query,
                search_type=search_type,
                region=region,
                timelimit=timelimit
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
            url = arguments.get("url")
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
            
        else:
            raise ValueError(f"Unknown tool: {name}")
            
    except Exception as e:
        logger.error(f"Error executing tool {name}: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    """Run the MCP server."""
    logger.info("Starting Free Web Search Ultimate MCP Server...")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

def run():
    """Entry point for the console script."""
    asyncio.run(main())

if __name__ == "__main__":
    run()
