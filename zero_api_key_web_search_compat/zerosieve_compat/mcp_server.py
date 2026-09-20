"""Compatibility shim for the historical MCP server import path."""

from zero_api_key_web_search.mcp_server import *  # noqa: F401,F403
from zero_api_key_web_search.mcp_server import app, call_tool, list_tools, run  # noqa: F401
