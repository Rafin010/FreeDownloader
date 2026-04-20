"""
Redis Client — Shared connection pool, caching, and rate limiting backend.

Usage:
    from infra.redis_client import get_redis, cache_get, cache_set

Graceful degradation: If Redis is unavailable, all operations become no-ops
so the app continues working (just without caching).
"""

import os
import json
import logging
import hashlib

logger = logging.getLogger(__name__)

# ── Redis Connection ──────────────────────────────────────────
_redis_client = None
_redis_available = False

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')


def get_redis():
    """Get or create a shared Redis client with connection pooling."""
    global _redis_client, _redis_available

    if _redis_client is not None:
        return _redis_client if _redis_available else None

    try:
        import redis
        _redis_client = redis.Redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        # Verify connection
        _redis_client.ping()
        _redis_available = True
        logger.info("✅ Redis connected: %s", REDIS_URL)
        return _redis_client
    except ImportError:
        logger.warning("⚠️  redis package not installed — caching DISABLED. "
                       "Install with: pip install redis")
        _redis_available = False
        return None
    except Exception as e:
        logger.warning("⚠️  Redis connection failed (%s) — caching DISABLED. "
                       "Install/start Redis: sudo apt install redis-server", str(e)[:80])
        _redis_available = False
        return None


def is_redis_available():
    """Check if Redis is connected and available."""
    return get_redis() is not None


# ── Caching Helpers ───────────────────────────────────────────
def _make_cache_key(prefix, url):
    """Create a consistent cache key from a URL."""
    url_hash = hashlib.md5(url.encode()).hexdigest()
    return f"fd:{prefix}:{url_hash}"


def cache_get(prefix, url):
    """Get cached data for a URL. Returns dict or None.

    Args:
        prefix: Cache namespace (e.g., 'yt_info', 'fb_info')
        url: The video URL being looked up
    """
    r = get_redis()
    if not r:
        return None

    try:
        key = _make_cache_key(prefix, url)
        data = r.get(key)
        if data:
            logger.debug("🎯 Cache HIT: %s", key)
            return json.loads(data)
        logger.debug("❌ Cache MISS: %s", key)
        return None
    except Exception as e:
        logger.warning("Cache get error: %s", str(e)[:80])
        return None


def cache_set(prefix, url, data, ttl=600):
    """Cache data for a URL with TTL (default 10 minutes).

    Args:
        prefix: Cache namespace (e.g., 'yt_info', 'fb_info')
        url: The video URL being cached
        data: Dict to cache (JSON-serializable)
        ttl: Time-to-live in seconds (default 600 = 10 min)
    """
    r = get_redis()
    if not r:
        return False

    try:
        key = _make_cache_key(prefix, url)
        r.setex(key, ttl, json.dumps(data))
        logger.debug("💾 Cached: %s (TTL=%ds)", key, ttl)
        return True
    except Exception as e:
        logger.warning("Cache set error: %s", str(e)[:80])
        return False


def cache_delete(prefix, url):
    """Delete a cached entry."""
    r = get_redis()
    if not r:
        return False

    try:
        key = _make_cache_key(prefix, url)
        r.delete(key)
        return True
    except Exception:
        return False


# ── Rate Limiter Storage URI ──────────────────────────────────
def get_limiter_storage_uri():
    """Return Redis URI for flask-limiter if available, else memory://."""
    if is_redis_available():
        return REDIS_URL
    return "memory://"
