"""
Full SFTP Deploy for Donate Payment System
Uploads all project files and restarts services.
"""
import paramiko
import os

hostname = "75.127.1.75"
port = 22
username = "root"
password = "OcjRMVUDAPyFWB8JuUAf"

LOCAL_BASE = r"E:\_free downloader Projext\Donate"
REMOTE_BASE = "/root/FreeDownloader/Donate"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname, port, username, password)
sftp = client.open_sftp()

# Create all remote directories
dirs = [
    REMOTE_BASE,
    f"{REMOTE_BASE}/templates",
    f"{REMOTE_BASE}/static",
    f"{REMOTE_BASE}/utils",
    f"{REMOTE_BASE}/services",
    f"{REMOTE_BASE}/routes",
]
for d in dirs:
    try:
        sftp.stat(d)
    except FileNotFoundError:
        sftp.mkdir(d)
        print(f"Created: {d}")

# Upload all project files
files = [
    ("app.py", "app.py"),
    ("config.py", "config.py"),
    (".env", ".env"),
    ("utils/__init__.py", "utils/__init__.py"),
    ("utils/db.py", "utils/db.py"),
    ("services/__init__.py", "services/__init__.py"),
    ("services/bkash.py", "services/bkash.py"),
    ("services/nagad.py", "services/nagad.py"),
    ("services/rocket.py", "services/rocket.py"),
    ("services/stripe_pay.py", "services/stripe_pay.py"),
    ("services/paypal_pay.py", "services/paypal_pay.py"),
    ("routes/__init__.py", "routes/__init__.py"),
    ("routes/payment_routes.py", "routes/payment_routes.py"),
    ("routes/webhook_routes.py", "routes/webhook_routes.py"),
    ("templates/index.html", "templates/index.html"),
]

for local_rel, remote_rel in files:
    local_path = os.path.join(LOCAL_BASE, local_rel)
    remote_path = f"{REMOTE_BASE}/{remote_rel}"
    if os.path.exists(local_path):
        sftp.put(local_path, remote_path)
        print(f"  Uploaded: {remote_rel}")
    else:
        print(f"  MISSING: {local_rel}")

# Upload static images
static_dir = os.path.join(LOCAL_BASE, "static")
if os.path.isdir(static_dir):
    for f in os.listdir(static_dir):
        local_path = os.path.join(static_dir, f)
        if os.path.isfile(local_path):
            sftp.put(local_path, f"{REMOTE_BASE}/static/{f}")
            print(f"  Uploaded static: {f}")

# Upload nginx config
nginx_local = r"E:\_free downloader Projext\nginx\freestore-domains.conf"
if os.path.exists(nginx_local):
    sftp.put(nginx_local, "/root/FreeDownloader/nginx/freestore-domains.conf")
    print("  Uploaded: freestore-domains.conf")

# Upload backend donate_routes too
dr_local = r"E:\_free downloader Projext\backend\routes\donate_routes.py"
if os.path.exists(dr_local):
    sftp.put(dr_local, "/root/FreeDownloader/backend/routes/donate_routes.py")
    print("  Uploaded: backend/donate_routes.py")

sftp.close()

# Install dependencies and restart
cmds = [
    "source /root/FreeDownloader/venv/bin/activate && pip install python-dotenv requests stripe 2>&1 | tail -5",
    "cp /root/FreeDownloader/nginx/freestore-domains.conf /etc/nginx/sites-available/freestore-domains.conf",
    "ln -sf /etc/nginx/sites-available/freestore-domains.conf /etc/nginx/sites-enabled/",
    "nginx -t && systemctl reload nginx",
    """cat << 'EOF' > /etc/systemd/system/donate.service
[Unit]
Description=Donate Payment Microservice (Flask)
After=network.target

[Service]
User=root
WorkingDirectory=/root/FreeDownloader/Donate
Environment="PATH=/root/FreeDownloader/venv/bin"
ExecStart=/root/FreeDownloader/venv/bin/gunicorn -w 2 -b 127.0.0.1:5007 app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF""",
    "systemctl daemon-reload",
    "systemctl enable donate",
    "systemctl restart donate freedownloader",
]

print("\n--- Running server commands ---")
for cmd in cmds:
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out: print(f"  {out}")
    if err: print(f"  stderr: {err}")

# Check service status
stdin, stdout, stderr = client.exec_command("systemctl is-active donate")
status = stdout.read().decode().strip()
print(f"\n[DONATE SERVICE STATUS] {status}")

print("\n=== DEPLOYMENT COMPLETE ===")
client.close()
