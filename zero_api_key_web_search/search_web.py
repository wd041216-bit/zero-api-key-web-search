#!/usr/bin/env python3
"""CLI entry point for the stable search-web command."""

import argparse
import json
from dataclasses import asdict

from zero_api_key_web_search.core import (  # noqa: F401
    Answer,
    Source,
    UltimateSearcher,
)


def main():
    """CLI entry point for search-web command."""
    parser = argparse.ArgumentParser(
        description="Zero-API-Key Web Search CLI (package: zero-api-key-web-search)",
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
    parser.add_argument(
        "--provider",
        action="append",
        dest="providers",
        help="Search provider to use. Repeat to enable multiple providers, e.g. --provider ddgs --provider searxng",
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

        skill_path = os.path.join(os.path.dirname(__file__), "skills", "SKILL.md")
        skill_msg = f"\n📖 SKILL.md: {skill_path}" if os.path.exists(skill_path) else ""

        print(f"\n{'='*60}")
        print("🔍 Cross-Validated Search REPL")
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
                        providers=parsed_repl.providers,
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
        providers=args.providers,
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
