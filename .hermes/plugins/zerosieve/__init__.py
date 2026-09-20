"""Hermes plugin registration for zerosieve.

This plugin connects to the zs-mcp MCP server which provides
all search, browse, verification, and report tools.
"""


def register(ctx):
    """Register the zerosieve plugin with Hermes."""
    # The MCP server provides all tools via the stdio protocol.
    # Hermes will auto-discover tools from the MCP server config.
    # No manual tool registration needed — the MCP server handles it.
    ctx.register_skill(
        "web-search",
        Path(__file__).parent.parent.parent.parent / "zerosieve" / "skills" / "SKILL.md",
    )


from pathlib import Path