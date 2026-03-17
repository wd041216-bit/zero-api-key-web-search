"""
Unit tests for free_web_search.browse_page module.
"""
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, ".")

from free_web_search.browse_page import browse


class TestBrowsePage(unittest.TestCase):
    """Tests for the browse() function."""

    @patch("free_web_search.browse_page.urllib.request.urlopen")
    def test_browse_returns_text(self, mock_urlopen):
        """browse() should return a non-empty string for a valid URL."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"""
        <html>
          <head><title>Test Page</title></head>
          <body>
            <p>Hello, this is a test page with some content.</p>
          </body>
        </html>
        """
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = browse("https://example.com")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    @patch("free_web_search.browse_page.urllib.request.urlopen")
    def test_browse_handles_network_error(self, mock_urlopen):
        """browse() should handle network errors gracefully."""
        mock_urlopen.side_effect = Exception("Connection refused")
        result = browse("https://nonexistent.example.com")
        # Should return an error string or empty string, not raise
        self.assertIsInstance(result, str)

    def test_browse_invalid_url(self):
        """browse() should handle invalid URLs without crashing."""
        result = browse("not-a-valid-url")
        self.assertIsInstance(result, str)


if __name__ == "__main__":
    unittest.main()
