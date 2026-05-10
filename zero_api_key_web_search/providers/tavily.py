"""Tavily-backed search provider."""

from __future__ import annotations

import os

from zero_api_key_web_search.providers.base import ProviderConfigurationError, ProviderResult


class TavilyProvider:
    """Search provider backed by the optional tavily-python package."""

    name = "tavily"
    ENV_VARS = (
        "ZERO_SEARCH_TAVILY_API_KEY",
        "TAVILY_API_KEY",
    )

    def __init__(self, timeout: int = 15, api_key: str | None = None):
        self.timeout = timeout
        self.api_key = api_key or self._configured_api_key()

    @classmethod
    def _configured_api_key(cls) -> str:
        for env_var in cls.ENV_VARS:
            value = os.getenv(env_var, "").strip()
            if value:
                return value
        return ""

    @classmethod
    def configuration_hint(cls) -> str:
        primary = cls.ENV_VARS[0]
        aliases = ", ".join(cls.ENV_VARS[1:])
        return (
            f"Configure Tavily by setting {primary}. "
            f"Alias env vars also supported: {aliases}."
        )

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def search(
        self,
        query: str,
        search_type: str,
        timelimit: str | None = None,
        region: str = "wt-wt",
        max_results: int = 15,
        **kwargs,
    ) -> list[ProviderResult]:
        if search_type not in ("text", "news"):
            return []
        if not self.api_key:
            raise ProviderConfigurationError(self.configuration_hint())

        try:
            from tavily import TavilyClient
        except ImportError as exc:
            raise ProviderConfigurationError(
                "Install Tavily support with: pip install zero-api-key-web-search[tavily]"
            ) from exc

        time_range_map = {
            "d": "day",
            "w": "week",
            "m": "month",
            "y": "year",
        }
        payload = {
            "query": query,
            "search_depth": kwargs.get("search_depth", "advanced"),
            "topic": "news" if search_type == "news" else "general",
            "max_results": min(max_results, 20),
        }
        time_range = time_range_map.get(timelimit or "")
        if time_range:
            payload["time_range"] = time_range

        client = TavilyClient(api_key=self.api_key)
        response = client.search(**payload)
        api_results = response.get("results", []) if isinstance(response, dict) else []

        results: list[ProviderResult] = []
        for item in api_results[:max_results]:
            if not isinstance(item, dict):
                continue
            url = item.get("url", "")
            if not isinstance(url, str) or not url:
                continue
            metadata: dict = {"provider": "tavily"}
            if "score" in item:
                metadata["score"] = item.get("score")
            results.append(
                ProviderResult(
                    url=url,
                    title=str(item.get("title", "")),
                    snippet=str(item.get("content", item.get("snippet", ""))),
                    date=str(item.get("published_date", item.get("publishedDate", ""))),
                    metadata=metadata,
                )
            )
        return results

    async def asearch(
        self,
        query: str,
        search_type: str,
        timelimit: str | None = None,
        region: str = "wt-wt",
        max_results: int = 15,
        **kwargs,
    ) -> list[ProviderResult]:
        import asyncio

        return await asyncio.to_thread(
            self.search, query, search_type, timelimit, region, max_results, **kwargs
        )
