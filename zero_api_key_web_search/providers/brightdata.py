"""Bright Data SERP API search provider.

Professional-grade search provider backed by Bright Data. Supports multi-engine
SERP (Google, Bing, DuckDuckGo, Yandex, Baidu, Yahoo, Naver), LLM-friendly
markdown output, AI Overviews, mobile device results, and geo-targeting across
195 countries. Requires a Bright Data account — sign up with 5000 free credits:
https://get.brightdata.com/h21j9xz4uxgd

Uses the Super Proxy endpoint with brd_json=1 for structured JSON results.
Falls back to HTML parsing when structured results are unavailable.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from urllib.parse import urlencode

from zero_api_key_web_search.providers.base import ProviderConfigurationError, ProviderResult


ENGINE_MAP = {
    "google": "https://www.google.com/search",
    "bing": "https://www.bing.com/search",
    "duckduckgo": "https://duckduckgo.com/",
    "yandex": "https://yandex.com/search/",
    "baidu": "https://www.baidu.com/s",
    "yahoo": "https://search.yahoo.com/search",
    "naver": "https://search.naver.com/search.naver",
}


class BrightDataProvider:
    """Professional-grade search provider backed by Bright Data SERP API.

    Supports 7 search engines (Google, Bing, DuckDuckGo, Yandex, Baidu, Yahoo, Naver),
    structured JSON results, LLM-friendly markdown output, AI Overviews, mobile
    device emulation, and geo-targeting across 195 countries.

    Uses the Super Proxy endpoint with brd_json=1 for parsed JSON results.
    Automatically falls back to HTML parsing when structured data is unavailable.

    Requires a Bright Data account. Sign up with 5000 free credits:
    https://get.brightdata.com/h21j9xz4uxgd
    """

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
    ENGINE_ENV_VAR = "ZERO_SEARCH_BRIGHTDATA_ENGINE"
    DEFAULT_ZONE = "serp_api1"
    DEFAULT_ENGINE = "google"
    SUPPORTED_ENGINES = tuple(ENGINE_MAP.keys())

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

    def _search_url(self, query: str, search_type: str, region: str, engine: str = "google") -> str:
        country = self._region_to_country(region)
        engine = engine if engine in ENGINE_MAP else self.DEFAULT_ENGINE
        base_url = ENGINE_MAP[engine]

        if engine == "google":
            params = {"q": query, "brd_json": "1"}
            if country:
                params["gl"] = country
                params["hl"] = region.split("-")[0] if "-" in region else "en"
            tbm_by_type = {"news": "nws", "images": "isch", "videos": "vid", "books": "bks"}
            tbm = tbm_by_type.get(search_type)
            if tbm:
                params["tbm"] = tbm

        elif engine == "bing":
            params = {"q": query, "brd_json": "1"}
            if country:
                params["cc"] = country
                params["setlang"] = region.split("-")[0] if "-" in region else "en"

        elif engine == "duckduckgo":
            params = {"q": query, "brd_json": "1"}
            if country:
                params["kl"] = region.lower()

        elif engine == "yandex":
            params = {"text": query, "brd_json": "1"}
            if country:
                params["lr"] = country

        elif engine == "baidu":
            params = {"wd": query, "brd_json": "1"}
            if country:
                params["rsv_srlang"] = region.split("-")[0] if "-" in region else "en"

        elif engine == "yahoo":
            params = {"p": query, "brd_json": "1"}
            if country:
                params["vc"] = country

        elif engine == "naver":
            params = {"query": query, "brd_json": "1"}
            if country:
                params["where"] = "nexearch"

        else:
            params = {"q": query, "brd_json": "1"}

        return base_url + "?" + urlencode(params)

    def _request_payload(
        self,
        query: str,
        search_type: str,
        region: str,
        **kwargs,
    ) -> dict:
        engine = kwargs.get("engine", self.DEFAULT_ENGINE)
        payload = {
            "zone": self.zone,
            "url": self._search_url(query, search_type, region, engine=engine),
            "format": "json",
            "method": "GET",
        }
        country = self._region_to_country(region)
        if country:
            payload["country"] = country
        if kwargs.get("data_format") == "markdown":
            payload["data_format"] = "markdown"
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

    def _parse_html_results(self, html: str, max_results: int) -> list[ProviderResult]:
        """Parse Google HTML search results using BeautifulSoup."""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return []

        soup = BeautifulSoup(html, "lxml")
        results: list[ProviderResult] = []

        for container in soup.select("div.tF2Cxc")[:max_results]:
            title_tag = container.select_one("h3")
            link_tag = container.select_one("a[href]")
            snippet_tag = container.select_one("div.VwiC3b, div.IsZvec")

            if not link_tag:
                continue

            url = link_tag.get("href", "")
            if not url or url.startswith("/search"):
                continue

            title = title_tag.get_text(strip=True) if title_tag else ""
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""

            results.append(
                ProviderResult(
                    url=url,
                    title=title,
                    snippet=snippet,
                    date="",
                    metadata={"provider": "brightdata", "zone": self.zone},
                )
            )

        if not results:
            for h3 in soup.select("h3")[:max_results]:
                parent_a = h3.find_parent("a", href=True)
                if not parent_a:
                    continue
                url = parent_a.get("href", "")
                if not url or url.startswith("/search"):
                    continue
                title = h3.get_text(strip=True)
                snippet = ""
                snippet_parent = h3.find_parent(["div", "li"])
                if snippet_parent:
                    snippet_tag = snippet_parent.select_one("div.VwiC3b, div.IsZvec, span.aCOpRe")
                    if snippet_tag:
                        snippet = snippet_tag.get_text(strip=True)

                results.append(
                    ProviderResult(
                        url=url,
                        title=title,
                        snippet=snippet,
                        date="",
                        metadata={"provider": "brightdata", "zone": self.zone},
                    )
                )

        return results

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

        engine = kwargs.get("engine", os.getenv(self.ENGINE_ENV_VAR, self.DEFAULT_ENGINE))

        request_body = json.dumps(
            self._request_payload(
                query=query,
                search_type=search_type,
                region=region,
                engine=engine,
                **{k: v for k, v in kwargs.items() if k != "engine"},
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
                "User-Agent": "zero-api-key-web-search/23.0.0",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                response_text = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Bright Data request failed: HTTP {exc.code} {detail}") from exc

        payload = json.loads(response_text)

        # Check for markdown data_format response
        if kwargs.get("data_format") == "markdown":
            markdown_content = ""
            if isinstance(payload.get("body"), str):
                markdown_content = payload["body"]
            elif isinstance(response_text, str):
                markdown_content = response_text

            if markdown_content:
                return [
                    ProviderResult(
                        url=self._search_url(query, search_type, region, engine=engine),
                        title=f"Search results: {query} (via {engine})",
                        snippet=markdown_content[:5000],
                        date="",
                        metadata={
                            "provider": "brightdata",
                            "zone": self.zone,
                            "search_engine": engine,
                            "format": "markdown",
                        },
                    )
                ]

        # Try structured SERP results first (brd_json=1 format)
        serp_data = None
        if isinstance(payload.get("body"), str) and payload["body"].startswith("{"):
            try:
                serp_data = json.loads(payload["body"])
            except (json.JSONDecodeError, TypeError):
                pass
        elif isinstance(payload.get("body"), dict):
            serp_data = payload["body"]

        if serp_data is None and "organic" in payload:
            serp_data = payload

        if serp_data:
            general = serp_data.get("general", {})
            if not isinstance(general, dict):
                general = {}
            json_results = self._extract_results(serp_data, max_results=max_results)

            if json_results:
                results: list[ProviderResult] = []
                for result in json_results:
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
                                "search_engine": engine,
                            },
                        ),
                    )
                return results

        # Fallback: parse HTML response
        html_body = ""
        if isinstance(payload.get("body"), str) and not payload["body"].startswith("{"):
            html_body = payload["body"]
        elif isinstance(response_text, str) and "<!doctype" in response_text.lower():
            html_body = response_text

        if html_body:
            return self._parse_html_results(html_body, max_results)

        return []

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