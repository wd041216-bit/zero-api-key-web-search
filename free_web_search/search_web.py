#!/usr/bin/env python3
"""Free Web Search Ultimate - Universal Search Core (v13.0).

Supports standard Python package entry_points, REPL interactive mode,
and SKILL.md auto-discovery for CLI-Anything compatibility.

Entry points:
    search-web: Main CLI for web/news/image/video/book search
    browse-page: Page content extractor
    free-web-search-mcp: MCP server for LLM tool use
"""
import argparse
import json
import os
import re
import ssl
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional

# Disable SSL verification globally to handle restrictive network environments
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


@dataclass
class Source:
    """A single search result source.

    Attributes:
        url: The URL of the source.
        title: The title of the page or article.
        snippet: A short excerpt or description.
        rank: The result rank (1-based, assigned after deduplication).
        engine: The search engine that returned this result.
        cross_validated: Whether this URL appeared in multiple engine results.
        date: Publication or update date (if available).
        extra: Additional type-specific metadata (e.g., image dimensions).
    """

    url: str
    title: str
    snippet: str = ""
    rank: int = 0
    engine: str = ""
    cross_validated: bool = False
    date: str = ""
    extra: Dict = None

    def __post_init__(self):
        if self.extra is None:
            self.extra = {}


@dataclass
class Answer:
    """The complete answer returned by UltimateSearcher.search().

    Attributes:
        query: The original search query.
        search_type: The type of search performed (text, news, images, etc.).
        answer: A brief markdown-formatted summary of the top sources.
        confidence: Confidence level: HIGH, MEDIUM, or LOW.
        sources: List of deduplicated and ranked Source objects.
        validation: Statistics about result counts and cross-validation.
        metadata: Engine usage info and any errors encountered.
        elapsed_ms: Total search time in milliseconds.
    """

    query: str
    search_type: str
    answer: str
    confidence: str
    sources: List[Source]
    validation: Dict
    metadata: Dict
    elapsed_ms: int


