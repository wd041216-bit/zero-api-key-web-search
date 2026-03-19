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


class TestSearchTavily(unittest.TestCase):
    """Tests for the _search_tavily method."""

    def setUp(self):
        self.searcher = UltimateSearcher(timeout=5)
        # Inject a mock 'tavily' module so the lazy import inside _search_tavily works
        self.mock_tavily_module = MagicMock()
        self._tavily_patcher = patch.dict("sys.modules", {"tavily": self.mock_tavily_module})
        self._tavily_patcher.start()

    def tearDown(self):
        self._tavily_patcher.stop()

    @patch.dict("os.environ", {"TAVILY_API_KEY": "tvly-test-key"})
    def test_tavily_text_returns_sources(self):
        """_search_tavily should map Tavily results to Source objects."""
        mock_client = MagicMock()
        self.mock_tavily_module.TavilyClient.return_value = mock_client
        mock_client.search.return_value = {
            "results": [
                {
                    "url": "https://example.com/article",
                    "title": "Example Article",
                    "content": "Article content snippet",
                    "score": 0.95,
                    "published_date": "2025-06-01",
                }
            ]
        }
        results = self.searcher._search_tavily("test query", "text", max_results=5)
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], Source)
        self.assertEqual(results[0].url, "https://example.com/article")
        self.assertEqual(results[0].title, "Example Article")
        self.assertEqual(results[0].snippet, "Article content snippet")
        self.assertEqual(results[0].engine, "Tavily-Text")
        self.assertEqual(results[0].date, "2025-06-01")
        self.assertEqual(results[0].extra, {"score": 0.95})

    @patch.dict("os.environ", {"TAVILY_API_KEY": "tvly-test-key"})
    def test_tavily_error_returns_error_source(self):
        """_search_tavily should return an error Source on exception."""
        self.mock_tavily_module.TavilyClient.return_value.search.side_effect = Exception("API error")
        results = self.searcher._search_tavily("test query", "text")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].url, "error")
        self.assertIn("API error", results[0].title)

    def test_tavily_unsupported_type_returns_empty(self):
        """_search_tavily should return [] for unsupported search types."""
        for stype in ("images", "videos", "books"):
            results = self.searcher._search_tavily("test", stype)
            self.assertEqual(results, [])

    @patch.dict("os.environ", {"TAVILY_API_KEY": "tvly-test-key"})
    def test_tavily_time_range_mapping(self):
        """_search_tavily should pass correct time_range for timelimit."""
        mock_client = MagicMock()
        self.mock_tavily_module.TavilyClient.return_value = mock_client
        mock_client.search.return_value = {"results": []}

        self.searcher._search_tavily("test", "text", timelimit="w")
        call_kwargs = mock_client.search.call_args[1]
        self.assertEqual(call_kwargs["time_range"], "week")

    @patch.dict("os.environ", {"TAVILY_API_KEY": "tvly-test-key"})
    def test_tavily_news_sets_topic(self):
        """_search_tavily should set topic='news' for news search type."""
        mock_client = MagicMock()
        self.mock_tavily_module.TavilyClient.return_value = mock_client
        mock_client.search.return_value = {"results": []}

        self.searcher._search_tavily("test", "news")
        call_kwargs = mock_client.search.call_args[1]
        self.assertEqual(call_kwargs["topic"], "news")


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
