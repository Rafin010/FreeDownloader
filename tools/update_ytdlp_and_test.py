import paramiko
import time

HOST = "75.127.1.75"
USER = "root"
PASS = "OcjRMVUDAPyFWB8JuUAf"

def run(client, cmd, timeout=120):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='ignore').strip()
    err = stderr.read().decode('utf-8', errors='ignore').strip()
    return out, err

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)

    # ================================
    # STEP 1: Update yt-dlp to latest
    # ================================
    print("STEP 1: Updating yt-dlp to latest version...")
    out, err = run(client, "/root/FreeDownloader/venv/bin/pip install --upgrade yt-dlp", timeout=120)
    print(f"  {out[-300:] if len(out) > 300 else out}")
    if err:
        print(f"  STDERR: {err[-200:]}")

    # Verify new version
    out, _ = run(client, "/root/FreeDownloader/venv/bin/python -c 'import yt_dlp; print(yt_dlp.version.__version__)'")
    print(f"  New yt-dlp version: {out}")

    # ================================
    # STEP 2: Restart all services to pick up new yt-dlp
    # ================================
    print("\nSTEP 2: Restarting all services...")
    run(client, "systemctl restart yt fb insta tik p")
    time.sleep(5)

    # Verify all running
    for svc in ['yt', 'fb', 'insta', 'tik', 'p']:
        out, _ = run(client, f"systemctl is-active {svc}")
        print(f"  {svc}: {out}")

    # ================================
    # STEP 3: Test with REAL video URLs
    # ================================
    print("\nSTEP 3: Testing with real video URLs...")

    real_tests = [
        {
            "name": "YouTube",
            "port": 8001,
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "timeout": 60
        },
        {
            "name": "TikTok",
            "port": 8003,
            "url": "https://www.tiktok.com/@khaby.lame/video/7252226503008036127",
            "timeout": 30
        },
    ]

    for test in real_tests:
        print(f"\n  Testing {test['name']}...")
        cmd = (
            f"curl -s -X POST http://127.0.0.1:{test['port']}/api/get_info "
            f"-H 'Content-Type: application/json' "
            f"-d '{{\"url\": \"{test['url']}\"}}' "
            f"--max-time {test['timeout']}"
        )
        out, _ = run(client, cmd, timeout=test['timeout'] + 10)
        if len(out) > 500:
            out = out[:500] + "..."
        print(f"  Response: {out if out else 'EMPTY (timeout)'}")

    client.close()
    print("\nDone!")

if __name__ == "__main__":
    main()
