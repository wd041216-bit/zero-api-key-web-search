"""Sanity checks for benchmark dataset fixtures."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

BENCHMARK_FILE = Path(__file__).resolve().parents[1] / "benchmarks" / "claims.jsonl"
FIXTURE_DIR = BENCHMARK_FILE.parent / "fixtures"
VALID_VERDICTS = {
    "supported",
    "likely_supported",
    "contested",
    "likely_false",
    "insufficient_evidence",
}


class TestBenchmarkDataset(unittest.TestCase):
    def test_claims_jsonl_has_required_fields(self):
        self.assertTrue(BENCHMARK_FILE.exists())

        seen_ids = set()
        lines = BENCHMARK_FILE.read_text(encoding="utf-8").strip().splitlines()
        self.assertGreaterEqual(len(lines), 1)

        for line in lines:
            payload = json.loads(line)
            self.assertIn("id", payload)
            self.assertIn("claim", payload)
            self.assertIn("expected_verdict", payload)
            self.assertIn("fixture", payload)
            self.assertIn("deep", payload)
            self.assertIn("expected_page_aware", payload)
            self.assertIn("notes", payload)
            self.assertNotIn(payload["id"], seen_ids)
            self.assertIn(payload["expected_verdict"], VALID_VERDICTS)
            self.assertIsInstance(payload["deep"], bool)
            self.assertIsInstance(payload["expected_page_aware"], bool)
            self.assertTrue((FIXTURE_DIR / payload["fixture"]).exists())
            seen_ids.add(payload["id"])
