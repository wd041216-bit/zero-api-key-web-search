#!/usr/bin/env python3
"""Provider performance benchmark for zero-api-key-web-search.

Compares DDGS-only, Bright Data, and cross-validated search performance.
Outputs a Markdown table with response times, result counts, and quality metrics.

Usage:
    python benchmarks/provider_benchmark.py
    BRIGHTDATA_API_KEY=xxx python benchmarks/provider_benchmark.py
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from zero_api_key_web_search.core import UltimateSearcher
from zero_api_key_web_search.providers import BrightDataProvider


QUERIES = [
    ("text", "Python programming language"),
    ("text", "climate change latest research 2025"),
    ("text", "best restaurants in Tokyo"),
    ("news", "artificial intelligence regulation"),
    ("text", "how to learn machine learning"),
]

PROFILES_TO_TEST = [
    ("DDGS only", {"providers": ["ddgs"]}),
    ("DDGS + Bright Data", {"providers": ["ddgs", "brightdata"]}),
    ("Bright Data only", {"providers": ["brightdata"]}),
]


def run_benchmark():
    """Run benchmark comparing provider configurations."""
    # Check Bright Data availability
    bd_key = os.getenv("ZERO_SEARCH_BRIGHTDATA_API_KEY",
                       os.getenv("BRIGHTDATA_API_KEY",
                                 os.getenv("BRIGHT_DATA_API_KEY", "")))
    bd_zone = os.getenv("ZERO_SEARCH_BRIGHTDATA_ZONE",
                        os.getenv("BRIGHTDATA_SERP_ZONE",
                                  os.getenv("BRIGHT_DATA_SERP_ZONE", "web_search")))

    bd_available = bool(bd_key)
    if not bd_available:
        print("⚠️  No Bright Data API key found. Bright Data tests will be skipped.")
        print("   Set ZERO_SEARCH_BRIGHTDATA_API_KEY to enable Bright Data tests.")
        print()

    # Filter profiles based on availability
    profiles = []
    for name, config in PROFILES_TO_TEST:
        if "brightdata" in config.get("providers", []) and not bd_available:
            print(f"   Skipping '{name}' — no Bright Data API key")
            continue
        profiles.append((name, config))

    if not profiles:
        print("No profiles to test. Exiting.")
        return

    print(f"\n{'='*70}")
    print("Provider Performance Benchmark")
    print(f"{'='*70}")
    print(f"Queries: {len(QUERIES)} | Profiles: {len(profiles)} | BD Zone: {bd_zone}")
    print()

    # Run benchmarks
    results = {}

    for profile_name, config in profiles:
        profile_results = []
        print(f"\n📊 Testing: {profile_name}")
        print("-" * 50)

        for search_type, query in QUERIES:
            searcher = UltimateSearcher()

            # Ensure Bright Data provider is initialized if needed
            if "brightdata" in config.get("providers", []) and bd_available:
                # The provider auto-initializes from env vars
                pass

            start = time.time()
            try:
                answer = searcher.search(
                    query=query,
                    search_type=search_type,
                    providers=config.get("providers"),
                )
                elapsed = time.time() - start

                cross_validated = sum(1 for s in answer.sources if s.cross_validated)
                result = {
                    "query": query[:40],
                    "type": search_type,
                    "elapsed_ms": answer.elapsed_ms,
                    "wall_ms": int(elapsed * 1000),
                    "results": len(answer.sources),
                    "unique": answer.validation.get("unique_results", 0),
                    "cross_validated": cross_validated,
                    "confidence": answer.confidence,
                    "providers_used": ", ".join(answer.metadata.get("providers_used", [])),
                    "error": None,
                }
            except Exception as e:
                elapsed = time.time() - start
                result = {
                    "query": query[:40],
                    "type": search_type,
                    "elapsed_ms": 0,
                    "wall_ms": int(elapsed * 1000),
                    "results": 0,
                    "unique": 0,
                    "cross_validated": 0,
                    "confidence": "error",
                    "providers_used": "",
                    "error": str(e)[:80],
                }

            profile_results.append(result)
            status = "✅" if not result["error"] else "❌"
            print(f"  {status} {search_type:5s} | {result['query']:40s} | "
                  f"{result['wall_ms']:5d}ms | {result['results']:2d} results | "
                  f"CV: {result['cross_validated']}")

        results[profile_name] = profile_results

    # Summary table
    print(f"\n{'='*70}")
    print("Summary")
    print(f"{'='*70}")
    print(f"{'Profile':<25} {'Avg ms':>8} {'Results':>8} {'CV Avg':>8} {'Errors':>8}")
    print("-" * 70)

    for profile_name, profile_results in results.items():
        successful = [r for r in profile_results if not r["error"]]
        avg_ms = sum(r["wall_ms"] for r in successful) / max(len(successful), 1)
        avg_results = sum(r["results"] for r in successful) / max(len(successful), 1)
        avg_cv = sum(r["cross_validated"] for r in successful) / max(len(successful), 1)
        errors = len([r for r in profile_results if r["error"]])

        print(f"{profile_name:<25} {avg_ms:>7.0f}ms {avg_results:>7.1f} {avg_cv:>7.1f} {errors:>7d}")

    # Bright Data specific info
    if bd_available:
        print(f"\n🔍 Bright Data Details:")
        print(f"   Zone: {bd_zone}")
        print(f"   API Key: {bd_key[:8]}...")
        print(f"   Free credits signup: https://get.brightdata.com/h21j9xz4uxgd")

    print()


if __name__ == "__main__":
    run_benchmark()