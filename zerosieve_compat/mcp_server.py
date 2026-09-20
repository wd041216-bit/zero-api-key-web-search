"""Compatibility shim for the historical MCP server import path."""

from zerosieve.mcp_server import *  # noqa: F401,F403
from zerosieve.mcp_server import app, call_tool, list_tools, run  # noqa: F401
