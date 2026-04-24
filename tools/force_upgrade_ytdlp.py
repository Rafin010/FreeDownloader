import paramiko
import time

HOST = "75.127.1.75"
USER = "root"
PASS = "OcjRMVUDAPyFWB8JuUAf"

def run(client, cmd, timeout=180):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='ignore').strip()
    err = stderr.read().decode('utf-8', errors='ignore').strip()
    return out, err

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)

    # Check Python version
    out, _ = run(client, "/root/FreeDownloader/venv/bin/python --version")
    print(f"Python version: {out}")

    # Force upgrade yt-dlp
    print("\nForce upgrading yt-dlp...")
    out, err = run(client, "/root/FreeDownloader/venv/bin/pip install --upgrade --force-reinstall yt-dlp", timeout=180)
    # Show last part
    lines = (out + "\n" + err).strip().split('\n')
    for line in lines[-10:]:
        print(f"  {line}")

    # Check new version
    out, _ = run(client, "/root/FreeDownloader/venv/bin/python -c 'import yt_dlp; print(yt_dlp.version.__version__)'")
    print(f"\nyt-dlp version after upgrade: {out}")

    # Also upgrade pip itself
    print("\nUpgrading pip...")
    out, _ = run(client, "/root/FreeDownloader/venv/bin/pip install --upgrade pip", timeout=60)
    print(f"  {out[-200:]}")

    # Try to install latest yt-dlp from git nightly if pip version is old
    if "2025" in out or True:
        print("\nTrying yt-dlp nightly/latest from PyPI...")
        out, err = run(client, "/root/FreeDownloader/venv/bin/pip install -U 'yt-dlp>=2026.0.0' 2>&1 || /root/FreeDownloader/venv/bin/pip install -U yt-dlp 2>&1", timeout=120)
        lines = (out + "\n" + err).strip().split('\n')
        for line in lines[-5:]:
            print(f"  {line}")

    # Final version check
    out, _ = run(client, "/root/FreeDownloader/venv/bin/python -c 'import yt_dlp; print(yt_dlp.version.__version__)'")
    print(f"\nFinal yt-dlp version: {out}")

    # Now let's see the actual server error logs for the YouTube test
    print("\n" + "="*60)
    print("CHECKING SERVER LOGS for YouTube extraction errors")
    print("="*60)
    
    # Get recent yt service logs
    out, _ = run(client, "journalctl -u yt.service --since '5 minutes ago' --no-pager | tail -40")
    open('yt_recent_logs.txt', 'w', encoding='utf-8').write(out)
    # Show error lines
    for line in out.split('\n'):
        if 'ERROR' in line or 'error' in line.lower() or 'WARNING' in line or 'failed' in line.lower():
            print(f"  {line.strip()[:150]}")

    # Direct test with yt-dlp on the server
    print("\n" + "="*60)
    print("DIRECT yt-dlp test on server (not via Flask)")
    print("="*60)
    out, err = run(client, 
        "cd /root/FreeDownloader/yt_d && "
        "/root/FreeDownloader/venv/bin/python -c \""
        "import yt_dlp; "
        "ydl = yt_dlp.YoutubeDL({'quiet': False, 'no_warnings': False, 'socket_timeout': 30}); "
        "try:\\n"
        "    info = ydl.extract_info('https://www.youtube.com/watch?v=dQw4w9WgXcQ', download=False)\\n"
        "    print('SUCCESS:', info.get('title', 'NO TITLE'))\\n"
        "except Exception as e:\\n"
        "    print('FAILED:', str(e)[:300])\\n"
        "\"", timeout=60)
    print(f"  stdout: {out[:500]}")
    if err:
        print(f"  stderr: {err[:500]}")

    # Restart services after upgrade
    print("\nRestarting all services with new yt-dlp...")
    run(client, "systemctl restart yt fb insta tik p")
    time.sleep(3)
    for svc in ['yt', 'fb', 'insta', 'tik', 'p']:
        o, _ = run(client, f"systemctl is-active {svc}")
        print(f"  {svc}: {o}")

    client.close()
    print("\nDone!")

if __name__ == "__main__":
    main()
