"""Sanity checks for self-hosted SearXNG assets."""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestSelfHostedAssets(unittest.TestCase):
    def test_env_example_exists(self):
        env_example = ROOT / ".env.searxng.example"
        self.assertTrue(env_example.exists())
        content = env_example.read_text(encoding="utf-8")
        self.assertIn("SEARXNG_IMAGE=", content)
        self.assertIn("CROSS_VALIDATED_SEARCH_SEARXNG_URL=", content)

    def test_compose_includes_healthcheck(self):
        compose_file = ROOT / "docker-compose.searxng.yml"
        content = compose_file.read_text(encoding="utf-8")
        self.assertIn("healthcheck:", content)
        self.assertIn("SEARXNG_IMAGE", content)
        self.assertIn("SEARXNG_PORT", content)

    def test_scripts_reference_ready_and_validation_flow(self):
        start_script = (ROOT / "scripts" / "start-searxng.sh").read_text(encoding="utf-8")
        validate_script = (ROOT / "scripts" / "validate-free-path.sh").read_text(encoding="utf-8")
        self.assertIn("Waiting for SearXNG readiness", start_script)
        self.assertIn("PASS summary: free dual-provider path is healthy.", validate_script)