class UltimateSearcher:
    """Universal web searcher using DuckDuckGo with cross-validation.

    Supports text, news, images, videos, and books search types.
    Results are deduplicated and ranked by cross-validation confidence.

    Example:
        searcher = UltimateSearcher()
        answer = searcher.search("Python 3.12 release notes")
        for source in answer.sources[:5]:
            print(source.title, source.url)
    """

    def __init__(self, timeout: int = 15):
        """Initialize the searcher.

        Args:
            timeout: HTTP request timeout in seconds (default: 15).
        """
        self.timeout = timeout

    def _search_ddgs(
        self,
        query: str,
        search_type: str,
        timelimit: Optional[str] = None,
        region: str = "wt-wt",
        max_results: int = 15,
        **kwargs,
    ) -> List[Source]:
        """Perform a search using the ddgs library (thread-safe, new instance per call).

        Args:
            query: The search query string.
            search_type: One of 'text', 'news', 'videos', 'books', 'images'.
            timelimit: Time filter — 'd' (day), 'w' (week), 'm' (month), 'y' (year),
                or None for no limit.
            region: DuckDuckGo region code, e.g. 'wt-wt' (global), 'zh-cn', 'en-us'.
            max_results: Maximum number of raw results to fetch.
            **kwargs: Additional type-specific parameters (e.g., size, color for images).

        Returns:
            A list of Source objects. On error, returns a single Source with
            url='error' and the error message in title.
        """
        results = []
        try:
            from ddgs import DDGS
            with DDGS(timeout=self.timeout) as ddgs:
                if search_type == "text":
                    api_results = ddgs.text(
                        query,
                        region=region,
                        max_results=max_results,
                        timelimit=timelimit,
                    )
                elif search_type == "news":
                    api_results = ddgs.news(
                        query,
                        region=region,
                        max_results=max_results,
                        timelimit=timelimit,
                    )
                elif search_type == "videos":
                    api_results = ddgs.videos(
                        query,
                        region=region,
                        max_results=max_results,
                        timelimit=timelimit,
                    )
                elif search_type == "books":
                    api_results = ddgs.books(query, max_results=max_results)
                elif search_type == "images":
                    # Images API supports rich kwargs; auto-fallback on size errors
                    img_size = kwargs.get("size") or "Wallpaper"
                    size_fallbacks = [img_size, "Wallpaper", "Small", "Large", "Medium"]
                    api_results = None
                    for try_size in size_fallbacks:
                        try:
                            api_results = ddgs.images(
                                query,
                                region=region,
                                max_results=max_results,
                                timelimit=timelimit,
                                size=try_size,
                                color=kwargs.get("color"),
                                type_image=kwargs.get("type_image"),
                                layout=kwargs.get("layout"),
                                license_image=kwargs.get("license_image"),
                            )
                            break
                        except Exception:
                            continue
                    if api_results is None:
                        api_results = []
                else:
                    return []

                for r in api_results:
                    url = r.get("href", r.get("url", r.get("content", "")))
                    if not url:
                        continue

                    source = Source(
                        url=url,
                        title=r.get("title", ""),
                        snippet=r.get("body", r.get("description", "")),
                        rank=0,  # Assigned later after deduplication
                        engine=f"DDG-{search_type.capitalize()}",
                        date=r.get("date", r.get("published", "")),
                        extra={},
                    )

                    # Extract type-specific extra metadata
                    if search_type == "videos":
                        source.extra["duration"] = r.get("duration")
                        source.extra["publisher"] = r.get("publisher")
                    elif search_type == "books":
                        source.extra["author"] = r.get("author")
                        source.extra["year"] = r.get("year")
                    elif search_type == "images":
                        # For images, 'image' field is the direct image URL;
                        # 'href'/'url' is the source page URL
                        source.url = r.get("image", url)
                        source.extra["source_url"] = url
                        source.extra["thumbnail"] = r.get("thumbnail")
                        source.extra["width"] = r.get("width")
                        source.extra["height"] = r.get("height")
                        source.extra["source"] = r.get("source")

                    results.append(source)
        except Exception as e:
            results.append(
                Source(url="error", title=f"Error: {str(e)}", engine="error")
            )
        return results

    def _search_tavily(
        self,
        query: str,
        search_type: str,
        timelimit: Optional[str] = None,
        region: str = "wt-wt",
        max_results: int = 15,
        **kwargs,
    ) -> List[Source]:
        """Perform a search using the Tavily API.

        Only supports 'text' and 'news' search types. For other types,
        returns an empty list so the caller falls back to DuckDuckGo.

        Args:
            query: The search query string.
            search_type: One of 'text', 'news'. Other types return [].
            timelimit: Time filter (mapped to Tavily time_range parameter).
            region: Unused (Tavily does not support region filtering).
            max_results: Maximum number of results to fetch.
            **kwargs: Additional parameters (unused).

        Returns:
            A list of Source objects. On error, returns a single Source with
            url='error' and the error message in title.
        """
        if search_type not in ("text", "news"):
            return []

        results = []
        try:
            from tavily import TavilyClient

            client = TavilyClient()

            # Map timelimit to Tavily's time_range parameter
            time_range_map = {"d": "day", "w": "week", "m": "month", "y": "year"}
            tavily_kwargs = {
                "query": query,
                "max_results": max_results,
                "search_depth": "advanced",
            }
            if search_type == "news":
                tavily_kwargs["topic"] = "news"
            if timelimit and timelimit in time_range_map:
                tavily_kwargs["time_range"] = time_range_map[timelimit]

            response = client.search(**tavily_kwargs)

            for r in response.get("results", []):
                url = r.get("url", "")
                if not url:
                    continue
                results.append(Source(
                    url=url,
                    title=r.get("title", ""),
                    snippet=r.get("content", ""),
                    rank=0,
                    engine=f"Tavily-{search_type.capitalize()}",
                    date=r.get("published_date", ""),
                    extra={"score": r.get("score")},
                ))
        except Exception as e:
            results.append(
                Source(url="error", title=f"Error: {str(e)}", engine="error")
            )
        return results

    def _cross_validate(self, all_results: List[Source]) -> List[Source]:
        """Deduplicate results and assign ranks based on cross-validation.

        URLs are normalized (scheme and www stripped) before grouping.
        Results appearing from multiple engines are marked as cross-validated
        and ranked higher.

        Args:
            all_results: Raw list of Source objects from all engines.

        Returns:
            Deduplicated and ranked list of Source objects, sorted with
            cross-validated results first.
        """
        url_groups: Dict[str, List[Source]] = {}
        for r in all_results:
            if r.url == "error":
                continue

            simplified = re.sub(r"^https?://(www\.)?", "", r.url).rstrip("/")
            simplified = simplified.split("#")[0].split("?")[0]

            if not simplified:
                continue

            if simplified not in url_groups:
                url_groups[simplified] = []
            url_groups[simplified].append(r)

        validated = []
        for url, group in url_groups.items():
            best_source = group[0]

            if len(group) >= 2:
                best_source.cross_validated = True
                best_source.engine = f"{best_source.engine} (x{len(group)})"

            # Use the longest snippet available across duplicates
            valid_snippets = [s.snippet for s in group if len(s.snippet) > 20]
            if valid_snippets:
                best_source.snippet = max(valid_snippets, key=len)

            validated.append(best_source)

        # Cross-validated results first, then by original order
        validated.sort(key=lambda x: x.cross_validated, reverse=True)

        # Assign 1-based ranks
        for i, s in enumerate(validated, 1):
            s.rank = i

        return validated

    def search(
        self,
        query: str,
        search_type: str = "text",
        timelimit: Optional[str] = None,
        region: str = "wt-wt",
        **kwargs,
    ) -> Answer:
        """Search the web and return a structured Answer.

        Args:
            query: The search query string.
            search_type: Type of search — 'text' (default), 'news', 'images',
                'videos', or 'books'.
            timelimit: Time filter — 'd' (past day), 'w' (past week),
                'm' (past month), 'y' (past year), or None for no limit.
            region: DuckDuckGo region code (default: 'wt-wt' for global).
                Use 'zh-cn' for Chinese results, 'en-us' for US English, etc.
            **kwargs: Additional type-specific parameters forwarded to the
                underlying search engine (e.g., size='Large' for images).

        Returns:
            An Answer object containing the query, sources, confidence level,
            validation statistics, and elapsed time.

        Example:
            searcher = UltimateSearcher()
            answer = searcher.search(
                "OpenAI GPT-4o release",
                search_type="news",
                timelimit="w",
            )
            print(answer.confidence)   # HIGH / MEDIUM / LOW
            print(answer.sources[0].url)
        """
        start_time = time.time()

        # Fetch enough results in a single request to avoid wasted network calls
        max_results = 30 if search_type == "text" else 20

        # Build engine list — Tavily added in parallel when API key is available
        engines = [(self._search_ddgs, query, search_type, timelimit, region, max_results)]
        if os.environ.get("TAVILY_API_KEY") and search_type in ("text", "news"):
            engines.append((self._search_tavily, query, search_type, timelimit, region, max_results))

        all_results = []
        errors = []
        with ThreadPoolExecutor(max_workers=len(engines)) as executor:
            futures = [
                executor.submit(e[0], e[1], e[2], e[3], e[4], e[5], **kwargs)
                for e in engines
            ]
            for future in as_completed(futures):
                res = future.result()
                for r in res:
                    if r.url == "error":
                        errors.append(r.title)
                    else:
                        all_results.append(r)

        validated_results = self._cross_validate(all_results)

        # Build a concise markdown summary of the top 5 sources
        if validated_results:
            answer_parts = []
            for i, s in enumerate(validated_results[:5], 1):
                badge = "✓" if s.cross_validated else "○"
                answer_parts.append(f"{i}. {badge} [{s.title}]({s.url})")
            answer_text = "Top Sources:\n" + "\n".join(answer_parts)
        else:
            error_detail = f" (Errors: {'; '.join(errors)})" if errors else ""
            answer_text = f"No results found. The search engine may be rate-limited.{error_detail}"

        cross_count = sum(1 for s in validated_results if s.cross_validated)
        confidence = "HIGH" if cross_count >= 2 else ("MEDIUM" if validated_results else "LOW")

        return Answer(
            query=query,
            search_type=search_type,
            answer=answer_text,
            confidence=confidence,
            sources=validated_results[:max_results],
            validation={
                "total_results": len(all_results),
                "unique_results": len(validated_results),
                "cross_validated": cross_count,
            },
            metadata={
                "engines_used": [e[2] for e in engines],
                "errors": errors,
            },
            elapsed_ms=int((time.time() - start_time) * 1000),
        )


