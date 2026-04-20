#!/usr/bin/env python3
"""
VPS Setup Script — Install and configure Redis + Celery for FreeDownloader.TOP

Run this ONCE on your VPS after deploying the new code:
    python3 setup_infrastructure.py

What it does:
    1. Installs Redis server
    2. Configures Redis for production (memory limit, persistence)
    3. Creates systemd services for Celery workers (all 5 backends)
    4. Installs Python dependencies (redis, celery, gevent)
    5. Updates Gunicorn configs for gevent workers
    6. Restarts all services
"""

import subprocess
import os
import sys

# ── VPS Config ────────────────────────────────────────────────
FREEDOWNLOADER_DIR = "/root/FreeDownloader"
VENV_BIN = f"{FREEDOWNLOADER_DIR}/venv/bin"

# Service definitions: (name, working_dir, port, queue_name, concurrency)
SERVICES = [
    ("yt",    "yt_d",          8001, "yt_d_queue",          16),
    ("fb",    "fb_downloader", 8002, "fb_downloader_queue",  8),
    ("tik",   "tik_d",         8003, "tik_d_queue",          8),
    ("insta", "insta_d",       8004, "insta_d_queue",        8),
    ("p_d",   "p_d",           8005, "p_d_queue",            8),
]


def run(cmd, check=True):
    """Run a shell command."""
    print(f"  → {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout.strip():
        print(f"    {result.stdout.strip()[:200]}")
    if result.returncode != 0 and check:
        print(f"    ⚠️ stderr: {result.stderr.strip()[:200]}")
    return result.returncode


def setup_redis():
    """Install and configure Redis."""
    print("\n═══ Step 1: Redis Installation ═══")
    run("apt-get update -qq")
    run("apt-get install -y redis-server")

    # Production Redis config
    redis_conf = """
# FreeDownloader Redis Config
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
tcp-keepalive 60
timeout 300
"""
    conf_path = "/etc/redis/redis-freedownloader.conf"
    with open(conf_path, 'w') as f:
        f.write(redis_conf)

    # Append our config to main redis.conf
    run(f"grep -q 'freedownloader' /etc/redis/redis.conf || echo 'include {conf_path}' >> /etc/redis/redis.conf")
    run("systemctl enable redis-server")
    run("systemctl restart redis-server")

    # Verify
    code = run("redis-cli ping", check=False)
    if code == 0:
        print("  ✅ Redis is running!")
    else:
        print("  ❌ Redis failed to start. Check: systemctl status redis-server")
        sys.exit(1)


def install_python_deps():
    """Install Python packages for all backends."""
    print("\n═══ Step 2: Python Dependencies ═══")
    run(f"{VENV_BIN}/pip install redis celery[redis] gevent")


def create_celery_services():
    """Create systemd services for Celery workers."""
    print("\n═══ Step 3: Celery Worker Services ═══")

    for svc_name, work_dir, port, queue, concurrency in SERVICES:
        service_name = f"celery-{svc_name}"
        service_content = f"""[Unit]
Description=Celery Worker for {svc_name} ({work_dir})
After=network.target redis-server.service

[Service]
Type=simple
User=root
WorkingDirectory={FREEDOWNLOADER_DIR}/{work_dir}
Environment="PATH={VENV_BIN}"
Environment="PYTHONPATH={FREEDOWNLOADER_DIR}"
Environment="REDIS_URL=redis://localhost:6379/0"
Environment="CELERY_BROKER_URL=redis://localhost:6379/1"
Environment="CELERY_RESULT_BACKEND=redis://localhost:6379/1"
ExecStart={VENV_BIN}/celery -A tasks worker \\
    --concurrency={concurrency} \\
    --pool=prefork \\
    -Q {queue} \\
    --loglevel=info \\
    --max-tasks-per-child=50 \\
    --max-memory-per-child=512000
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier={service_name}

[Install]
WantedBy=multi-user.target
"""
        service_path = f"/etc/systemd/system/{service_name}.service"
        with open(service_path, 'w') as f:
            f.write(service_content)
        print(f"  ✅ Created {service_path} (concurrency={concurrency})")

    run("systemctl daemon-reload")


def update_gunicorn_services():
    """Update existing Gunicorn services to use gevent workers."""
    print("\n═══ Step 4: Gunicorn Upgrade ═══")

    for svc_name, work_dir, port, _, _ in SERVICES:
        service_content = f"""[Unit]
Description={svc_name} Downloader (Flask + Gunicorn gevent)
After=network.target redis-server.service

[Service]
User=root
WorkingDirectory={FREEDOWNLOADER_DIR}/{work_dir}
Environment="PATH={VENV_BIN}"
Environment="PYTHONPATH={FREEDOWNLOADER_DIR}"
Environment="REDIS_URL=redis://localhost:6379/0"
Environment="CELERY_BROKER_URL=redis://localhost:6379/1"
Environment="CELERY_RESULT_BACKEND=redis://localhost:6379/1"
ExecStart={VENV_BIN}/gunicorn \\
    -c {FREEDOWNLOADER_DIR}/infra/gunicorn.conf.py \\
    -b 127.0.0.1:{port} \\
    app:app
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier={svc_name}

[Install]
WantedBy=multi-user.target
"""
        service_path = f"/etc/systemd/system/{svc_name}.service"
        with open(service_path, 'w') as f:
            f.write(service_content)
        print(f"  ✅ Updated {service_path} (gevent + Redis)")

    run("systemctl daemon-reload")


def start_all_services():
    """Enable and start all services."""
    print("\n═══ Step 5: Starting Services ═══")

    # Start Celery workers
    for svc_name, _, _, _, _ in SERVICES:
        celery_svc = f"celery-{svc_name}"
        run(f"systemctl enable {celery_svc}")
        run(f"systemctl restart {celery_svc}")
        print(f"  ✅ {celery_svc} started")

    # Restart Gunicorn services
    for svc_name, _, _, _, _ in SERVICES:
        run(f"systemctl restart {svc_name}.service")
        print(f"  ✅ {svc_name}.service restarted")


def verify():
    """Verify everything is running."""
    print("\n═══ Verification ═══")

    # Redis
    code = run("redis-cli ping", check=False)
    print(f"  Redis: {'✅ PONG' if code == 0 else '❌ FAILED'}")

    # Celery workers
    for svc_name, _, _, _, _ in SERVICES:
        celery_svc = f"celery-{svc_name}"
        result = subprocess.run(f"systemctl is-active {celery_svc}", shell=True,
                                capture_output=True, text=True)
        status = result.stdout.strip()
        print(f"  {celery_svc}: {'✅' if status == 'active' else '❌'} {status}")

    # Gunicorn
    for svc_name, _, port, _, _ in SERVICES:
        result = subprocess.run(f"systemctl is-active {svc_name}", shell=True,
                                capture_output=True, text=True)
        status = result.stdout.strip()
        print(f"  {svc_name} (:{port}): {'✅' if status == 'active' else '❌'} {status}")


def main():
    print("╔══════════════════════════════════════════════╗")
    print("║  FreeDownloader.TOP Infrastructure Setup     ║")
    print("║  Redis + Celery + Gevent Workers             ║")
    print("╚══════════════════════════════════════════════╝")

    if not os.path.exists(FREEDOWNLOADER_DIR):
        print(f"❌ Project not found at {FREEDOWNLOADER_DIR}")
        sys.exit(1)

    setup_redis()
    install_python_deps()
    create_celery_services()
    update_gunicorn_services()
    start_all_services()
    verify()

    print("\n✅ INFRASTRUCTURE SETUP COMPLETE!")
    print("   Next: Deploy your code with safe_deploy.py")


if __name__ == "__main__":
    main()
