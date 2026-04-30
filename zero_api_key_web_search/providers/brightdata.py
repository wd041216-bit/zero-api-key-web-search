"""Bright Data SERP API search provider."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from urllib.parse import urlencode

from zero_api_key_web_search.providers.base import ProviderConfigurationError, ProviderResult


class BrightDataProvider:
    """Optional production-grade provider backed by Bright Data SERP API."""

    name = "brightdata"
    SIGNUP_URL = "https://get.brightdata.com/h21j9xz4uxgd"
    API_URL = "https://api.brightdata.com/request"
    API_KEY_ENV_VARS = (
        "ZERO_SEARCH_BRIGHTDATA_API_KEY",
        "BRIGHTDATA_API_KEY",
        "BRIGHT_DATA_API_KEY",
    )
    ZONE_ENV_VARS = (
        "ZERO_SEARCH_BRIGHTDATA_ZONE",
        "BRIGHTDATA_SERP_ZONE",
        "BRIGHT_DATA_SERP_ZONE",
    )
    COUNTRY_ENV_VAR = "ZERO_SEARCH_BRIGHTDATA_COUNTRY"
    DEFAULT_ZONE = "web_search"

    def __init__(
        self,
        timeout: int = 15,
        api_key: str | None = None,
        zone: str | None = None,
        api_url: str | None = None,
    ):
        self.timeout = timeout
        self.api_key = api_key or self._configured_api_key()
        self.zone = zone or self._configured_zone() or self.DEFAULT_ZONE
        self.api_url = api_url or os.getenv("ZERO_SEARCH_BRIGHTDATA_API_URL", self.API_URL)

    @classmethod
    def _configured_api_key(cls) -> str:
        for env_var in cls.API_KEY_ENV_VARS:
            value = os.getenv(env_var, "").strip()
            if value:
                return value
        return ""

    @classmethod
    def _configured_zone(cls) -> str:
        for env_var in cls.ZONE_ENV_VARS:
            value = os.getenv(env_var, "").strip()
            if value:
                return value
        return ""

    @classmethod
    def configuration_hint(cls) -> str:
        key_vars = ", ".join(cls.API_KEY_ENV_VARS)
        zone_vars = ", ".join(cls.ZONE_ENV_VARS)
        return (
            "Configure Bright Data by setting "
            f"{cls.API_KEY_ENV_VARS[0]} and, if your SERP zone is not "
            f"'{cls.DEFAULT_ZONE}', {cls.ZONE_ENV_VARS[0]}. "
            f"Aliases supported: {key_vars}; {zone_vars}. "
            f"New users can sign up at {cls.SIGNUP_URL}."
        )

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _region_to_country(self, region: str) -> str:
        configured = os.getenv(self.COUNTRY_ENV_VAR, "").strip()
        if configured:
            return configured.lower()

        cleaned = (region or "").lower()
        if cleaned in {"", "wt-wt"}:
            return ""
        for part in cleaned.replace("_", "-").split("-"):
            if len(part) == 2 and part.isalpha():
                return part
        return ""

    def _search_url(self, query: str, search_type: str, region: str) -> str:
        country = self._region_to_country(region)
        params = {"q": query}
        if country:
            params["gl"] = country
            params["hl"] = region.split("-")[0] if "-" in region else "en"

        tbm_by_type = {
            "news": "nws",
            "images": "isch",
            "videos": "vid",
            "books": "bks",
        }
        tbm = tbm_by_type.get(search_type)
        if tbm:
            params["tbm"] = tbm

        return "https://www.google.com/search?" + urlencode(params)

    def _request_payload(
        self,
        query: str,
        search_type: str,
        region: str,
        **kwargs,
    ) -> dict:
        payload = {
            "zone": self.zone,
            "url": self._search_url(query, search_type, region),
            "format": "json",
            "method": "GET",
        }
        country = self._region_to_country(region)
        if country:
            payload["country"] = country
        data_format = kwargs.get("data_format")
        if data_format:
            payload["data_format"] = data_format
        return payload

    def _extract_result_url(self, result: dict) -> str:
        return (
            result.get("link")
            or result.get("url")
            or result.get("href")
            or result.get("display_link")
            or ""
        )

    def _extract_results(self, payload: dict, max_results: int) -> list[dict]:
        candidates = []
        for key in ("organic", "results", "news", "images", "videos", "books"):
            value = payload.get(key)
            if isinstance(value, list):
                candidates.extend(item for item in value if isinstance(item, dict))

        if not candidates and isinstance(payload.get("body"), dict):
            return self._extract_results(payload["body"], max_results)
        return candidates[:max_results]

    def search(
        self,
        query: str,
        search_type: str,
        timelimit: str | None = None,
        region: str = "wt-wt",
        max_results: int = 15,
        **kwargs,
    ) -> list[ProviderResult]:
        if not self.api_key:
            raise ProviderConfigurationError(self.configuration_hint())

        request_body = json.dumps(
            self._request_payload(
                query=query,
                search_type=search_type,
                region=region,
                **kwargs,
            )
        ).encode("utf-8")
        request = urllib.request.Request(
            self.api_url,
            data=request_body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "zero-api-key-web-search/1.0.0",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                response_text = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Bright Data request failed: HTTP {exc.code} {detail}") from exc

        payload = json.loads(response_text)
        general = payload.get("general", {})
        if not isinstance(general, dict):
            general = {}
        results: list[ProviderResult] = []
        for result in self._extract_results(payload, max_results=max_results):
            url = self._extract_result_url(result)
            if not url:
                continue
            results.append(
                ProviderResult(
                    url=url,
                    title=result.get("title", result.get("name", "")),
                    snippet=result.get("description", result.get("snippet", "")),
                    date=result.get("date", result.get("published", "")),
                    metadata={
                        "provider": "brightdata",
                        "zone": self.zone,
                        "search_engine": general.get("search_engine"),
                    },
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
