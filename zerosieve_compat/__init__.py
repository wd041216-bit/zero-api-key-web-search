"""Compatibility shim: the historical ``zerosieve_compat`` import name.

Re-exports the current package so old integrations keep working after the
ZeroSieve rebrand. New code should import from ``zerosieve`` directly.
"""

from zerosieve import (  # noqa: F401
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
