#!/usr/bin/env python3
"""Zero-API-Key Web Search - Web Page Browser and Text Extractor.

Fetches a URL, handles gzip/deflate decompression, and extracts readable
content from HTML pages using BeautifulSoup (with regex fallback).

Supports:
  - HTML-to-Markdown conversion (via markdownify) and plain-text extraction
  - Prompt-based extraction hints for calling agents
  - LRU response cache with 15-minute TTL
  - Cross-host redirect blocking (same-host redirects allowed, max 10 hops)
  - Domain allowlist/blocklist via environment variables
  - Basic PDF text extraction (optional, requires pypdf)
  - Configurable content size limits with truncation markers

Entry point:
    browse-page <url> [--max-chars N] [--format text|markdown] [--json]
"""

import argparse
import gzip
import json
import logging
import os
import re
import urllib.error
import urllib.request
import zlib
from http.client import HTTPResponse
from urllib.parse import urlparse

from zero_api_key_web_search.cache import get_cache
from zero_api_key_web_search.transport import build_ssl_context, insecure_ssl_enabled

logger = logging.getLogger("zero-api-key-web-search")

MAIN_CONTENT_TAGS = {"main", "article", "section", "div"}
MAIN_CONTENT_ROLES = {"main", "article", "content", "main-content"}
BOILERPLATE_TAGS = {"nav", "header", "footer", "aside", "form", "noscript"}
BOILERPLATE_ROLES = {"navigation", "banner", "contentinfo", "complementary", "search"}

MAX_REDIRECT_HOPS = 10

# --- Domain safety ---

_BLOCKED_DOMAINS: list[str] | None = None
_ALLOWED_DOMAINS: list[str] | None = None


def _load_domain_lists() -> None:
    global _BLOCKED_DOMAINS, _ALLOWED_DOMAINS
    block_str = os.getenv("ZERO_SEARCH_BLOCK_DOMAINS", "").strip()
    allow_str = os.getenv("ZERO_SEARCH_ALLOW_DOMAINS", "").strip()
    _BLOCKED_DOMAINS = [d.strip().lower() for d in block_str.split(",") if d.strip()] if block_str else []
    _ALLOWED_DOMAINS = [d.strip().lower() for d in allow_str.split(",") if d.strip()] if allow_str else []


def _check_domain_allowed(url: str) -> tuple[bool, str]:
    """Check whether a URL's domain is allowed. Returns (allowed, reason)."""
    global _BLOCKED_DOMAINS, _ALLOWED_DOMAINS
    if _BLOCKED_DOMAINS is None:
        _load_domain_lists()

    hostname = urlparse(url).hostname or ""

    if _ALLOWED_DOMAINS:
        for allowed in _ALLOWED_DOMAINS:
            if hostname == allowed or hostname.endswith("." + allowed):
                break
        else:
            return False, f"Domain {hostname} not in allowlist"

    if _BLOCKED_DOMAINS:
        for blocked in _BLOCKED_DOMAINS:
            if hostname == blocked or hostname.endswith("." + blocked):
                return False, f"Domain {hostname} in blocklist"

    return True, ""


# --- Redirect handling ---


def _is_same_host(original: str, redirect: str) -> bool:
    """Whether two URLs share the same host, allowing www prefix differences."""
    o = urlparse(original)
    r = urlparse(redirect)
    if o.scheme != r.scheme:
        return False
    if o.port != r.port:
        return False
    # Allow www.example.com <-> example.com
    o_host = (o.hostname or "").lstrip("www.")
    r_host = (r.hostname or "").lstrip("www.")
    return o_host == r_host


class _SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Follow same-host redirects only; block cross-host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not _is_same_host(req.full_url, newurl):
            # Store the redirect info for the caller to handle
            raise _CrossHostRedirect(req.full_url, newurl, code)
        if self.max_redirects <= 0:
            raise urllib.error.HTTPError(req.full_url, code, "Too many redirects", headers, fp)
        self.max_redirects -= 1
        new_req = urllib.request.Request(newurl, headers=req.headers)
        return new_req


class _CrossHostRedirect(Exception):
    """Raised when a redirect goes to a different host."""

    def __init__(self, original_url: str, redirect_url: str, status_code: int):
        self.original_url = original_url
        self.redirect_url = redirect_url
        self.status_code = status_code
        super().__init__(f"Cross-host redirect: {original_url} -> {redirect_url} ({status_code})")


# --- Content extraction ---


