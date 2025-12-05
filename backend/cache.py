# backend/cache.py
import json
import redis
from backend.config import Config

_redis = redis.Redis.from_url(Config.REDIS_URL)


def cache_get(key: str):
    """Return cached JSON data for key, or None."""
    raw = _redis.get(key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def cache_set(key: str, value, ttl: int = 60):
    """Store JSON-serializable data with TTL in seconds."""
    _redis.setex(key, ttl, json.dumps(value))


def cache_delete(prefix: str):
    """Delete all keys starting with prefix (for invalidation)."""
    pattern = prefix + "*"
    for k in _redis.scan_iter(match=pattern):
        _redis.delete(k)
