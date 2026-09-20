"""Tests for concurrent provider calls and retry logic."""

from __future__ import annotations

import asyncio
import unittest

from zero_api_key_web_search.core import UltimateSearcher
from zero_api_key_web_search.providers.base import ProviderResult


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


class TestCircuitBreaker(unittest.TestCase):
    def test_circuit_breaker_trips_after_threshold(self):
        class AlwaysFailProvider:
            name = "failing"

            def search(self, query, search_type, **kwargs):
                raise RuntimeError("Always fails")

        searcher = UltimateSearcher(timeout=5, providers=[AlwaysFailProvider()])
        for _ in range(3):
            searcher.search("test", providers=["failing"])
        self.assertTrue(searcher._provider_is_tripped("failing"))

    def test_circuit_breaker_returns_error_when_tripped(self):
        class AlwaysFailProvider:
            name = "failing"

            def search(self, query, search_type, **kwargs):
                raise RuntimeError("Always fails")

        searcher = UltimateSearcher(timeout=5, providers=[AlwaysFailProvider()])
        for _ in range(3):
            searcher.search("test", providers=["failing"])
        result = searcher.search("test", providers=["failing"])
        self.assertTrue(any("Circuit breaker" in e for e in result.metadata["errors"]))

    def test_circuit_breaker_resets_after_success(self):
        call_count = 0

        class EventualSuccessProvider:
            name = "eventual"

            def search(self, query, search_type, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count <= 4:
                    raise RuntimeError("Fails initially")
                return [ProviderResult(url="https://example.com", title="OK", snippet="works")]

        searcher = UltimateSearcher(timeout=5, providers=[EventualSuccessProvider()])
        searcher.search("test", providers=["eventual"])
        searcher._circuit_breaker.setdefault("eventual", {"consecutive_failures": 2, "last_failure_time": 0})
        searcher._record_provider_success("eventual")
        self.assertFalse(searcher._provider_is_tripped("eventual"))

    def test_circuit_breaker_state_in_metadata(self):
        class AlwaysFailProvider:
            name = "failing"

            def search(self, query, search_type, **kwargs):
                raise RuntimeError("Always fails")

        searcher = UltimateSearcher(timeout=5, providers=[AlwaysFailProvider()])
        for _ in range(3):
            searcher.search("test", providers=["failing"])
        result = searcher.search("test", providers=["failing"])
        self.assertIn("circuit_breaker_state", result.metadata)


class TestAsyncSearch(unittest.TestCase):
    def test_async_search_with_single_provider(self):
        class AsyncProvider:
            name = "ddgs"

            def search(self, query, search_type, **kwargs):
                return [ProviderResult(url="https://example.com", title="Test", snippet="test")]

            async def asearch(self, query, search_type, **kwargs):
                return self.search(query, search_type, **kwargs)

        searcher = UltimateSearcher(timeout=5, providers=[AsyncProvider()])
        result = asyncio.run(searcher.asearch("test", providers=["ddgs"]))
        self.assertEqual(len(result.sources), 1)
        self.assertTrue(result.metadata.get("async"))

    def test_async_search_with_multiple_providers(self):
        class AsyncP1:
            name = "p1"

            def search(self, query, search_type, **kwargs):
                return [ProviderResult(url="https://p1.example.com", title="P1", snippet="p1")]

            async def asearch(self, query, search_type, **kwargs):
                return self.search(query, search_type, **kwargs)

        class AsyncP2:
            name = "p2"

            def search(self, query, search_type, **kwargs):
                return [ProviderResult(url="https://p2.example.com", title="P2", snippet="p2")]

            async def asearch(self, query, search_type, **kwargs):
                return self.search(query, search_type, **kwargs)

        searcher = UltimateSearcher(timeout=5, providers=[AsyncP1(), AsyncP2()])
        result = asyncio.run(searcher.asearch("test", providers=["p1", "p2"]))
        self.assertEqual(len(result.sources), 2)
        self.assertIn("p1", result.metadata["providers_used"])
        self.assertIn("p2", result.metadata["providers_used"])

    def test_async_search_circuit_breaker(self):
        class AsyncFailProvider:
            name = "fail"

            def search(self, query, search_type, **kwargs):
                raise RuntimeError("Always fails")

            async def asearch(self, query, search_type, **kwargs):
                raise RuntimeError("Always fails")

        searcher = UltimateSearcher(timeout=5, providers=[AsyncFailProvider()])
        for _ in range(3):
            asyncio.run(searcher.asearch("test", providers=["fail"]))
        result = asyncio.run(searcher.asearch("test", providers=["fail"]))
        self.assertTrue(any("Circuit breaker" in e for e in result.metadata["errors"]))


if __name__ == "__main__":
    unittest.main()
