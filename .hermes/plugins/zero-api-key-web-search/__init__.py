"""Hermes plugin registration for zero-api-key-web-search.

This plugin connects to the zero-mcp MCP server which provides
all search, browse, verification, and report tools.
"""


def register(ctx):
    """Register the zero-api-key-web-search plugin with Hermes."""
    # The MCP server provides all tools via the stdio protocol.
    # Hermes will auto-discover tools from the MCP server config.
    # No manual tool registration needed — the MCP server handles it.
    ctx.register_skill(
        "web-search",
        Path(__file__).parent.parent.parent.parent / "zero_api_key_web_search" / "skills" / "SKILL.md",
    )


from pathlib import Path