def _score_candidate(element) -> float:
    """Score an element's likelihood of being main content."""
    tag = element.name
    score = 0.0

    if tag == "main":
        score += 50
    elif tag == "article":
        score += 40
    elif tag == "section":
        score += 10

    role = element.get("role", "")
    if role in MAIN_CONTENT_ROLES:
        score += 30

    identifiers = " ".join([
        element.get("id", ""),
        " ".join(element.get("class", []) if hasattr(element.get("class", ""), "__iter__") else []),
    ]).lower()
    positive_words = {"content", "article", "post", "entry", "body", "text", "story", "main"}
    negative_words = {
        "nav", "sidebar", "footer", "header", "comment", "social",
        "share", "ad", "promo", "related", "widget",
    }
    for word in positive_words:
        if word in identifiers:
            score += 10
    for word in negative_words:
        if word in identifiers:
            score -= 15

    text = element.get_text(strip=True)
    score += min(len(text) / 50, 30)

    links = element.find_all("a")
    link_text = sum(len(a.get_text(strip=True)) for a in links)
    if len(text) > 0:
        link_ratio = link_text / len(text)
        if link_ratio > 0.4:
            score -= 20
        elif link_ratio > 0.25:
            score -= 10

    if tag in BOILERPLATE_TAGS:
        score -= 30
    if element.get("role", "") in BOILERPLATE_ROLES:
        score -= 30

    return score


def _find_main_content(soup):
    """Find the element most likely to contain main content."""
    for tag in soup.find_all(BOILERPLATE_TAGS):
        tag.decompose()
    for tag in soup.find_all(attrs={"role": lambda v: v in BOILERPLATE_ROLES if v else False}):
        tag.decompose()

    candidates = soup.find_all(MAIN_CONTENT_TAGS)
    if not candidates:
        return soup

    best = max(candidates, key=_score_candidate)
    if _score_candidate(best) > 0:
        return best
    return soup


