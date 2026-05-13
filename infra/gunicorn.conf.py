# Gunicorn Production Configuration for FreeDownloader.TOP
# Usage: gunicorn -c /root/FreeDownloader/infra/gunicorn.conf.py app:app

import multiprocessing
import os

# ── Workers ───────────────────────────────────────────────────
# gevent allows each worker to handle thousands of concurrent connections
# (vs sync workers which handle only 1 at a time)
worker_class = 'gevent'
workers = int(os.environ.get('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2))
worker_connections = 1000          # Max concurrent connections per gevent worker
threads = 1                        # Not needed with gevent

# ── Timeouts ──────────────────────────────────────────────────
timeout = 300                      # 5 min — allows long sync downloads (fallback)
graceful_timeout = 30              # Time to finish requests on restart
keepalive = 5                      # Keep connection alive for 5s

# ── Memory Management ────────────────────────────────────────
max_requests = 1000                # Recycle worker after 1000 requests (prevents leaks)
max_requests_jitter = 50           # Random jitter to prevent all workers recycling at once

# ── Logging ───────────────────────────────────────────────────
accesslog = '-'                    # Log to stdout
errorlog = '-'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# ── Server ────────────────────────────────────────────────────
bind = os.environ.get('GUNICORN_BIND', '127.0.0.1:8000')
preload_app = False                 # Load app after forking (avoids gevent monkey-patch issues with yt-dlp)
forwarded_allow_ips = '*'          # Trust X-Forwarded-For from nginx

# ── Hooks ─────────────────────────────────────────────────────
def post_fork(server, worker):
    """Called after a worker process is forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def worker_exit(server, worker):
    """Called when a worker exits."""
    server.log.info("Worker exited (pid: %s)", worker.pid)
