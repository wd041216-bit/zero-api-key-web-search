#!/usr/bin/env python3
"""CLI entry point for LLM-optimized search context."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from zero_api_key_web_search.core import LlmContextResult, UltimateSearcher


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build compact, citation-ready search context for LLMs and agents.",
        epilog=(
            "Examples:\n"
            "  zero-context \"Python 3.13 release\"\n"
            "  zero-context \"AI regulation news\" --type news --profile production --json\n"
            "  zero-context \"FastAPI lifespan docs\" --goggles docs-first"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("query", help="Search query to turn into LLM context")
    parser.add_argument(
        "--type",
        choices=["text", "news", "videos", "books", "images"],
        default="text",
        help="Search type (default: text)",
    )
    parser.add_argument("--region", default="wt-wt", help="Region code, e.g. us-en or wt-wt")
    parser.add_argument("--timelimit", choices=["d", "w", "m", "y"], help="Freshness window")
    parser.add_argument(
        "--provider",
        action="append",
        dest="providers",
        help="Search provider to use. Repeat to enable multiple providers.",
    )
    parser.add_argument(
        "--profile",
        choices=["free", "default", "free-verified", "production", "max-evidence"],
        help="Provider profile. Ignored when --provider is supplied.",
    )
    parser.add_argument("--goggles", help="Built-in goggles preset or path to a JSON goggles file")
    parser.add_argument("--max-sources", type=int, default=8, help="Maximum sources in the context pack")
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip the lightweight support/conflict evidence read.",
    )
    parser.add_argument("--json", action="store_true", help="Output structured JSON")

    args = parser.parse_args()
    searcher = UltimateSearcher()
    result: LlmContextResult = searcher.llm_context(
        query=args.query,
        search_type=args.type,
        timelimit=args.timelimit,
        region=args.region,
        providers=args.providers,
        profile=args.profile,
        goggles=args.goggles,
        max_sources=args.max_sources,
        include_verification=not args.no_verify,
    )

    if args.json:
        print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    else:
        print(result.context_markdown)


if __name__ == "__main__":
    main()
