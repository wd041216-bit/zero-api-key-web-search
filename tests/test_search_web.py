"""
Unit tests for free_web_search.search_web module.
"""
import json
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, ".")

from free_web_search.search_web import Answer, Source, UltimateSearcher


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

    @patch("free_web_search.search_web.DDGS")
    def test_search_ddgs_text_returns_sources(self, mock_ddgs_class):
        """_search_ddgs should return a list of Source objects for text search."""
        mock_ddgs = MagicMock()
        mock_ddgs_class.return_value.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs_class.return_value.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text.return_value = [
            {
                "href": "https://example.com",
                "title": "Example",
                "body": "A test snippet",
            }
        ]
        results = self.searcher._search_ddgs("test query", "text", max_results=5)
        self.assertIsInstance(results, list)
        if results:
            self.assertIsInstance(results[0], Source)
            self.assertEqual(results[0].url, "https://example.com")

    @patch("free_web_search.search_web.DDGS")
    def test_search_ddgs_handles_exception(self, mock_ddgs_class):
        """_search_ddgs should return an empty list when DDGS raises an exception."""
        mock_ddgs_class.return_value.__enter__ = MagicMock(
            side_effect=Exception("Network error")
        )
        mock_ddgs_class.return_value.__exit__ = MagicMock(return_value=False)
        results = self.searcher._search_ddgs("test query", "text")
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 0)

    def test_search_returns_answer_object(self):
        """search() should return an Answer dataclass instance."""
        with patch.object(
            self.searcher,
            "_search_ddgs",
            return_value=[
                Source(
                    url="https://example.com",
                    title="Example",
                    snippet="snippet",
                    rank=1,
                    engine="ddgs",
                )
            ],
        ):
            result = self.searcher.search("python testing", search_type="text")
            self.assertIsInstance(result, Answer)
            self.assertEqual(result.query, "python testing")
            self.assertIn("sources", result.__dataclass_fields__)

    def test_search_empty_query(self):
        """search() should handle empty queries gracefully."""
        with patch.object(self.searcher, "_search_ddgs", return_value=[]):
            result = self.searcher.search("", search_type="text")
            self.assertIsInstance(result, Answer)


class TestAnswerSerialization(unittest.TestCase):
    """Tests for Answer JSON serialization."""

    def test_answer_json_serializable(self):
        """Answer object should be serializable to JSON."""
        searcher = UltimateSearcher(timeout=5)
        with patch.object(
            searcher,
            "_search_ddgs",
            return_value=[
                Source(
                    url="https://example.com",
                    title="Test",
                    snippet="test snippet",
                    rank=1,
                    engine="ddgs",
                )
            ],
        ):
            result = searcher.search("test", search_type="text")
            from dataclasses import asdict

            result_dict = asdict(result)
            json_str = json.dumps(result_dict)
            self.assertIsInstance(json_str, str)
            parsed = json.loads(json_str)
            self.assertIn("query", parsed)
            self.assertIn("sources", parsed)


if __name__ == "__main__":
    unittest.main()
