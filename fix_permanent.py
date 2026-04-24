import paramiko
import time

HOST = "75.127.1.75"
USER = "root"
PASS = "OcjRMVUDAPyFWB8JuUAf"

def ssh_run(client, cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    return out, err

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)

    # ==========================================
    # FIX 1: Kill the rogue 0.0.0.0:8003 gunicorn
    # ==========================================
    print("FIX 1: Kill rogue gunicorn on 0.0.0.0:8003")
    # Find PIDs bound to 0.0.0.0:8003 (not 127.0.0.1:8003)
    out, _ = ssh_run(client, "ss -tlnp | grep '0.0.0.0:8003'")
    print(f"  Rogue process: {out.strip()}")
    
    # Stop tik service first
    ssh_run(client, "systemctl stop tik")
    time.sleep(1)
    
    # Kill everything on port 8003
    ssh_run(client, "fuser -k -9 8003/tcp")
    time.sleep(2)
    
    # Verify it's dead
    out, _ = ssh_run(client, "fuser 8003/tcp 2>/dev/null")
    print(f"  Port 8003 after kill: '{out.strip()}'")
    
    if out.strip():
        # Nuclear option
        pids = out.strip().split()
        for p in pids:
            p = p.strip()
            if p.isdigit():
                ssh_run(client, f"kill -9 {p}")
                print(f"  Killed PID {p}")
        time.sleep(2)
        out, _ = ssh_run(client, "fuser 8003/tcp 2>/dev/null")
        print(f"  Port 8003 final check: '{out.strip()}'")

    # ==========================================
    # FIX 2: Create p.service for porn downloader
    # ==========================================
    print("\nFIX 2: Create p.service")
    p_service = """[Unit]
Description=Porn Downloader (Flask + Gunicorn gevent)
After=network.target redis-server.service

[Service]
User=root
WorkingDirectory=/root/FreeDownloader/p_d
Environment="PATH=/root/FreeDownloader/venv/bin"
Environment="PYTHONPATH=/root/FreeDownloader"
Environment="REDIS_URL=redis://localhost:6379/0"
Environment="CELERY_BROKER_URL=redis://localhost:6379/1"
Environment="CELERY_RESULT_BACKEND=redis://localhost:6379/1"
ExecStartPre=/bin/bash -c '/usr/bin/fuser -k 8005/tcp 2>/dev/null || true'
ExecStart=/root/FreeDownloader/venv/bin/gunicorn \\
    -c /root/FreeDownloader/infra/gunicorn.conf.py \\
    -b 127.0.0.1:8005 \\
    app:app
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=p

[Install]
WantedBy=multi-user.target
"""
    # Write p.service
    escaped = p_service.replace("'", "'\\''")
    ssh_run(client, f"cat > /etc/systemd/system/p.service << 'SERVICEEOF'\n{p_service}SERVICEEOF")
    
    # Verify
    out, _ = ssh_run(client, "cat /etc/systemd/system/p.service")
    print(f"  p.service created: {len(out)} bytes")

    # ==========================================
    # FIX 3: Add ExecStartPre to tik.service to prevent port collision
    # ==========================================
    print("\nFIX 3: Fix tik.service with ExecStartPre to kill stale port holders")
    tik_service = """[Unit]
Description=tik Downloader (Flask + Gunicorn gevent)
After=network.target redis-server.service

[Service]
User=root
WorkingDirectory=/root/FreeDownloader/tik_d
Environment="PATH=/root/FreeDownloader/venv/bin"
Environment="PYTHONPATH=/root/FreeDownloader"
Environment="REDIS_URL=redis://localhost:6379/0"
Environment="CELERY_BROKER_URL=redis://localhost:6379/1"
Environment="CELERY_RESULT_BACKEND=redis://localhost:6379/1"
ExecStartPre=/bin/bash -c '/usr/bin/fuser -k 8003/tcp 2>/dev/null || true'
ExecStart=/root/FreeDownloader/venv/bin/gunicorn \\
    -c /root/FreeDownloader/infra/gunicorn.conf.py \\
    -b 127.0.0.1:8003 \\
    app:app
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=tik

[Install]
WantedBy=multi-user.target
"""
    ssh_run(client, f"cat > /etc/systemd/system/tik.service << 'SERVICEEOF'\n{tik_service}SERVICEEOF")
    out, _ = ssh_run(client, "cat /etc/systemd/system/tik.service")
    print(f"  tik.service updated: {len(out)} bytes")

    # ==========================================
    # FIX 4: Enable services and restart
    # ==========================================
    print("\nFIX 4: Reload, enable, and restart tik + p services")
    
    # Kill anything on 8003 and 8005 before starting
    ssh_run(client, "fuser -k -9 8003/tcp 2>/dev/null")
    ssh_run(client, "fuser -k -9 8005/tcp 2>/dev/null")
    time.sleep(2)
    
    ssh_run(client, "systemctl daemon-reload")
    ssh_run(client, "systemctl enable tik p")
    ssh_run(client, "systemctl restart tik p")
    time.sleep(5)

    # ==========================================
    # VERIFY
    # ==========================================
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)
    
    for svc in ['yt', 'fb', 'insta', 'tik', 'p']:
        out, _ = ssh_run(client, f"systemctl is-active {svc}")
        status = out.strip()
        icon = "OK" if status == "active" else "FAIL"
        print(f"  [{icon}] {svc}: {status}")
    
    print()
    out, _ = ssh_run(client, "ss -tlnp | grep -E '800[1-5]'")
    print(f"Listening ports:\n{out}")
    
    print("Testing HTTP endpoints:")
    for port, name in [(8001, 'yt'), (8002, 'fb'), (8003, 'tik'), (8004, 'insta'), (8005, 'p')]:
        out, _ = ssh_run(client, f"curl -s -o /dev/null -w '%{{http_code}}' http://127.0.0.1:{port}/ --max-time 5")
        code = out.strip()
        icon = "OK" if code == "200" else "FAIL"
        print(f"  [{icon}] {name} (:{port}): HTTP {code}")

    client.close()
    print("\nAll fixes applied!")

if __name__ == "__main__":
    main()
