"""Tests for concurrent provider calls and retry logic."""

from __future__ import annotations

import unittest
from unittest.mock import patch, MagicMock
from concurrent.futures import ThreadPoolExecutor

from cross_validated_search.core import UltimateSearcher, Source
from cross_validated_search.providers.base import ProviderResult


class FakeProvider:
    """Fake search provider for testing."""

    def __init__(self, name, results=None, error=None, call_times=None):
        self.name = name
        self._results = results or []
        self._error = error
        self._call_times = call_times

    def search(self, query, search_type, timelimit=None, region="wt-wt", max_results=15, **kwargs):
        if self._call_times is not None:
            self._call_times.append(query)
        if self._error is not None:
            raise self._error
        return list(self._results)


class TestConcurrentProviderCalls(unittest.TestCase):
    def test_multiple_providers_called_concurrently(self):
        call_order = []

        class SlowProvider:
            name = "slow"

            def search(self, query, search_type, timelimit=None, region="wt-wt", max_results=15, **kwargs):
                call_order.append("slow_start")
                import time
                time.sleep(0.05)
                call_order.append("slow_end")
                return [ProviderResult(url="https://slow.example.com", title="Slow Result", snippet="slow")]

        class FastProvider:
            name = "fast"

            def search(self, query, search_type, timelimit=None, region="wt-wt", max_results=15, **kwargs):
                call_order.append("fast_start")
                call_order.append("fast_end")
                return [ProviderResult(url="https://fast.example.com", title="Fast Result", snippet="fast")]

        searcher = UltimateSearcher(timeout=5, providers=[SlowProvider(), FastProvider()])
        result = searcher.search("test query", providers=["slow", "fast"])

        self.assertEqual(len(result.sources), 2)
        self.assertIn("slow", result.metadata["providers_used"])
        self.assertIn("fast", result.metadata["providers_used"])

    def test_single_provider_no_threadpool(self):
        provider = FakeProvider(
            "ddgs",
            [ProviderResult(url="https://example.com", title="Test", snippet="test")],
        )
        searcher = UltimateSearcher(timeout=5, providers=[provider])
        result = searcher.search("test", providers=["ddgs"])
        self.assertEqual(len(result.sources), 1)
        self.assertEqual(result.metadata["providers_used"], ["ddgs"])

    def test_concurrent_provider_error_does_not_block_others(self):
        class ErrorProvider:
            name = "error_provider"

            def search(self, query, search_type, **kwargs):
                raise RuntimeError("Provider failed")

        class GoodProvider:
            name = "good_provider"

            def search(self, query, search_type, **kwargs):
                return [ProviderResult(url="https://good.example.com", title="Good", snippet="good")]

        searcher = UltimateSearcher(timeout=5, providers=[ErrorProvider(), GoodProvider()])
        result = searcher.search("test", providers=["error_provider", "good_provider"])

        self.assertIn("good_provider", result.metadata["providers_used"])
        self.assertTrue(any("error" in e.lower() or "Error" in e for e in result.metadata["errors"]))


class TestRetryLogic(unittest.TestCase):
    def test_retry_on_transient_error_succeeds(self):
        call_count = 0

        class TransientErrorProvider:
            name = "transient"

            def search(self, query, search_type, timelimit=None, region="wt-wt", max_results=15, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count <= 2:
                    raise ConnectionError("Temporary network error")
                return [ProviderResult(url="https://example.com", title="Result", snippet="retry ok")]

        searcher = UltimateSearcher(timeout=5, providers=[TransientErrorProvider()])
        result = searcher.search("test", providers=["transient"])
        self.assertEqual(len(result.sources), 1)
        self.assertEqual(result.metadata["providers_used"], ["transient"])
        self.assertGreaterEqual(call_count, 3)

    def test_retry_exhausted_returns_error(self):
        class PermanentErrorProvider:
            name = "permanent"

            def search(self, query, search_type, **kwargs):
                raise RuntimeError("Permanent failure")

        searcher = UltimateSearcher(timeout=5, providers=[PermanentErrorProvider()])
        result = searcher.search("test", providers=["permanent"])

        self.assertEqual(result.sources, [])
        self.assertTrue(any("3 retries" in e for e in result.metadata["errors"]))

    def test_retry_success_on_second_attempt(self):
        call_count = 0

        class OneRetryProvider:
            name = "one_retry"

            def search(self, query, search_type, timelimit=None, region="wt-wt", max_results=15, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise ConnectionError("First attempt fails")
                return [ProviderResult(url="https://example.com", title="OK", snippet="second try works")]

        searcher = UltimateSearcher(timeout=5, providers=[OneRetryProvider()])
        result = searcher.search("test", providers=["one_retry"])

        self.assertEqual(len(result.sources), 1)
        self.assertEqual(result.metadata["providers_used"], ["one_retry"])
        self.assertEqual(call_count, 2)


if __name__ == "__main__":
    unittest.main()