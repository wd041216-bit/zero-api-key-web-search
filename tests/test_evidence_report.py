"""Unit tests for the evidence-report workflow."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from cross_validated_search.core import Answer, UltimateSearcher, Source


class TestEvidenceReport(unittest.TestCase):
    def test_evidence_report_returns_citation_ready_summary(self):
        answer = Answer(
            query="Python 3.13 stable release",
            search_type="text",
            answer="Top Sources:\n1. [Official Python 3.13 release](https://docs.python.org/3/whatsnew/3.13.html)",
            confidence="MEDIUM",
            sources=[
                Source(
                    url="https://docs.python.org/3/whatsnew/3.13.html",
                    title="Official Python 3.13 release",
                    snippet="Official release notes confirm Python 3.13 is the stable release line.",
                    engine="DDGS-Text",
                    date="2026-03-20",
                )
            ],
            validation={"total_results": 1, "unique_results": 1, "cross_validated": 0},
            metadata={"providers_used": ["ddgs"], "providers_requested": ["ddgs"], "errors": []},
            elapsed_ms=5,
        )
        searcher = UltimateSearcher(timeout=5)

        with patch.object(searcher, "search", return_value=answer) as mock_search:
            report = searcher.evidence_report(
                query="Python 3.13 stable release",
                claim="Python 3.13 is the latest stable release",
                providers=["ddgs"],
            )

        mock_search.assert_called_once()
        self.assertEqual(report.query, "Python 3.13 stable release")
        self.assertEqual(report.claim, "Python 3.13 is the latest stable release")
        self.assertEqual(report.analysis["report_model"], "evidence-report-v2")
        self.assertEqual(report.analysis["query_source_count"], 1)
        self.assertGreaterEqual(len(report.source_digest), 1)
        self.assertTrue(report.citations)
        self.assertTrue(report.verdict_rationale)
        self.assertIn("supporting", report.stance_summary)
        self.assertTrue(report.coverage_warnings)
        self.assertIn("free_provider_path", report.analysis)
        self.assertIn("provider", report.executive_summary)
        self.assertTrue(any("searxng" in step.lower() for step in report.next_steps))
