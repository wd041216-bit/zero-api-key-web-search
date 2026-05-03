"""Bright Data Web Unlocker provider for accessing blocked and geo-restricted pages.

Uses the same Super Proxy endpoint as the SERP provider but with a different zone
(web_unlocker1 by default). Handles CAPTCHAs, anti-bot protections, IP rotation,
and JavaScript rendering automatically.

Requires a Bright Data account. Sign up with 5000 free credits:
https://get.brightdata.com/h21j9xz4uxgd
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from zero_api_key_web_search.providers.base import ProviderConfigurationError


class WebUnlockerProvider:
    """Access blocked, CAPTCHA-protected, or geo-restricted pages via Bright Data Web Unlocker.

    Web Unlocker automatically handles browser fingerprinting, CAPTCHA solving,
    IP rotation, JavaScript rendering, and cookie management. It returns the
    fully rendered page content as HTML or Markdown.

    Requires a Bright Data account. Sign up at:
    https://get.brightdata.com/h21j9xz4uxgd

    Set ZERO_SEARCH_BRIGHTDATA_API_KEY with your API key. The same key works
    for both SERP and Web Unlocker. Create a Web Unlocker zone in your Bright Data
    dashboard (Proxies → Add new zone → Web Unlocker).
    """

    name = "web_unlocker"
    SIGNUP_URL = "https://get.brightdata.com/h21j9xz4uxgd"
    API_URL = "https://api.brightdata.com/request"
    API_KEY_ENV_VARS = (
        "ZERO_SEARCH_BRIGHTDATA_API_KEY",
        "BRIGHTDATA_API_KEY",
        "BRIGHT_DATA_API_KEY",
    )
    UNLOCKER_ZONE_ENV_VARS = (
        "ZERO_SEARCH_BRIGHTDATA_UNLOCKER_ZONE",
        "BRIGHTDATA_UNLOCKER_ZONE",
        "BRIGHT_DATA_UNLOCKER_ZONE",
    )
    SERP_ZONE_ENV_VARS = (
        "ZERO_SEARCH_BRIGHTDATA_ZONE",
        "BRIGHTDATA_SERP_ZONE",
        "BRIGHT_DATA_SERP_ZONE",
    )
    DEFAULT_ZONE = "web_unlocker1"
    AUTO_ENV_VAR = "ZERO_SEARCH_BRIGHTDATA_UNLOCKER_AUTO"

    def __init__(
        self,
        timeout: int = 30,
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
        for env_var in cls.UNLOCKER_ZONE_ENV_VARS:
            value = os.getenv(env_var, "").strip()
            if value:
                return value
        for env_var in cls.SERP_ZONE_ENV_VARS:
            value = os.getenv(env_var, "").strip()
            if value:
                return value
        return ""

    @classmethod
    def configuration_hint(cls) -> str:
        zone_vars = ", ".join(cls.UNLOCKER_ZONE_ENV_VARS)
        return (
            "Configure Web Unlocker by setting "
            f"{cls.API_KEY_ENV_VARS[0]} (same key as SERP) and, "
            f"if your zone is not '{cls.DEFAULT_ZONE}', {cls.UNLOCKER_ZONE_ENV_VARS[0]}. "
            f"Create a Web Unlocker zone in Bright Data Dashboard: "
            f"Proxies → Add new zone → Web Unlocker. "
            f"Zone aliases: {zone_vars}. "
            f"New users can sign up at {cls.SIGNUP_URL}."
        )

    @classmethod
    def is_auto_enabled(cls) -> bool:
        env_val = os.getenv(cls.AUTO_ENV_VAR, "1").strip()
        return env_val not in ("0", "false", "no", "disabled")

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def unlock(
        self,
        url: str,
        data_format: str = "markdown",
        country: str = "",
    ) -> dict:
        """Fetch a URL through Bright Data Web Unlocker.

        Args:
            url: The URL to fetch.
            data_format: Output format — "markdown" (LLM-friendly) or "raw" (full HTML).
            country: Two-letter country code for geo-targeting (e.g. "us", "de").

        Returns:
            Dict with keys: status, url, title, content, markdown, text,
            truncated, total_length, format, via_unlocker.
        """
        if not self.api_key:
            return {
                "status": "error",
                "url": url,
                "error": ProviderConfigurationError(self.configuration_hint()),
                "via_unlocker": True,
            }

        payload = {
            "zone": self.zone,
            "url": url,
            "format": "json",
            "method": "GET",
        }
        if data_format == "markdown":
            payload["data_format"] = "markdown"
        if country:
            payload["country"] = country

        request_body = json.dumps(payload).encode("utf-8")
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
            return {
                "status": "error",
                "url": url,
                "error": f"Web Unlocker failed: HTTP {exc.code} {detail[:200]}",
                "via_unlocker": True,
            }
        except Exception as exc:
            return {
                "status": "error",
                "url": url,
                "error": f"Web Unlocker failed: {exc}",
                "via_unlocker": True,
            }

        content = ""
        content_type = ""
        status_code = 200

        try:
            parsed = json.loads(response_text)
            if isinstance(parsed, dict):
                body = parsed.get("body", "")
                if isinstance(body, str):
                    content = body
                status_code = parsed.get("status_code", 200)
                headers = parsed.get("headers", {})
                if isinstance(headers, dict):
                    content_type = headers.get("content-type", headers.get("Content-Type", ""))
        except (json.JSONDecodeError, TypeError):
            content = response_text

        if not content:
            content = response_text

        from zero_api_key_web_search.browse_page import extract_text, extract_markdown

        title = ""
        text = ""
        markdown = ""
        truncated = False
        total_length = len(content)

        if data_format == "markdown" and "<" not in content[:200]:
            markdown = content
            text = content
            title = ""
        else:
            title, text = extract_text(content)
            _, markdown = extract_markdown(content)

        return {
            "status": "success",
            "url": url,
            "title": title,
            "content": markdown if data_format == "markdown" else text,
            "markdown": markdown,
            "text": text,
            "truncated": truncated,
            "total_length": total_length,
            "format": data_format,
            "via_unlocker": True,
        }