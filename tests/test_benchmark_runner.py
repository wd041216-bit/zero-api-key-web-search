"""Regression runner smoke tests."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

BENCHMARK_RUNNER = Path(__file__).resolve().parents[1] / "benchmarks" / "run_benchmark.py"


class TestBenchmarkRunner(unittest.TestCase):
    def test_benchmark_runner_json_output(self):
        result = subprocess.run(
            [sys.executable, str(BENCHMARK_RUNNER), "--json"],
            capture_output=True,
            text=True,
            check=True,
        )

        payload = json.loads(result.stdout)
        self.assertEqual(payload["total"], 12)
        self.assertEqual(payload["failed"], 0)
        self.assertEqual(len(payload["results"]), 12)
        self.assertTrue(all("checks" in item for item in payload["results"]))
        self.assertIn("grouped_summary", payload)
        self.assertEqual(payload["grouped_summary"]["expected_verdict"]["supported"]["total"], 3)
        self.assertEqual(payload["grouped_summary"]["expected_verdict"]["likely_supported"]["total"], 2)
        self.assertEqual(payload["grouped_summary"]["expected_verdict"]["contested"]["total"], 2)
        self.assertEqual(payload["grouped_summary"]["expected_verdict"]["likely_false"]["total"], 3)
        self.assertEqual(payload["grouped_summary"]["expected_verdict"]["insufficient_evidence"]["total"], 2)
        self.assertEqual(payload["grouped_summary"]["page_aware"]["true"]["total"], 3)
        self.assertEqual(payload["grouped_summary"]["page_aware"]["false"]["total"], 9)
        self.assertEqual(payload["grouped_summary"]["provider_diversity"]["1"]["total"], 6)
        self.assertEqual(payload["grouped_summary"]["provider_diversity"]["2"]["total"], 6)
