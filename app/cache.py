"""
Lightweight Redis JSON cache. Optional — if REDIS_URL is unset, all calls
no-op so the app keeps working without Redis configured.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Callable, Optional

try:
    import redis  # type: ignore
    _redis_available = True
except ImportError:
    _redis_available = False

from app.config import get_settings

log = logging.getLogger(__name__)

_client: Optional["redis.Redis"] = None
_initialized = False


def _get_client() -> Optional["redis.Redis"]:
    global _client, _initialized
    if _initialized:
        return _client
    _initialized = True

    if not _redis_available:
        return None

    settings = get_settings()
    url = settings.redis_url
    if not url:
        return None

    try:
        _client = redis.from_url(url, decode_responses=True, socket_timeout=2)
        _client.ping()
        log.info("redis cache connected")
    except Exception as e:
        log.warning("redis unavailable, caching disabled: %s", e)
        _client = None
    return _client


def cached_json(key: str, ttl: int, fetch: Callable[[], Any]) -> Any:
    """
    Try to read `key` from Redis. On miss/error, call `fetch()`, store its
    JSON-encoded result with TTL, and return it. Never raises on cache failures.
    """
    client = _get_client()
    if client is None:
        return fetch()

    try:
        raw = client.get(key)
        if raw is not None:
            return json.loads(raw)
    except Exception as e:
        log.debug("cache read failed for %s: %s", key, e)

    value = fetch()
    try:
        client.setex(key, ttl, json.dumps(value, default=str))
    except Exception as e:
        log.debug("cache write failed for %s: %s", key, e)
    return value


def invalidate(prefix: str) -> None:
    """Delete all keys matching prefix*. Safe no-op if Redis unavailable."""
    client = _get_client()
    if client is None:
        return
    try:
        for k in client.scan_iter(match=f"{prefix}*"):
            client.delete(k)
    except Exception:
        pass
