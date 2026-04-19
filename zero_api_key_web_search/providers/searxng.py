"""SearXNG-backed search provider."""

from __future__ import annotations

import json
import os
import urllib.request
from urllib.parse import quote_plus

from zero_api_key_web_search.providers.base import ProviderResult


class SearxngProvider:
    """Search provider backed by a SearXNG instance."""

    name = "searxng"
    ENV_VARS = (
        "ZERO_SEARCH_SEARXNG_URL",
        "CROSS_VALIDATED_SEARCH_SEARXNG_URL",
        "FREE_WEB_SEARCH_SEARXNG_URL",
        "SEARXNG_URL",
    )

    def __init__(self, timeout: int = 15, base_url: str | None = None):
        self.timeout = timeout
        env_base_url = self._configured_base_url()
        self.base_url = (base_url or env_base_url).rstrip("/")

    @classmethod
    def _configured_base_url(cls) -> str:
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
            f"Configure a self-hosted SearXNG instance via {primary}. "
            f"Alias env vars also supported: {aliases}."
        )

    def is_configured(self) -> bool:
        return bool(self.base_url)

    def search(
        self,
        query: str,
        search_type: str,
        timelimit: str | None = None,
        region: str = "wt-wt",
        max_results: int = 15,
        **kwargs,
    ) -> list[ProviderResult]:
        if not self.base_url:
            raise RuntimeError(self.configuration_hint())

        categories_map = {
            "text": "general",
            "news": "news",
            "images": "images",
            "videos": "videos",
        }
        if search_type == "books":
            return []

        category = categories_map.get(search_type, "general")
        url = (
            f"{self.base_url}/search?q={quote_plus(query)}"
            f"&format=json&language={quote_plus(region)}"
            f"&categories={quote_plus(category)}"
        )
        if timelimit:
            url += f"&time_range={quote_plus(timelimit)}"

        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "zero-api-key-web-search/1.0.0",
            },
        )

        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))

        results: list[ProviderResult] = []
        for result in payload.get("results", [])[:max_results]:
            result_url = result.get("url")
            if not result_url:
                continue
            results.append(
                ProviderResult(
                    url=result_url,
                    title=result.get("title", ""),
                    snippet=result.get("content", ""),
                    date=result.get("publishedDate", result.get("published_date", "")),
                    metadata={"provider": "searxng"},
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
            self.search, query, search_type, timelimit, region, max_results, **kwargs,
        )
