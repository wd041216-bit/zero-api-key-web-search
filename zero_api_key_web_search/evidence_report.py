#!/usr/bin/env python3
"""CLI entry point for the evidence-report command."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from zero_api_key_web_search.core import EvidenceReportResult, UltimateSearcher


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a concise evidence report for a query or claim.",
        epilog=(
            "Examples:\n"
            "  evidence-report \"Python 3.13 stable release\"\n"
            "  evidence-report \"OpenAI API pricing\" --timelimit w --json\n"
            "  evidence-report \"Python 3.13 stable release\""
            " --claim \"Python 3.13 is the latest stable release\" --deep --max-pages 2"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("query", help="Search query used to gather evidence")
    parser.add_argument(
        "--claim",
        help="Optional explicit claim to verify. Defaults to the query text.",
    )
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
        "--json",
        action="store_true",
        help="Output the report as JSON",
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
    parser.add_argument(
        "--max-sources",
        type=int,
        default=5,
        help="Maximum number of sources to include in the report digest (default: 5).",
    )

    args = parser.parse_args()
    searcher = UltimateSearcher()
    result: EvidenceReportResult = searcher.evidence_report(
        query=args.query,
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
        max_sources=args.max_sources,
    )

    if args.json:
        print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
        return

    print("\n" + "=" * 60)
    print(f"Evidence Report Query: {result.query}")
    print(f"Claim: {result.claim}")
    print(f"Verdict: {result.verdict}")
    print(f"Confidence: {result.confidence}")
    print(result.executive_summary)
    print(result.verification_summary)
    print(
        "Report Model: "
        f"{result.analysis['report_model']} | "
        f"search_confidence={result.analysis['search_confidence']} | "
        f"support={result.analysis['support_score']:.2f} | "
        f"conflict={result.analysis['conflict_score']:.2f} | "
        f"providers={result.analysis['provider_diversity']} | "
        f"pages={result.analysis['page_fetches_succeeded']}/{result.analysis['page_fetches_attempted']}"
    )
    print("=" * 60 + "\n")

    if result.verdict_rationale:
        print("Why this verdict:")
        for item in result.verdict_rationale:
            print(f"  - {item}")
        print()

    if result.coverage_warnings:
        print("Coverage warnings:")
        for warning in result.coverage_warnings:
            print(f"  - {warning}")
        print()

    if result.stance_summary:
        print("Stance summary:")
        for label, bucket in result.stance_summary.items():
            print(
                f"  - {label}: count={bucket['count']} score={bucket['score']} "
                f"domains={', '.join(bucket['top_domains']) or 'none'}"
            )
        print()

    if result.source_digest:
        print("Source digest:")
        for index, item in enumerate(result.source_digest, 1):
            print(
                f"  {index}. {item['title']}\n"
                f"     URL: {item['url']}\n"
                f"     class={item['classification']} strength={item['evidence_strength']} "
                f"quality={item['source_quality_tier']} freshness={item['freshness_bucket']} "
                f"page={item['page_evidence_status']}"
            )
            if item["snippet"]:
                print(f"     {item['snippet']}")
        print()

    if result.citations:
        print("Recommended citations:")
        for citation in result.citations:
            print(f"  - {citation}")
        print()

    if result.next_steps:
        print("Next steps:")
        for step in result.next_steps:
            print(f"  - {step}")


if __name__ == "__main__":
    main()
