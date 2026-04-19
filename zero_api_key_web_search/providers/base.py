"""Provider interfaces and normalized provider results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class ProviderResult:
    """Normalized search result returned by an upstream search provider."""

    url: str
    title: str
    snippet: str = ""
    date: str = ""
    metadata: dict = field(default_factory=dict)


class SearchProvider(Protocol):
    """Protocol implemented by search backends."""

    name: str

    def search(
        self,
        query: str,
        search_type: str,
        timelimit: str | None = None,
        region: str = "wt-wt",
        max_results: int = 15,
        **kwargs,
    ) -> list[ProviderResult]:  # type: ignore[empty-body]
        """Return normalized search results for the given query."""

    async def asearch(
        self,
        query: str,
        search_type: str,
        timelimit: str | None = None,
        region: str = "wt-wt",
        max_results: int = 15,
        **kwargs,
    ) -> list[ProviderResult]:
        """Async variant of search. Defaults to running sync search in a thread."""
        import asyncio
        return await asyncio.to_thread(self.search, query, search_type, timelimit, region, max_results, **kwargs)
