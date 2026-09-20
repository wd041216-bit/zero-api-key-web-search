"""Tests for the evidence-oriented claim verification flow."""

from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from zero_api_key_web_search.core import Source, UltimateSearcher


class TestVerifyClaim(unittest.TestCase):
    def test_verify_claim_detects_contestation(self):
        searcher = UltimateSearcher(timeout=5)
        fake_sources = [
            Source(
                url="https://example.com/a",
                title="Claim supported",
                snippet="Python 3.13 is the latest stable release according to release notes.",
                engine="DDG-Text",
                date="2026-03-20",
            ),
            Source(
                url="https://example.org/b",
                title="Claim repeated",
                snippet="Multiple outlets report Python 3.13 is the latest stable release.",
                engine="DDG-Text",
                date="2026-03-19",
            ),
            Source(
                url="https://example.net/c",
                title="Fact check says false",
                snippet="A fact check claims Python 3.13 is not the latest stable release and says the statement is false.",
                engine="DDG-Text",
                date="2026-03-18",
            ),
        ]

        with patch.object(searcher, "search") as mock_search:
            mock_search.return_value = type(
                "SearchResult",
                (),
                {
                    "query": "Python 3.13 is the latest stable release",
                    "search_type": "text",
                    "answer": "Top Sources",
                    "confidence": "MEDIUM",
                    "sources": fake_sources,
                    "validation": {"total_results": 3, "unique_results": 3, "cross_validated": 0},
                    "metadata": {"providers_used": ["ddgs"], "errors": []},
                    "elapsed_ms": 10,
                },
            )()

            result = searcher.verify_claim("Python 3.13 is the latest stable release")

        self.assertEqual(result.verdict, "contested")
        self.assertGreaterEqual(len(result.supporting_sources), 1)
        self.assertGreaterEqual(len(result.conflicting_sources), 1)
        self.assertIn("supporting_count", result.analysis)
        self.assertIn("provider_diversity", result.analysis)
        self.assertIn("page_fetches_attempted", result.analysis)
        self.assertIn("support_score", result.analysis)
        self.assertIn("verification_model", result.analysis)
        self.assertIn("score_breakdown", result.analysis["verification_model"])
        self.assertIn("supporting_domains", result.analysis["contested_summary"])
        self.assertEqual(result.analysis["verification_model"]["name"], "evidence-aware-heuristic-v3")
        self.assertTrue(
            result.supporting_sources[0].extra["verification"]["source_quality"]["tier"]
            in {"high", "medium", "low"}
        )
        self.assertIn("Supporting evidence is led by domains", result.summary)

    def test_verify_claim_json_serializable(self):
        searcher = UltimateSearcher(timeout=5)
        with patch.object(searcher, "search") as mock_search:
            mock_search.return_value = type(
                "SearchResult",
                (),
                {
                    "query": "Claim",
                    "search_type": "text",
                    "answer": "Top Sources",
                    "confidence": "LOW",
                    "sources": [],
                    "validation": {"total_results": 0, "unique_results": 0, "cross_validated": 0},
                    "metadata": {"providers_used": ["ddgs"], "errors": []},
                    "elapsed_ms": 1,
                },
            )()

            result = searcher.verify_claim("Claim")

        payload = json.dumps(result, default=lambda obj: obj.__dict__)
        self.assertIsInstance(payload, str)

    def test_note_does_not_trigger_false_conflict_match(self):
        searcher = UltimateSearcher(timeout=5)
        source = Source(
            url="https://docs.python.org/release",
            title="Official release notes",
            snippet="Release notes confirm Python 3.13 is stable. This note summarizes the update.",
            engine="DDG-Text",
            date="2026-03-18",
        )

        classification, evidence = searcher._classify_source_against_claim(
            ["python", "stable", "release"],
            source,
        )

        self.assertEqual(classification, "supporting")
        self.assertFalse(evidence["conflict_markers_detected"])
        self.assertEqual(evidence["source_quality"]["tier"], "high")

    def test_verify_claim_can_detect_likely_false(self):
        searcher = UltimateSearcher(timeout=5)
        fake_sources = [
            Source(
                url="https://example.net/fact-check",
                title="Fact check says false",
                snippet="Fact check says the claim is false, disputed, and not supported by current release notes.",
                engine="DDG-Text",
                date="2026-03-20",
            ),
            Source(
                url="https://example.org/correction",
                title="Correction published",
                snippet="A correction explains the statement is incorrect and contradicts official updates.",
                engine="DDG-Text",
                date="2026-03-19",
            ),
        ]

        with patch.object(searcher, "search") as mock_search:
            mock_search.return_value = type(
                "SearchResult",
                (),
                {
                    "query": "Claim",
                    "search_type": "text",
                    "answer": "Top Sources",
                    "confidence": "LOW",
                    "sources": fake_sources,
                    "validation": {"total_results": 2, "unique_results": 2, "cross_validated": 0},
                    "metadata": {"providers_used": ["ddgs"], "errors": []},
                    "elapsed_ms": 1,
                },
            )()

            result = searcher.verify_claim("Claim")

        self.assertEqual(result.verdict, "likely_false")
        self.assertGreater(result.analysis["conflict_score"], result.analysis["support_score"])

    def test_verify_claim_with_pages_refines_evidence(self):
        searcher = UltimateSearcher(
            timeout=5,
            browse_func=lambda url, max_chars=10000: {
                "status": "success",
                "url": url,
                "title": "Official page",
                "content": "Python 3.13 is the latest stable release according to official release notes.",
                "truncated": False,
                "total_length": 79,
            },
        )
        fake_sources = [
            Source(
                url="https://example.com/a",
                title="Ambiguous snippet",
                snippet="This short snippet is too vague on its own.",
                engine="DDG-Text",
                date="2026-03-20",
            )
        ]

        with patch.object(searcher, "search") as mock_search:
            mock_search.return_value = type(
                "SearchResult",
                (),
                {
                    "query": "Python 3.13 is the latest stable release",
                    "search_type": "text",
                    "answer": "Top Sources",
                    "confidence": "LOW",
                    "sources": fake_sources,
                    "validation": {"total_results": 1, "unique_results": 1, "cross_validated": 0},
                    "metadata": {"providers_used": ["ddgs"], "errors": []},
                    "elapsed_ms": 10,
                },
            )()

            result = searcher.verify_claim(
                "Python 3.13 is the latest stable release",
                include_pages=True,
                max_pages=1,
            )

        self.assertTrue(result.analysis["page_aware"])
        self.assertEqual(result.analysis["page_fetches_attempted"], 1)
        self.assertEqual(result.analysis["page_fetches_succeeded"], 1)
        self.assertTrue(
            fake_sources[0].extra["verification"]["page_aware"]
        )
        self.assertEqual(
            fake_sources[0].extra["verification"]["page_evidence"]["classification"],
            "supporting",
        )

    def test_verify_claim_deep_alias_enables_page_aware_mode(self):
        searcher = UltimateSearcher(
            timeout=5,
            browse_func=lambda url, max_chars=10000: {
                "status": "success",
                "url": url,
                "title": "Official page",
                "content": "Python 3.13 is the latest stable release according to official release notes.",
                "truncated": False,
                "total_length": 79,
            },
        )

        fake_sources = [
            Source(
                url="https://example.com/a",
                title="Ambiguous snippet",
                snippet="This short snippet is too vague on its own.",
                engine="DDG-Text",
                date="2026-03-20",
            )
        ]

        with patch.object(searcher, "search") as mock_search:
            mock_search.return_value = type(
                "SearchResult",
                (),
                {
                    "query": "Python 3.13 is the latest stable release",
                    "search_type": "text",
                    "answer": "Top Sources",
                    "confidence": "LOW",
                    "sources": fake_sources,
                    "validation": {"total_results": 1, "unique_results": 1, "cross_validated": 0},
                    "metadata": {"providers_used": ["ddgs"], "errors": []},
                    "elapsed_ms": 10,
                },
            )()

            result = searcher.verify_claim(
                "Python 3.13 is the latest stable release",
                deep=True,
                max_pages=1,
            )

        self.assertTrue(result.analysis["page_aware"])
