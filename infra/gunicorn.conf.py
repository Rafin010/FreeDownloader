# Gunicorn Production Configuration for Memory Optimization
import os

# ── Workers ───────────────────────────────────────────────────
# Use sync/gthread instead of gevent to save memory
worker_class = 'gthread'
# Fixed 1 worker for minimal idle memory usage
workers = 1
# Allow 2-4 concurrent threads per worker for handling requests
threads = 4

# ── Timeouts ──────────────────────────────────────────────────
timeout = 300                      # 5 min — allows long sync downloads
graceful_timeout = 30
keepalive = 2                      # Reduced keepalive

# ── Memory Management ────────────────────────────────────────
max_requests = 100                 # Recycle frequently to prevent memory leaks
max_requests_jitter = 10

# ── Logging ───────────────────────────────────────────────────
accesslog = '-'
errorlog = '-'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# ── Server ────────────────────────────────────────────────────
bind = [
    '0.0.0.0:8004',   # yt_d       → y.freedownloader.top
    '0.0.0.0:8001',   # fb_d       → f.freedownloader.top
    '0.0.0.0:8002',   # insta_d    → i.freedownloader.top
    '0.0.0.0:8003',   # tik_d      → t.freedownloader.top
    '0.0.0.0:8009',   # p_d        → p.freedownloader.top
    '0.0.0.0:5000',   # backend    → admin.freedownloader.top
    '0.0.0.0:8010',   # freeStore  → freedownloader.top
    '0.0.0.0:5007',   # donate_app → donate.freedownloader.top
    '0.0.0.0:8008',   # free_d     → web.freedownloader.top
]
preload_app = False                # False saves memory if many workers, but true is better for 1 worker. Left False for yt-dlp safety.
forwarded_allow_ips = '*'
