"""Compatibility shim: the historical ``zero_api_key_web_search_compat`` import name.

Re-exports the current package so old integrations keep working after the
Zero-API-Key Web Search rebrand. New code should import from ``zero_api_key_web_search`` directly.
"""

from zero_api_key_web_search import (  # noqa: F401
    browse_page,
    cache,
    context,
    core,
    evidence_report,
    laya_filter,
    provider_setup,
    search,
    search_web,
    transport,
    verify_claim,
)

__all__ = [
    "browse_page",
    "cache",
    "context",
    "core",
    "evidence_report",
    "laya_filter",
    "provider_setup",
    "search",
    "search_web",
    "transport",
    "verify_claim",
]