def main():
    """CLI entry point for search-web command."""
    parser = argparse.ArgumentParser(
        description="Free Web Search Ultimate (v13.0)",
        epilog=(
            "Examples:\n"
            "  search-web \"Python 3.12\"\n"
            "  search-web \"OpenAI\" --type news\n"
            "  search-web \"AI news\" --type news --timelimit w\n"
            "  search-web  # Run without arguments to enter REPL mode"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="Search query (omit to enter REPL mode)",
    )
    parser.add_argument(
        "--type",
        choices=["text", "news", "videos", "books", "images"],
        default="text",
        help="Search type (default: text)",
    )
    parser.add_argument(
        "--region",
        default="wt-wt",
        help="Region code, e.g. zh-cn, en-us, wt-wt (global)",
    )
    parser.add_argument(
        "--timelimit",
        choices=["d", "w", "m", "y"],
        help="Time limit: d (day), w (week), m (month), y (year)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format",
    )

    # Image-specific parameters
    parser.add_argument(
        "--size",
        choices=["Small", "Medium", "Large", "Wallpaper"],
        help="[images] Image size filter",
    )
    parser.add_argument(
        "--color",
        help="[images] Color filter, e.g. Red, Blue, Monochrome",
    )
    parser.add_argument(
        "--type_image",
        choices=["photo", "clipart", "gif", "transparent", "line"],
        help="[images] Image type filter",
    )
    parser.add_argument(
        "--license",
        choices=["any", "Public", "Share", "ShareCommercially", "Modify", "ModifyCommercially"],
        help="[images] License filter",
    )

    args = parser.parse_args()

    searcher = UltimateSearcher()

    # REPL mode (no query provided)
    if not args.query:
        import os
        import sys

        skill_path = os.path.join(os.path.dirname(__file__), "skills", "SKILL.md")
        skill_msg = f"\n📖 SKILL.md: {skill_path}" if os.path.exists(skill_path) else ""

        print(f"\n{'='*60}")
        print("🔍 Free Web Search Ultimate REPL (v13.0)")
        print("Type your query and press Enter. Type 'exit' or 'quit' to quit.")
        print("Advanced options can be appended after the query, e.g.:")
        print("  apple --type news")
        print("  python --region zh-cn --timelimit w" + skill_msg)
        print(f"{'='*60}\n")

        while True:
            try:
                user_input = input("\nsearch-web> ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ["exit", "quit"]:
                    break

                repl_args = user_input.split()
                try:
                    parsed_repl = parser.parse_args(repl_args)
                except SystemExit:
                    continue  # Suppress argparse exit; keep REPL running

                kwargs = {}
                if parsed_repl.size:
                    kwargs["size"] = parsed_repl.size
                if parsed_repl.color:
                    kwargs["color"] = parsed_repl.color
                if parsed_repl.type_image:
                    kwargs["type_image"] = parsed_repl.type_image
                if parsed_repl.license:
                    kwargs["license_image"] = parsed_repl.license

                if parsed_repl.query:
                    answer = searcher.search(
                        parsed_repl.query,
                        search_type=parsed_repl.type,
                        timelimit=parsed_repl.timelimit,
                        region=parsed_repl.region,
                        **kwargs,
                    )
                    print(
                        f"\n⏱  {answer.elapsed_ms}ms | "
                        f"{answer.validation['unique_results']} results | "
                        f"confidence: {answer.confidence}"
                    )
                    if answer.sources:
                        for s in answer.sources[:5]:
                            print(f"  {s.rank}. [{s.engine}] {s.title[:60]}")
                            print(f"     {s.url}")
            except KeyboardInterrupt:
                break
            except EOFError:
                break
        return

    # Single-query mode
    kwargs = {}
    if args.size:
        kwargs["size"] = args.size
    if args.color:
        kwargs["color"] = args.color
    if args.type_image:
        kwargs["type_image"] = args.type_image
    if args.license:
        kwargs["license_image"] = args.license

    answer = searcher.search(
        args.query,
        search_type=args.type,
        timelimit=args.timelimit,
        region=args.region,
        **kwargs,
    )

    if args.json:
        print(json.dumps(asdict(answer), indent=2, ensure_ascii=False))
    else:
        print(f"\n{'='*60}")
        print(
            f"🔍 Query: {answer.query} "
            f"(type: {answer.search_type} | region: {args.region})"
        )
        print(
            f"⏱  {answer.elapsed_ms}ms | "
            f"confidence: {answer.confidence}"
        )
        print(
            f"📊 {answer.validation['unique_results']} unique results "
            f"({answer.validation['cross_validated']} cross-validated)"
        )
        if answer.metadata["errors"]:
            print(f"⚠  {len(answer.metadata['errors'])} engine error(s)")
        print(f"{'='*60}\n")

        if answer.sources:
            print("📋 Summary:\n")
            print(answer.answer)
            print(f"\n{'-'*60}")
            print("🔗 Sources:")
            for s in answer.sources:
                badge = "✓" if s.cross_validated else "○"
                date_str = f" [{s.date}]" if s.date else ""
                extra_str = f" {s.extra}" if s.extra else ""
                print(
                    f"  {s.rank}. {badge} [{s.engine}] "
                    f"{s.title[:60]}{date_str}{extra_str}"
                )
                print(f"     URL: {s.url}")
        else:
            print("❌ No results found.")


if __name__ == "__main__":
    main()
