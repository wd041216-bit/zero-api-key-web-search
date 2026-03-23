"""Provider interfaces and normalized provider results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Protocol


@dataclass
class ProviderResult:
    """Normalized search result returned by an upstream search provider."""

    url: str
    title: str
    snippet: str = ""
    date: str = ""
    metadata: Dict = field(default_factory=dict)


class SearchProvider(Protocol):
    """Protocol implemented by search backends."""

    name: str

    def search(
        self,
        query: str,
        search_type: str,
        timelimit: Optional[str] = None,
        region: str = "wt-wt",
        max_results: int = 15,
        **kwargs,
    ) -> list[ProviderResult]:
        """Return normalized search results for the given query."""
