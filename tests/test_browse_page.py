"""Unit tests for free_web_search.browse_page module."""
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from free_web_search.browse_page import browse


class TestBrowsePage(unittest.TestCase):
    """Tests for the browse() function."""

    @patch("free_web_search.browse_page.urllib.request.urlopen")
    def test_browse_returns_success_payload(self, mock_urlopen):
        """browse() should return a success payload for a valid URL."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"""
        <html>
          <head><title>Test Page</title></head>
          <body>
            <p>Hello, this is a test page with some content.</p>
          </body>
        </html>
        """
        mock_response.headers = {}
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = browse("https://example.com")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["title"], "Test Page")
        self.assertIn("Hello, this is a test page", result["content"])
        self.assertIn("insecure_ssl", result)

    @patch("free_web_search.browse_page.urllib.request.urlopen")
    def test_browse_handles_network_error(self, mock_urlopen):
        """browse() should return an error payload on network failures."""
        mock_urlopen.side_effect = Exception("Connection refused")
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

    @patch("free_web_search.browse_page.urllib.request.urlopen")
    def test_browse_truncates_content(self, mock_urlopen):
        """browse() should truncate long content while reporting the full length."""
        mock_response = MagicMock()
        mock_response.read.return_value = (
            "<html><head><title>Fixture</title></head><body>"
            + ("A" * 120)
            + "</body></html>"
        ).encode("utf-8")
        mock_response.headers = {}
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = browse("https://example.com/long", max_chars=40)

        self.assertEqual(result["status"], "success")
        self.assertTrue(result["truncated"])
        self.assertEqual(len(result["content"]), 40)
        self.assertGreater(result["total_length"], len(result["content"]))


if __name__ == "__main__":
    unittest.main()
