import paramiko
import time

HOST = "75.127.1.75"
USER = "root"
PASS = "OcjRMVUDAPyFWB8JuUAf"

def ssh_run(client, cmd):
    """Run a command and return stdout text (safe for unicode)."""
    stdin, stdout, stderr = client.exec_command(cmd)
    stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    return out, err

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)
    
    print("=" * 60)
    print("STEP 1: Stop all services")
    print("=" * 60)
    ssh_run(client, "systemctl stop yt fb insta tik p")
    time.sleep(1)
    
    print("STEP 2: Find EVERYTHING on port 8003")
    out, _ = ssh_run(client, "ss -tlnp | grep 8003")
    print(f"  ss output: {out}")
    
    out, _ = ssh_run(client, "fuser 8003/tcp 2>/dev/null")
    print(f"  fuser output: '{out.strip()}'")
    
    print("STEP 3: Kill ALL gunicorn processes aggressively")
    ssh_run(client, "pkill -9 -f gunicorn")
    time.sleep(1)
    
    print("STEP 4: Force kill anything on port 8003")
    ssh_run(client, "fuser -k 8003/tcp 2>/dev/null")
    time.sleep(1)
    
    # Check again
    out, _ = ssh_run(client, "fuser 8003/tcp 2>/dev/null")
    print(f"  Port 8003 after fuser -k: '{out.strip()}'")
    
    if out.strip():
        print("  Still occupied! Using kill -9 on PIDs...")
        pids = out.strip().split()
        for pid in pids:
            pid = pid.strip()
            if pid.isdigit():
                ssh_run(client, f"kill -9 {pid}")
        time.sleep(1)
    
    print("STEP 5: Force kill anything on port 8005 (for p service)")  
    ssh_run(client, "fuser -k 8005/tcp 2>/dev/null")
    time.sleep(1)
    
    # Verify ports are free
    out, _ = ssh_run(client, "ss -tlnp | grep -E '800[1-5]'")
    print(f"  Ports 8001-8005 status: {out if out.strip() else 'ALL FREE'}")
    
    print()
    print("=" * 60)
    print("STEP 6: Check if p.service exists and what port it uses")
    print("=" * 60)
    out, err = ssh_run(client, "cat /etc/systemd/system/p.service 2>/dev/null || echo 'FILE NOT FOUND'")
    print(out)
    
    print("=" * 60)
    print("STEP 7: Check tik service WorkingDirectory and app.py")
    print("=" * 60)
    out, _ = ssh_run(client, "ls -la /root/FreeDownloader/tik_d/app.py")
    print(f"  tik app.py: {out.strip()}")
    out, _ = ssh_run(client, "ls -la /root/FreeDownloader/p_d/app.py 2>/dev/null || echo 'p_d/app.py NOT FOUND'")
    print(f"  p app.py: {out.strip()}")
    
    print()
    print("=" * 60)
    print("STEP 8: Check nginx config for subdomains -> ports")
    print("=" * 60)
    out, _ = ssh_run(client, "grep -r 'proxy_pass' /etc/nginx/sites-enabled/ 2>/dev/null")
    print(out)
    
    print()
    print("=" * 60)
    print("STEP 9: Start all services")
    print("=" * 60)
    ssh_run(client, "systemctl daemon-reload")
    ssh_run(client, "systemctl start yt fb insta tik p")
    time.sleep(3)
    
    print("STEP 10: Check final status")
    for svc in ['yt', 'fb', 'insta', 'tik', 'p']:
        out, _ = ssh_run(client, f"systemctl is-active {svc}")
        print(f"  {svc}: {out.strip()}")
    
    # Check ports
    out, _ = ssh_run(client, "ss -tlnp | grep -E '800[1-5]'")
    print(f"\n  Listening ports:\n{out}")
    
    # Test each service with curl
    print("=" * 60)
    print("STEP 11: Test each service endpoint")
    print("=" * 60)
    for port, name in [(8001, 'yt'), (8002, 'fb'), (8003, 'tik'), (8004, 'insta'), (8005, 'p')]:
        out, _ = ssh_run(client, f"curl -s -o /dev/null -w '%{{http_code}}' http://127.0.0.1:{port}/ --max-time 5")
        print(f"  {name} (:{port}): HTTP {out.strip()}")
    
    client.close()
    print("\nDone!")

if __name__ == "__main__":
    main()