def extract_text(html: str) -> tuple[str, str]:
    """Extract title and plain text from HTML. Returns (title, text)."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "noscript", "iframe", "svg", "canvas", "form"]):
            tag.decompose()
        title = soup.title.get_text(strip=True) if soup.title else "Unknown Title"
        main = _find_main_content(soup)
        text = main.get_text(separator=" ", strip=True)
        text = re.sub(r"\s+", " ", text)
        return title, text
    except ImportError:
        title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.DOTALL)
        title = "Unknown Title"
        if title_match:
            title = re.sub(r"<[^>]+>", "", title_match.group(1)).strip()
            title = re.sub(r"\s+", " ", title)
        text = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.I)
        text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL | re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return title, text


def extract_markdown(html: str) -> tuple[str, str]:
    """Extract title and Markdown-formatted content from HTML. Returns (title, markdown)."""
    try:
        from markdownify import MarkdownConverter
    except ImportError:
        logger.warning("markdownify not installed, falling back to plain text extraction")
        return extract_text(html)

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "lxml")

    # Remove non-content tags
    for tag in soup(["script", "style", "noscript", "iframe", "svg", "canvas", "form"]):
        tag.decompose()

    title = soup.title.get_text(strip=True) if soup.title else "Unknown Title"

    # Find main content
    main = _find_main_content(soup)

    # Convert to Markdown
    md = MarkdownConverter(
        heading_style="atx",
        bullets="-",
        code_language="",
    ).convert_soup(main)

    # Clean up excessive whitespace
    md = re.sub(r"\n{3,}", "\n\n", md)
    md = md.strip()

    return title, md


def _extract_pdf_text(raw: bytes) -> str:
    """Try to extract text from PDF bytes. Returns empty string if pypdf unavailable."""
    try:
        from io import BytesIO
        from pypdf import PdfReader
        reader = PdfReader(BytesIO(raw))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n\n".join(pages)
    except ImportError:
        return ""
    except Exception as e:
        logger.warning("PDF extraction failed: %s", e)
        return ""


def _try_web_unlocker(url: str, max_chars: int, format: str) -> dict | None:
    """Attempt to fetch a URL via Bright Data Web Unlocker.

    Returns None if Web Unlocker is not configured or fails silently.
    """
    try:
        from zero_api_key_web_search.providers.web_unlocker import WebUnlockerProvider
    except ImportError:
        return None

    provider = WebUnlockerProvider()
    if not provider.is_configured():
        return None

    data_format = "markdown" if format == "markdown" else "raw"
    try:
        result = provider.unlock(url, data_format=data_format)
    except Exception as e:
        logger.info("web_unlocker_fallback_failed: url=%r error=%s", url, e)
        return None

    if result.get("status") != "success":
        logger.info("web_unlocker_fallback_failed: url=%r status=%s", url, result.get("status"))
        return None

    content = result.get("content", "")
    markdown_content = result.get("markdown", content)
    text_content = result.get("text", content)
    title = result.get("title", "")

    output = markdown_content if format == "markdown" else text_content
    is_truncated = len(output) > max_chars
    truncated_output = output[:max_chars]
    if is_truncated:
        truncated_output += f"\n[Content truncated at {max_chars} chars. Total length: {len(output)}.]"

    return {
        "status": "success",
        "url": url,
        "title": title,
        "content": truncated_output,
        "markdown": markdown_content[:max_chars],
        "text": text_content[:max_chars],
        "truncated": is_truncated,
        "total_length": len(output),
        "format": format,
        "via_unlocker": True,
        "insecure_ssl": insecure_ssl_enabled(),
    }


def browse(url: str, max_chars: int = 50000, format: str = "markdown",
           prompt: str | None = None, use_unlocker: bool | None = None) -> dict:
    """Fetch a URL and return its extracted content.

    Args:
        url: The URL to fetch and extract content from.
        max_chars: Maximum characters in the content field (default: 50000).
        format: Output format — 'markdown' (default) or 'text'.
        prompt: Optional extraction hint for the calling agent. When provided,
            included in the response as prompt_hint for the agent's LLM to focus on.
        use_unlocker: Web Unlocker mode for blocked/geo-restricted pages.
            None (default): auto — use Web Unlocker when direct fetch fails with 403/429.
            True: always use Web Unlocker.
            False: never use Web Unlocker.

    Returns:
        Dict with:
            - status: 'success', 'redirect', 'blocked', or 'error'
            - url: The requested URL
            - title: Page title (on success)
            - content: Extracted content (markdown or text, truncated to max_chars)
            - markdown: Markdown-formatted content (always included on success)
            - text: Plain text content (always included on success)
            - truncated: Whether content was truncated
            - total_length: Full content length
            - format: The format used
            - prompt_hint: The prompt, if provided
            - via_unlocker: True if content was fetched via Web Unlocker
            - insecure_ssl: Whether insecure SSL was enabled
    """
    # Domain safety check
    allowed, reason = _check_domain_allowed(url)
    if not allowed:
        return {
            "status": "blocked",
            "url": url,
            "domain": urlparse(url).hostname or "",
            "reason": reason,
        }

    # Web Unlocker: when use_unlocker=True, skip direct fetch and go straight to unlocker
    if use_unlocker is True:
        unlocker_result = _try_web_unlocker(url, max_chars, format)
        if unlocker_result is not None:
            return unlocker_result
        # Fall through to direct fetch if unlocker fails

    # Check cache
    cache = get_cache()
    cache_key = f"browse:{url}:{format}:u={use_unlocker}"
    cached = cache.get(cache_key)
    if cached is not None:
        cached_text = cached[0]
        # Return cached result (still apply truncation)
        content = cached_text[:max_chars]
        is_truncated = len(cached_text) > max_chars
        result = {
            "status": "success",
            "url": url,
            "title": "(from cache)",
            "content": content,
            "truncated": is_truncated,
            "total_length": len(cached_text),
            "format": format,
            "insecure_ssl": insecure_ssl_enabled(),
            "from_cache": True,
        }
        if format == "markdown" or format == "text":
            result["markdown"] = content
            result["text"] = content
        if prompt:
            result["prompt_hint"] = prompt
        if is_truncated:
            result["truncation_marker"] = f"[Content truncated at {max_chars} chars. Total length: {len(cached_text)}.]"
        return result

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate",
    }

    context = build_ssl_context()

    try:
        logger.info("browse: url=%r max_chars=%d format=%s", url, max_chars, format)
        req = urllib.request.Request(url, headers=headers)
        redirect_handler = _SafeRedirectHandler()
        redirect_handler.max_redirects = MAX_REDIRECT_HOPS
        opener = urllib.request.build_opener(redirect_handler, urllib.request.HTTPSHandler(context=context))

        try:
            r: HTTPResponse = opener.open(req, timeout=15)
        except _CrossHostRedirect as e:
            return {
                "status": "redirect",
                "original_url": e.original_url,
                "redirect_url": e.redirect_url,
                "status_code": e.status_code,
            }

        raw = r.read()
        content_type = r.headers.get("Content-Type", "")
        encoding = r.headers.get("Content-Encoding", "")

        # Decompress
        if encoding == "gzip":
            html = gzip.decompress(raw).decode("utf-8", errors="ignore")
        elif encoding == "deflate":
            html = zlib.decompress(raw).decode("utf-8", errors="ignore")
        else:
            html = raw.decode("utf-8", errors="ignore")

        # Handle PDF
        if "application/pdf" in content_type:
            pdf_text = _extract_pdf_text(raw)
            if pdf_text:
                title = "PDF Document"
                text = pdf_text
                md = pdf_text
            else:
                return {
                    "status": "success",
                    "url": url,
                    "title": "PDF Document",
                    "content": "[PDF content — install pypdf for text extraction: pip install zero-api-key-web-search[pdf]]",
                    "markdown": "[PDF content — install pypdf for text extraction: pip install zero-api-key-web-search[pdf]]",
                    "text": "[PDF content — install pypdf for text extraction: pip install zero-api-key-web-search[pdf]]",
                    "truncated": False,
                    "total_length": 0,
                    "format": format,
                    "insecure_ssl": insecure_ssl_enabled(),
                }

        # Handle non-HTML content types
        elif "text/html" not in content_type and "application/xhtml" not in content_type:
            # For plain text, JSON, etc. — return as-is
            title = urlparse(url).path.split("/")[-1] or "Document"
            text = html[:max_chars]
            md = html[:max_chars]
        else:
            # HTML — extract content
            title, text = extract_text(html)
            _, md = extract_markdown(html)

        # Select output format
        if format == "text":
            output = text
        else:
            output = md

        # Truncation
        is_truncated = len(output) > max_chars
        content = output[:max_chars]

        result = {
            "status": "success",
            "url": url,
            "title": title,
            "content": content,
            "truncated": is_truncated,
            "total_length": len(output),
            "format": format,
            "markdown": md,
            "text": text,
            "insecure_ssl": insecure_ssl_enabled(),
        }

        if is_truncated:
            result["truncation_marker"] = f"[Content truncated at {max_chars} chars. Total length: {len(output)}.]"
        if prompt:
            result["prompt_hint"] = prompt

        # Cache the full content (not truncated)
        cache.put(cache_key, output, f"text/{format}")

        return result

    except urllib.error.HTTPError as e:
        logger.error("browse_http_error: url=%r code=%s", url, e.code)
        # Auto-fallback to Web Unlocker for 403/429 (blocked/CAPTCHA/geo-restricted)
        unlocker_auto = os.getenv("ZERO_SEARCH_BRIGHTDATA_UNLOCKER_AUTO", "1").strip() not in ("0", "false", "no", "disabled")
        if use_unlocker is not False and unlocker_auto and e.code in (403, 429):
            unlocker_result = _try_web_unlocker(url, max_chars, format)
            if unlocker_result is not None:
                return unlocker_result
        return {
            "status": "error",
            "url": url,
            "error": f"HTTP {e.code}: {e.reason}",
            "insecure_ssl": insecure_ssl_enabled(),
        }
    except Exception as e:
        logger.error("browse_error: url=%r error=%s", url, e)
        return {
            "status": "error",
            "url": url,
            "error": str(e),
            "insecure_ssl": insecure_ssl_enabled(),
        }


def main():
    """CLI entry point for browse-page command."""
    parser = argparse.ArgumentParser(
        description="Zero-API-Key Web Search page reader (package: zero-api-key-web-search)",
        epilog=(
            "Examples:\n"
            "  browse-page https://example.com\n"
            "  browse-page https://example.com --max-chars 5000 --format markdown --json"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("url", help="URL to fetch and extract content from")
    parser.add_argument(
        "--max-chars",
        type=int,
        default=50000,
        help="Maximum characters to return (default: 50000)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "markdown"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON",
    )

    args = parser.parse_args()
    result = browse(args.url, max_chars=args.max_chars, format=args.format)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        if result["status"] == "success":
            print(f"\n{result['title']}")
            print(f"{result['url']}")
            print(f"{'='*60}\n")
            print(result["content"])
            if result.get("truncated"):
                print(f"\n{result.get('truncation_marker', '')}")
        elif result["status"] == "redirect":
            print(f"Cross-host redirect: {result['original_url']} -> {result['redirect_url']} ({result['status_code']})")
        elif result["status"] == "blocked":
            print(f"Domain blocked: {result['domain']} ({result['reason']})")
        else:
            print(f"Error browsing {result['url']}: {result['error']}")


if __name__ == "__main__":
    main()