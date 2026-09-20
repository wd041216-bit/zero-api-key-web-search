"""Tests for calibration note and sub-claims in verification results."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from zero_api_key_web_search.core import (
    CALIBRATION_NOTE,
    Source,
    UltimateSearcher,
)


class TestCalibrationNote(unittest.TestCase):
    def test_calibration_note_constant_exists(self):
        self.assertTrue(len(CALIBRATION_NOTE) > 0)
        self.assertIn("heuristic", CALIBRATION_NOTE.lower())
        self.assertIn("calibrated", CALIBRATION_NOTE.lower())

    def test_verify_result_includes_calibration_note(self):
        searcher = UltimateSearcher(timeout=5)
        fake_sources = [
            Source(
                url="https://example.com/a",
                title="Claim supported",
                snippet="Python 3.13 is the latest stable release according to release notes.",
                engine="DDG-Text",
                date="2026-03-20",
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
                    "validation": {"total_results": 1, "unique_results": 1, "cross_validated": 0},
                    "metadata": {"providers_used": ["ddgs"], "errors": []},
                    "elapsed_ms": 10,
                },
            )()
            result = searcher.verify_claim("Python 3.13 is the latest stable release")

        self.assertEqual(result.calibration_note, CALIBRATION_NOTE)
        self.assertIn("heuristic", result.calibration_note.lower())

    def test_evidence_report_includes_calibration_note(self):
        from zero_api_key_web_search.core import Answer

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
        with patch.object(searcher, "search", return_value=answer):
            report = searcher.evidence_report(
                query="Python 3.13 stable release",
                claim="Python 3.13 is the latest stable release",
                providers=["ddgs"],
            )

        self.assertEqual(report.calibration_note, CALIBRATION_NOTE)
        self.assertIn("heuristic", report.calibration_note.lower())

    def test_sub_claims_default_empty_for_simple_claim(self):
        searcher = UltimateSearcher(timeout=5)
        fake_sources = [
            Source(
                url="https://example.com/a",
                title="Claim supported",
                snippet="Python 3.13 is the latest stable release according to release notes.",
                engine="DDG-Text",
                date="2026-03-20",
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
                    "validation": {"total_results": 1, "unique_results": 1, "cross_validated": 0},
                    "metadata": {"providers_used": ["ddgs"], "errors": []},
                    "elapsed_ms": 10,
                },
            )()
            result = searcher.verify_claim("Python 3.13 is the latest stable release")

        self.assertIsInstance(result.sub_claims, list)


if __name__ == "__main__":
    unittest.main()
