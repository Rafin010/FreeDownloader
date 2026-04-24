import paramiko

def deploy_fix():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print("Connecting to VPS...")
        client.connect(hostname, port, username, password)
        print("Connected!\n")

        commands = [
            # 1. Pull latest code
            "cd /root/FreeDownloader && git fetch origin && git reset --hard origin/main",

            # 2. Update yt-dlp and curl-cffi in the virtual environment where services run
            "/root/FreeDownloader/venv/bin/pip install -U yt-dlp curl-cffi 2>&1",

            # 3. Restart services
            "systemctl restart yt.service",
            "systemctl restart fb.service",

            # 4. Check statuses
            "systemctl is-active yt.service",
            "systemctl is-active fb.service",

            # 5. Verify the yt-dlp version in the venv
            "/root/FreeDownloader/venv/bin/python -c 'import yt_dlp; print(\"yt-dlp version:\", yt_dlp.version.__version__)'",
        ]

        for cmd in commands:
            print(f">>> Running: {cmd[:100]}...")
            stdin, stdout, stderr = client.exec_command(cmd, timeout=60)
            status = stdout.channel.recv_exit_status()
            out = stdout.read().decode('utf-8', errors='replace').strip()
            err = stderr.read().decode('utf-8', errors='replace').strip()

            if out:
                print(f"  OUT: {out}")
            if err:
                print(f"  ERR: {err}")
            print(f"  Status: {status}\n")

        print("=" * 60)
        print("DEPLOYMENT COMPLETE")
        print("=" * 60)

    except Exception as e:
        print(f"Exception: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    deploy_fix()
