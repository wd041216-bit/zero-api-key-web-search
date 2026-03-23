"""Run deterministic benchmark regressions for claim verification."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cross_validated_search.core import Source, UltimateSearcher


BENCHMARK_ROOT = Path(__file__).resolve().parent
CLAIMS_FILE = BENCHMARK_ROOT / "claims.jsonl"
FIXTURES_DIR = BENCHMARK_ROOT / "fixtures"


def _load_claims(path: Path) -> list[dict]:
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def _make_search_result(claim: str, fixture: dict):
    sources = [
        Source(
            url=item["url"],
            title=item["title"],
            snippet=item.get("snippet", ""),
            engine=item.get("engine", ""),
            date=item.get("date", ""),
        )
        for item in fixture.get("sources", [])
    ]
    return SimpleNamespace(
        query=claim,
        search_type="text",
        answer="Top Sources",
        confidence="MEDIUM",
        sources=sources,
        validation={
            "total_results": len(sources),
            "unique_results": len(sources),
            "cross_validated": 0,
        },
        metadata=fixture.get("metadata", {"providers_used": [], "errors": []}),
        elapsed_ms=1,
    )


def run_case(case: dict) -> dict:
    fixture = _load_fixture(case["fixture"])
    page_map = fixture.get("pages", {})

    def browse_func(url: str, max_chars: int = 10000) -> dict:
        if url in page_map:
            return page_map[url]
        return {"status": "error", "url": url, "error": "fixture_missing"}

    searcher = UltimateSearcher(timeout=5, browse_func=browse_func)
    search_result = _make_search_result(case["claim"], fixture)
    searcher.search = lambda *args, **kwargs: search_result  # type: ignore[method-assign]
    result = searcher.verify_claim(
        case["claim"],
        deep=case.get("deep", False),
        include_pages=case.get("deep", False),
        max_pages=2,
    )
    checks = {
        "verdict": result.verdict == case["expected_verdict"],
        "page_aware": result.analysis["page_aware"] == case.get("expected_page_aware", case.get("deep", False)),
    }
    support_score = result.analysis["support_score"]
    conflict_score = result.analysis["conflict_score"]
    if "min_support_score" in case:
        checks["min_support_score"] = support_score >= case["min_support_score"]
    if "max_support_score" in case:
        checks["max_support_score"] = support_score <= case["max_support_score"]
    if "min_conflict_score" in case:
        checks["min_conflict_score"] = conflict_score >= case["min_conflict_score"]
    if "max_conflict_score" in case:
        checks["max_conflict_score"] = conflict_score <= case["max_conflict_score"]
    matched = all(checks.values())

    return {
        "id": case["id"],
        "claim": case["claim"],
        "notes": case.get("notes", ""),
        "expected_verdict": case["expected_verdict"],
        "actual_verdict": result.verdict,
        "expected_page_aware": case.get("expected_page_aware", case.get("deep", False)),
        "matched": matched,
        "checks": checks,
        "support_score": support_score,
        "conflict_score": conflict_score,
        "page_aware": result.analysis["page_aware"],
        "providers_used": result.metadata.get("providers_used", []),
        "provider_diversity": result.analysis["provider_diversity"],
    }


def _group_results(results: list[dict], key: str) -> dict[str, dict[str, int]]:
    grouped: dict[str, dict[str, int]] = {}
    for item in results:
        value = item[key]
        label = str(value).lower() if isinstance(value, bool) else str(value)
        bucket = grouped.setdefault(label, {"total": 0, "passed": 0, "failed": 0})
        bucket["total"] += 1
        if item["matched"]:
            bucket["passed"] += 1
        else:
            bucket["failed"] += 1
    return grouped


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic verification benchmarks.")
    parser.add_argument(
        "--input",
        default=str(CLAIMS_FILE),
        help="Path to the benchmark claims JSONL file.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the full benchmark result as JSON.",
    )
    args = parser.parse_args()

    claims = _load_claims(Path(args.input))
    results = [run_case(case) for case in claims]
    summary = {
        "total": len(results),
        "passed": sum(1 for item in results if item["matched"]),
        "failed": sum(1 for item in results if not item["matched"]),
        "grouped_summary": {
            "expected_verdict": _group_results(results, "expected_verdict"),
            "actual_verdict": _group_results(results, "actual_verdict"),
            "page_aware": _group_results(results, "page_aware"),
            "provider_diversity": _group_results(results, "provider_diversity"),
        },
        "results": results,
    }

    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        for item in results:
            status = "PASS" if item["matched"] else "FAIL"
            print(
                f"{status} {item['id']}: expected={item['expected_verdict']} "
                f"actual={item['actual_verdict']} support={item['support_score']:.2f} "
                f"conflict={item['conflict_score']:.2f} page_aware={item['page_aware']}"
            )
        print(
            f"\nSummary: {summary['passed']}/{summary['total']} passed, "
            f"{summary['failed']} failed."
        )
        print("\nGrouped summary:")
        for group_name, group_values in summary["grouped_summary"].items():
            print(f"- {group_name}:")
            for label, counts in sorted(group_values.items()):
                print(
                    f"  {label}: total={counts['total']} "
                    f"passed={counts['passed']} failed={counts['failed']}"
                )

    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
