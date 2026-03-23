"""Tests for transport security helpers."""

from __future__ import annotations

import os
import ssl
import unittest
from unittest.mock import patch

from cross_validated_search.transport import build_ssl_context, insecure_ssl_enabled


class TestTransport(unittest.TestCase):
    def test_insecure_ssl_disabled_by_default(self):
        with patch.dict(os.environ, {}, clear=False):
            self.assertFalse(insecure_ssl_enabled())

    def test_insecure_ssl_enabled_via_env(self):
        with patch.dict(os.environ, {"CROSS_VALIDATED_SEARCH_INSECURE_SSL": "1"}, clear=False):
            self.assertTrue(insecure_ssl_enabled())
            context = build_ssl_context()
            self.assertEqual(context.verify_mode, ssl.CERT_NONE)
