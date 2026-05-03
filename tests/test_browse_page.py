"""Unit tests for zero_api_key_web_search.browse_page module."""
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from zero_api_key_web_search.browse_page import browse, extract_text


class TestBrowsePage(unittest.TestCase):
    """Tests for the browse() function."""

    def _make_mock_opener(self, html_bytes, headers=None):
        """Create a mock opener that returns the given HTML."""
        mock_response = MagicMock()
        mock_response.read.return_value = html_bytes
        mock_response.headers = headers or {"Content-Type": "text/html"}
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_opener = MagicMock()
        mock_opener.open.return_value = mock_response
        return mock_opener

    @patch("zero_api_key_web_search.browse_page.urllib.request.build_opener")
    def test_browse_returns_success_payload(self, mock_build_opener):
        """browse() should return a success payload for a valid URL."""
        html = b"""<html><head><title>Test Page</title></head>
        <body><p>Hello, this is a test page with some content.</p></body></html>"""
        mock_build_opener.return_value = self._make_mock_opener(html)

        result = browse("https://example.com")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["title"], "Test Page")
        self.assertIn("Hello, this is a test page", result["content"])
        self.assertIn("insecure_ssl", result)

    @patch("zero_api_key_web_search.browse_page.urllib.request.build_opener")
    def test_browse_handles_network_error(self, mock_build_opener):
        """browse() should return an error payload on network failures."""
        mock_opener = MagicMock()
        mock_opener.open.side_effect = urllib.error.URLError("Connection refused")
        mock_build_opener.return_value = mock_opener
        result = browse("https://nonexistent.example.com")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "error")
        self.assertIn("Connection refused", result["error"])
        self.assertIn("insecure_ssl", result)

    def test_browse_invalid_url(self):
        """browse() should return an error payload for invalid URLs."""
        result = browse("not-a-valid-url")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "error")

    @patch("zero_api_key_web_search.browse_page.urllib.request.build_opener")
    def test_browse_truncates_content(self, mock_build_opener):
        """browse() should truncate long content while reporting the full length."""
        html = (
            b"<html><head><title>Fixture</title></head><body>"
            + b"A" * 120
            + b"</body></html>"
        )
        mock_build_opener.return_value = self._make_mock_opener(html)

        result = browse("https://example.com/long", max_chars=40)

        self.assertEqual(result["status"], "success")
        self.assertTrue(result["truncated"])
        self.assertEqual(len(result["content"]), 40)
        self.assertGreater(result["total_length"], len(result["content"]))


class TestReadabilityHeuristic(unittest.TestCase):
    """Tests for the readability-style main content detection."""

    def test_extracts_article_tag(self):
        """Main content in <article> should be preferred."""
        html = """
        <html><head><title>Test</title></head><body>
          <nav><a href="/">Home</a><a href="/about">About</a></nav>
          <article>
            <p>This is the main article content that should be extracted.</p>
            <p>It has multiple paragraphs of meaningful text.</p>
          </article>
          <footer>Copyright 2026</footer>
        </body></html>
        """
        title, text = extract_text(html)
        self.assertIn("main article content", text)
        self.assertNotIn("Home", text)

    def test_extracts_main_tag(self):
        """Main content in <main> should be extracted."""
        html = """
        <html><head><title>Test</title></head><body>
          <div class="sidebar"><a>Link 1</a><a>Link 2</a></div>
          <main role="main">
            <p>The main content area with substantial text.</p>
          </main>
        </body></html>
        """
        title, text = extract_text(html)
        self.assertIn("main content area", text)

    def test_falls_back_to_full_text(self):
        """When no main content candidate scores well, fall back to full text."""
        html = """
        <html><head><title>Test</title></head><body>
          <p>Some content without semantic structure.</p>
        </body></html>
        """
        title, text = extract_text(html)
        self.assertIn("Some content", text)

    def test_avoids_boilerplate(self):
        """Boilerplate elements should be deprioritized."""
        html = """
        <html><head><title>Test</title></head><body>
          <footer class="contentinfo">
            <a>Link 1</a><a>Link 2</a><a>Link 3</a><a>Link 4</a>
            <p>Footer content</p>
          </footer>
          <div class="article-content">
            <p>This is the real article with enough text to score well.</p>
            <p>More paragraphs add to the text density score significantly.</p>
            <p>A third paragraph further increases the content signal.</p>
          </div>
        </body></html>
        """
        title, text = extract_text(html)
        self.assertIn("real article", text)


if __name__ == "__main__":
    unittest.main()