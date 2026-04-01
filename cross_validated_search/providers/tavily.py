"""Tavily-backed search provider."""

from __future__ import annotations

import os
from typing import Optional

from cross_validated_search.providers.base import ProviderResult


class TavilyProvider:
    """Search provider backed by the Tavily API."""

    name = "tavily"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout

    @staticmethod
    def is_configured() -> bool:
        """Return True when a Tavily API key is available."""
        return bool(os.getenv("TAVILY_API_KEY"))

    def search(
        self,
        query: str,
        search_type: str,
        timelimit: Optional[str] = None,
        region: str = "wt-wt",
        max_results: int = 15,
        **kwargs,
    ) -> list[ProviderResult]:
        from tavily import TavilyClient

        if search_type not in ("text", "news"):
            return []

        client = TavilyClient()

        topic = "news" if search_type == "news" else "general"

        search_kwargs: dict = {
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
            "topic": topic,
        }

        if timelimit:
            time_range_map = {
                "d": "day",
                "w": "week",
                "m": "month",
                "y": "year",
            }
            mapped = time_range_map.get(timelimit, timelimit)
            if mapped in ("day", "week", "month", "year"):
                search_kwargs["time_range"] = mapped

        response = client.search(**search_kwargs)

        results: list[ProviderResult] = []
        for item in response.get("results", []):
            url = item.get("url", "")
            if not url:
                continue
            results.append(
                ProviderResult(
                    url=url,
                    title=item.get("title", ""),
                    snippet=item.get("content", ""),
                    date=item.get("published_date", ""),
                    metadata={
                        "score": item.get("score"),
                    },
                )
            )

        return results
