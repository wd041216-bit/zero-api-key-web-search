"""LRU response cache with TTL expiry for browse and search results."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from collections import OrderedDict

logger = logging.getLogger("zero-api-key-web-search")

MAX_CACHE_SIZE = 50 * 1024 * 1024  # 50 MB
CACHE_TTL = 900  # 15 minutes in seconds


class ResponseCache:
    """Thread-safe LRU cache with TTL expiry and size-based eviction.

    Keys are strings (URLs for browse, hashes for search).
    Values are (content_bytes, content_type, insert_time) tuples.
    Lazy TTL eviction: expired entries are removed on access, not by a background task.
    """

    def __init__(self, max_bytes: int = MAX_CACHE_SIZE, ttl: int = CACHE_TTL):
        self._store: OrderedDict[str, tuple[bytes, str, float]] = OrderedDict()
        self._max_bytes = max_bytes
        self._ttl = ttl
        self._current_bytes = 0
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def _make_search_key(self, query: str, provider: str, search_type: str,
                         region: str, timelimit: str | None) -> str:
        raw = json.dumps({
            "q": query, "p": provider, "t": search_type,
            "r": region, "tl": timelimit or "",
        }, sort_keys=True)
        return "search:" + hashlib.sha256(raw.encode()).hexdigest()[:16]

    def get(self, key: str) -> tuple[str, str] | None:
        """Return (content_text, content_type) if cache hit, else None."""
        entry = self._store.get(key)
        if entry is None:
            self._misses += 1
            return None

        content_bytes, content_type, insert_time = entry
        if time.time() - insert_time > self._ttl:
            # TTL expired — remove and count as miss
            self._remove_entry(key)
            self._misses += 1
            return None

        # LRU: move to end (most recently used)
        self._store.move_to_end(key)
        self._hits += 1
        return content_bytes.decode("utf-8", errors="replace"), content_type

    def put(self, key: str, content: str, content_type: str = "text/markdown") -> None:
        """Store content in cache, evicting if size limit exceeded."""
        content_bytes = content.encode("utf-8")
        entry_size = len(content_bytes)

        # If single entry exceeds max, skip caching
        if entry_size > self._max_bytes:
            return

        # Remove old entry if overwriting
        if key in self._store:
            self._remove_entry(key)

        # Evict until we have room
        while self._current_bytes + entry_size > self._max_bytes and self._store:
            oldest_key = next(iter(self._store))
            self._remove_entry(oldest_key)
            self._evictions += 1

        self._store[key] = (content_bytes, content_type, time.time())
        self._current_bytes += entry_size

    def clear(self) -> None:
        """Drop all cached entries."""
        self._store.clear()
        self._current_bytes = 0

    def stats(self) -> dict:
        """Return cache hit/miss/eviction/size statistics."""
        return {
            "hits": self._hits,
            "misses": self._misses,
            "evictions": self._evictions,
            "entries": len(self._store),
            "size_bytes": self._current_bytes,
            "max_bytes": self._max_bytes,
            "ttl_seconds": self._ttl,
        }

    def _remove_entry(self, key: str) -> None:
        entry = self._store.pop(key, None)
        if entry is not None:
            self._current_bytes -= len(entry[0])


# Module-level singleton for convenience
_cache: ResponseCache | None = None


def get_cache() -> ResponseCache:
    """Return the module-level cache singleton."""
    global _cache
    if _cache is None:
        _cache = ResponseCache()
    return _cache


def clear_cache() -> None:
    """Clear the module-level cache."""
    get_cache().clear()