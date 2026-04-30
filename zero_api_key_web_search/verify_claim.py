#!/usr/bin/env python3
"""CLI entry point for the verify-claim command."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from zero_api_key_web_search.core import UltimateSearcher, VerificationResult


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify a factual claim using corroborating and conflicting search evidence.",
        epilog=(
            "Examples:\n"
            "  verify-claim \"Python 3.13 is the latest stable release\"\n"
            "  verify-claim \"OpenAI released GPT-5 this week\" --timelimit w --json"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("claim", help="Claim to verify against live search results")
    parser.add_argument(
        "--region",
        default="wt-wt",
        help="Region code, e.g. zh-cn, en-us, wt-wt (global)",
    )
    parser.add_argument(
        "--timelimit",
        choices=["d", "w", "m", "y"],
        help="Optional freshness window for the underlying search query",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output the verification result as JSON",
    )
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
    parser.add_argument(
        "--goggles",
        help="Built-in goggles preset or path to a JSON goggles file for reranking/filtering.",
    )
    parser.add_argument(
        "--with-pages",
        action="store_true",
        help="Fetch the top source pages and use page content to refine classification.",
    )
    parser.add_argument(
        "--deep",
        action="store_true",
        help="Alias for --with-pages. Enables page-aware verification.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=3,
        help="Maximum number of pages to fetch when --with-pages is enabled (default: 3).",
    )
    parser.add_argument(
        "--page-max-chars",
        type=int,
        default=4000,
        help="Maximum characters to read from each fetched page (default: 4000).",
    )

    args = parser.parse_args()
    searcher = UltimateSearcher()
    result: VerificationResult = searcher.verify_claim(
        claim=args.claim,
        region=args.region,
        timelimit=args.timelimit,
        providers=args.providers,
        profile=args.profile,
        goggles=args.goggles,
        include_pages=args.with_pages or args.deep,
        deep=args.deep,
        max_pages=args.max_pages,
        page_max_chars=args.page_max_chars,
    )

    if args.json:
        print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
        return

    print(f"\n{'='*60}")
    print(f"🔎 Claim: {result.claim}")
    print(f"Verdict: {result.verdict}")
    print(f"Confidence: {result.confidence}")
    print(result.summary)
    print(
        "Evidence model: "
        f"{result.analysis['verification_model']['name']} | "
        f"support={result.analysis['support_score']:.2f} | "
        f"conflict={result.analysis['conflict_score']:.2f} | "
        f"domains={result.analysis['domain_diversity']} | "
        f"providers={result.analysis['provider_diversity']} | "
        f"pages={result.analysis['page_fetches_succeeded']}/{result.analysis['page_fetches_attempted']}"
    )
    print(f"{'='*60}\n")

    def print_sources(label: str, sources: list) -> None:
        if not sources:
            return
        print(f"{label}:")
        for index, source in enumerate(sources, 1):
            evidence = source.extra.get("verification", {})
            overlap = evidence.get("keyword_overlap", 0)
            strength = evidence.get("evidence_strength", 0)
            quality = evidence.get("source_quality", {})
            freshness = evidence.get("freshness", {})
            print(f"  {index}. [{source.title}]({source.url})")
            print(
                "     "
                f"overlap={overlap} "
                f"strength={strength} "
                f"quality={quality.get('tier', 'unknown')} "
                f"freshness={freshness.get('bucket', 'unknown')} "
                f"domain={evidence.get('domain', '')}"
            )
            if source.snippet:
                print(f"     {source.snippet}")
        print()

    print_sources("Supporting sources", result.supporting_sources[:5])
    print_sources("Conflicting sources", result.conflicting_sources[:5])
    print_sources("Neutral sources", result.neutral_sources[:3])


if __name__ == "__main__":
    main()
