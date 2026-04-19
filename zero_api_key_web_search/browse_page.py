#!/usr/bin/env python3
"""Cross-Validated Search - Web Page Browser and Text Extractor.

Fetches a URL, handles gzip/deflate decompression, and extracts readable
text content using BeautifulSoup (with a regex fallback).

Entry point:
    browse-page <url> [--max-chars N] [--json]
"""
import argparse
import gzip
import json
import logging
import re
import urllib.request

from zero_api_key_web_search.transport import build_ssl_context, insecure_ssl_enabled

logger = logging.getLogger("zero-api-key-web-search")

MAIN_CONTENT_TAGS = {"main", "article", "section", "div"}
MAIN_CONTENT_ROLES = {"main", "article", "content", "main-content"}
BOILERPLATE_TAGS = {"nav", "header", "footer", "aside", "form", "noscript"}
BOILERPLATE_ROLES = {"navigation", "banner", "contentinfo", "complementary", "search"}


def _score_candidate(element) -> float:
    """Score an element's likelihood of being main content."""
    tag = element.name
    score = 0.0

    # Semantic HTML5 main content tags
    if tag == "main":
        score += 50
    elif tag == "article":
        score += 40
    elif tag == "section":
        score += 10

    # ARIA / role attribute
    role = element.get("role", "")
    if role in MAIN_CONTENT_ROLES:
        score += 30

    # ID/class heuristics
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

    # Text density: longer text blocks are more likely main content
    text = element.get_text(strip=True)
    score += min(len(text) / 50, 30)

    # Link density: high link ratio suggests nav/sidebar
    links = element.find_all("a")
    link_text = sum(len(a.get_text(strip=True)) for a in links)
    if len(text) > 0:
        link_ratio = link_text / len(text)
        if link_ratio > 0.4:
            score -= 20
        elif link_ratio > 0.25:
            score -= 10

    # Penalize boilerplate tags
    if tag in BOILERPLATE_TAGS:
        score -= 30
    if element.get("role", "") in BOILERPLATE_ROLES:
        score -= 30

    return score


def _find_main_content(soup):
    """Find the element most likely to contain main content."""
    # Remove boilerplate tags before scoring
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


def extract_text(html: str):
    """Extract the title and readable text content from an HTML string.

    Uses a readability-style heuristic to find the main content area,
    then extracts clean text from it. Falls back to full-page text if
    no main content candidate is found.

    Uses BeautifulSoup with lxml if available; falls back to regex otherwise.

    Args:
        html: Raw HTML string to parse.

    Returns:
        A tuple of (title, text) where title is the page title (or
        'Unknown Title' if not found) and text is the cleaned body text
        with excess whitespace collapsed.
    """
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")

        # Remove tags that never contain useful content
        for tag in soup(["script", "style", "noscript", "iframe", "svg", "canvas", "form"]):
            tag.decompose()

        title = "Unknown Title"
        if soup.title:
            title = soup.title.get_text(strip=True) or "Unknown Title"

        # Find main content using readability heuristic
        main = _find_main_content(soup)
        text = main.get_text(separator=" ", strip=True)
        text = re.sub(r"\s+", " ", text)

        return title, text
    except ImportError:
        # Regex fallback when BeautifulSoup is not installed
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


def browse(url: str, max_chars: int = 10000) -> dict:
    """Fetch a URL and return its extracted text content.

    Handles gzip and deflate content encoding automatically.
    Truncates the output to max_chars characters.

    Args:
        url: The URL to fetch and extract text from.
        max_chars: Maximum number of characters to return in the content
            field (default: 10000). The full length is always reported.

    Returns:
        A dict with the following keys on success:
            - status (str): 'success'
            - url (str): The requested URL.
            - title (str): The page title.
            - content (str): Extracted text, truncated to max_chars.
            - truncated (bool): True if the content was truncated.
            - total_length (int): Full length of the extracted text.

        On error, returns:
            - status (str): 'error'
            - url (str): The requested URL.
            - error (str): The error message.
    """
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
        logger.info("browse: url=%r max_chars=%d", url, max_chars)
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15, context=context) as r:
            raw = r.read()
            encoding = r.headers.get("Content-Encoding", "")

            if encoding == "gzip":
                html = gzip.decompress(raw).decode("utf-8", errors="ignore")
            elif encoding == "deflate":
                import zlib
                html = zlib.decompress(raw).decode("utf-8", errors="ignore")
            else:
                html = raw.decode("utf-8", errors="ignore")

            title, text = extract_text(html)
            content = text[:max_chars]
            is_truncated = len(text) > max_chars

            return {
                "status": "success",
                "url": url,
                "title": title,
                "content": content,
                "truncated": is_truncated,
                "total_length": len(text),
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
            "  browse-page https://example.com --max-chars 5000 --json"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("url", help="URL to fetch and extract text from")
    parser.add_argument(
        "--max-chars",
        type=int,
        default=10000,
        help="Maximum characters to return (default: 10000)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON",
    )

    args = parser.parse_args()
    result = browse(args.url, args.max_chars)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        if result["status"] == "success":
            print(f"\n📄 {result['title']}")
            print(f"🔗 {result['url']}")
            print(f"{'='*60}\n")
            print(result["content"])
            if result["truncated"]:
                print(
                    f"\n... [Truncated. Total length: {result['total_length']} chars]"
                )
        else:
            print(f"❌ Error browsing {result['url']}: {result['error']}")


if __name__ == "__main__":
    main()
