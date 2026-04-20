"""
Proxy Pool — Rotating proxy support for yt-dlp and requests.

Usage:
    from infra.proxy_pool import get_proxy, mark_bad

    proxy = get_proxy()  # Returns "socks5://user:pass@host:port" or None
    if proxy:
        yt_dlp_opts['proxy'] = proxy

Configuration:
    Set PROXY_LIST env var as comma-separated proxy URLs:
    export PROXY_LIST="socks5://user:pass@1.2.3.4:1080,http://user:pass@5.6.7.8:8080"

    Or create a file at /root/FreeDownloader/proxies.txt with one proxy per line.

If no proxies are configured, get_proxy() returns None and yt-dlp uses direct connection.
"""

import os
import random
import time
import logging
import threading

logger = logging.getLogger(__name__)

# ── Proxy Pool ────────────────────────────────────────────────
_lock = threading.Lock()
_proxies = []
_bad_proxies = {}  # proxy -> timestamp when marked bad
BAD_PROXY_COOLDOWN = 300  # 5 minutes before retrying a bad proxy

# File path for proxy list
PROXY_FILE = os.environ.get('PROXY_FILE', '/root/FreeDownloader/proxies.txt')


def _load_proxies():
    """Load proxies from environment variable or file."""
    global _proxies

    # Try env var first
    env_proxies = os.environ.get('PROXY_LIST', '').strip()
    if env_proxies:
        _proxies = [p.strip() for p in env_proxies.split(',') if p.strip()]
        logger.info("✅ Loaded %d proxies from PROXY_LIST env var", len(_proxies))
        return

    # Try file
    if os.path.exists(PROXY_FILE):
        try:
            with open(PROXY_FILE, 'r') as f:
                _proxies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            if _proxies:
                logger.info("✅ Loaded %d proxies from %s", len(_proxies), PROXY_FILE)
                return
        except Exception as e:
            logger.warning("⚠️  Could not read proxy file: %s", e)

    logger.info("ℹ️  No proxies configured — using direct connection. "
                "Set PROXY_LIST env var or create %s for proxy rotation.", PROXY_FILE)


# Load on import
_load_proxies()


def get_proxy():
    """Get a random healthy proxy from the pool.

    Returns:
        Proxy URL string (e.g., 'socks5://user:pass@host:port') or None if no proxies available.
    """
    if not _proxies:
        return None

    now = time.time()

    with _lock:
        # Filter out currently-bad proxies
        available = []
        for p in _proxies:
            if p in _bad_proxies:
                if now - _bad_proxies[p] > BAD_PROXY_COOLDOWN:
                    # Cooldown expired, give it another chance
                    del _bad_proxies[p]
                    available.append(p)
            else:
                available.append(p)

        if not available:
            # All proxies are bad, reset and try again
            logger.warning("⚠️  All proxies marked bad, resetting pool")
            _bad_proxies.clear()
            available = list(_proxies)

        return random.choice(available) if available else None


def mark_bad(proxy):
    """Mark a proxy as temporarily bad after a failure.

    Args:
        proxy: The proxy URL that failed
    """
    if not proxy:
        return

    with _lock:
        _bad_proxies[proxy] = time.time()
        bad_count = len(_bad_proxies)
        total = len(_proxies)
        logger.warning("🚫 Proxy marked bad: %s (%d/%d bad)", proxy[:30], bad_count, total)


def get_proxy_count():
    """Get total number of configured proxies."""
    return len(_proxies)


def get_healthy_count():
    """Get number of currently healthy proxies."""
    now = time.time()
    with _lock:
        bad = sum(1 for p, t in _bad_proxies.items() if now - t < BAD_PROXY_COOLDOWN)
        return len(_proxies) - bad


def reload_proxies():
    """Reload proxy list from env/file (useful for hot-reloading)."""
    with _lock:
        _bad_proxies.clear()
    _load_proxies()
