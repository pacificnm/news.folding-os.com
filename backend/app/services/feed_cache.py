"""Small TTL cache for the assembled article feed (keyed on category+q+limit)
— avoids re-fetching every registered RSS source on every request. Direct
analog of the original app's `cache.js` (an `lru-cache` wrapper); articles
themselves are never persisted, only cached in-process for a short window.
"""

from cachetools import TTLCache

from app.core.config import settings

_cache: TTLCache = TTLCache(maxsize=200, ttl=settings.feed_cache_ttl_seconds)


def get(key: str):
    return _cache.get(key)


def put(key: str, value) -> None:
    _cache[key] = value
