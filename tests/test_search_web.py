"""Unit tests for zero_api_key_web_search.search_web module."""
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from zero_api_key_web_search.providers.base import ProviderResult
from zero_api_key_web_search.search_web import Answer, Source, UltimateSearcher


class FakeProvider:
    def __init__(self, name, results=None, error=None):
        self.name = name
        self._results = results or []
        self._error = error

    def search(self, query, search_type, timelimit=None, region="wt-wt", max_results=15, **kwargs):
        if self._error is not None:
            raise self._error
        return list(self._results)


class TestSourceDataclass(unittest.TestCase):
    """Tests for the Source dataclass."""

    def test_source_default_extra(self):
        """Source.extra should default to an empty dict, not None."""
        src = Source(url="https://example.com", title="Example")
        self.assertIsNotNone(src.extra)
        self.assertIsInstance(src.extra, dict)

    def test_source_fields(self):
        """Source should store all provided fields correctly."""
        src = Source(
            url="https://example.com",
            title="Example Title",
            snippet="A short snippet",
            rank=1,
            engine="ddgs",
            cross_validated=True,
            date="2025-01-01",
        )
        self.assertEqual(src.url, "https://example.com")
        self.assertEqual(src.title, "Example Title")
        self.assertEqual(src.rank, 1)
        self.assertTrue(src.cross_validated)


class TestUltimateSearcher(unittest.TestCase):
    """Tests for the UltimateSearcher class."""

    def setUp(self):
        self.searcher = UltimateSearcher(timeout=5)

    def test_init_timeout(self):
        """UltimateSearcher should store the timeout value."""
        self.assertEqual(self.searcher.timeout, 5)

    def test_search_returns_answer_object(self):
        """search() should return an Answer dataclass instance."""
        searcher = UltimateSearcher(
            timeout=5,
            providers=[
                FakeProvider(
                    "ddgs",
                    [
                        ProviderResult(
                            url="https://example.com",
                            title="Example",
                            snippet="snippet",
                        )
                    ],
                )
            ],
        )
        result = searcher.search("python testing", search_type="text")
        self.assertIsInstance(result, Answer)
        self.assertEqual(result.query, "python testing")
        self.assertIn("sources", result.__dataclass_fields__)
        self.assertEqual(result.metadata["providers_used"], ["ddgs"])

    def test_search_provider_handles_exception(self):
        """Provider failures should be surfaced as search errors, not crashes."""
        searcher = UltimateSearcher(
            timeout=5,
            providers=[FakeProvider("ddgs", error=RuntimeError("Network error"))],
        )

        result = searcher.search("python testing", search_type="text")

        self.assertEqual(result.sources, [])
        self.assertEqual(result.metadata["providers_used"], [])
        self.assertTrue(any("Network error" in error for error in result.metadata["errors"]))

    def test_search_empty_query(self):
        """search() should handle empty queries gracefully."""
        searcher = UltimateSearcher(timeout=5, providers=[FakeProvider("ddgs", [])])
        result = searcher.search("", search_type="text")
        self.assertIsInstance(result, Answer)

    def test_search_can_aggregate_multiple_providers(self):
        searcher = UltimateSearcher(
            timeout=5,
            providers=[
                FakeProvider(
                    "ddgs",
                    [
                        ProviderResult(
                            url="https://example.com/ddgs",
                            title="DDGS result",
                            snippet="snippet",
                        )
                    ],
                ),
                FakeProvider(
                    "searxng",
                    [
                        ProviderResult(
                            url="https://example.org/searx",
                            title="SearXNG result",
                            snippet="snippet",
                        )
                    ],
                ),
            ],
        )
        result = searcher.search(
            "python release",
            providers=["ddgs", "searxng"],
        )

        self.assertEqual(result.metadata["providers_used"], ["ddgs", "searxng"])
        self.assertEqual(result.validation["providers_requested"], ["ddgs", "searxng"])
        self.assertGreaterEqual(len(result.sources), 2)

    def test_default_providers_detects_searxng_env(self):
        with patch.dict(os.environ, {"ZERO_SEARCH_SEARXNG_URL": "https://searx.example"}, clear=False):
            providers = [provider.name for provider in self.searcher._default_providers()]
        self.assertEqual(providers, ["ddgs", "searxng"])

    def test_default_providers_detects_searxng_alias_env(self):
        with patch.dict(os.environ, {"SEARXNG_URL": "https://searx.example"}, clear=False):
            providers = [provider.name for provider in self.searcher._default_providers()]
        self.assertEqual(providers, ["ddgs", "searxng"])

    def test_search_metadata_includes_free_provider_guidance(self):
        searcher = UltimateSearcher(
            timeout=5,
            providers=[
                FakeProvider(
                    "ddgs",
                    [
                        ProviderResult(
                            url="https://example.com",
                            title="Example",
                            snippet="snippet",
                        )
                    ],
                )
            ],
        )
        result = searcher.search("python release", search_type="text")
        guidance = result.metadata["provider_guidance"]
        self.assertEqual(guidance["free_recommended_pair"], ["ddgs", "searxng"])
        self.assertIn("ZERO_SEARCH_SEARXNG_URL", guidance["free_setup_hint"])
        self.assertFalse(guidance["searxng_configured"])

    def test_search_metadata_marks_free_dual_provider_active(self):
        searcher = UltimateSearcher(
            timeout=5,
            providers=[
                FakeProvider(
                    "ddgs",
                    [
                        ProviderResult(
                            url="https://example.com",
                            title="Example",
                            snippet="snippet",
                        )
                    ],
                )
            ],
        )
        with patch.dict(os.environ, {"ZERO_SEARCH_SEARXNG_URL": "https://searx.example"}, clear=False):
            result = searcher.search("python release", search_type="text")
        guidance = result.metadata["provider_guidance"]
        self.assertTrue(guidance["searxng_configured"])
        self.assertEqual(guidance["recommended_next_step"], "Free dual-provider path is active.")

    def test_search_rejects_unknown_provider(self):
        with self.assertRaises(ValueError):
            self.searcher.search("python", providers=["unknown"])


class TestAnswerSerialization(unittest.TestCase):
    """Tests for Answer JSON serialization."""

    def test_answer_json_serializable(self):
        """Answer object should be serializable to JSON."""
        searcher = UltimateSearcher(
            timeout=5,
            providers=[
                FakeProvider(
                    "ddgs",
                    [
                        ProviderResult(
                            url="https://example.com",
                            title="Test",
                            snippet="test snippet",
                        )
                    ],
                )
            ],
        )
        result = searcher.search("test", search_type="text")
        from dataclasses import asdict

        result_dict = asdict(result)
        json_str = json.dumps(result_dict)
        self.assertIsInstance(json_str, str)
        parsed = json.loads(json_str)
        self.assertIn("query", parsed)
        self.assertIn("sources", parsed)
        self.assertIn("provider_guidance", parsed["metadata"])


if __name__ == "__main__":
    unittest.main()
