import paramiko
import time
import json

HOST = "75.127.1.75"
USER = "root"
PASS = "OcjRMVUDAPyFWB8JuUAf"

def run(client, cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    stdout.channel.recv_exit_status()
    return stdout.read().decode('utf-8', errors='ignore').strip()

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)

    print("=" * 70)
    print("TESTING DOWNLOAD APIs ON ALL 5 SERVICES")
    print("=" * 70)

    tests = [
        {
            "name": "YouTube (yt)",
            "port": 8001,
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        },
        {
            "name": "Facebook (fb)",
            "port": 8002,
            "url": "https://www.facebook.com/reel/1234567890"
        },
        {
            "name": "TikTok (tik)",
            "port": 8003,
            "url": "https://www.tiktok.com/@tiktok/video/7000000000000000000"
        },
        {
            "name": "Instagram (insta)",
            "port": 8004,
            "url": "https://www.instagram.com/reel/ABC123/"
        },
        {
            "name": "Porn (p)",
            "port": 8005,
            "url": "https://www.xvideos.com/video.ihxagfe2b88/test"
        },
    ]

    for test in tests:
        print(f"\n{'='*50}")
        print(f"Testing: {test['name']} (port {test['port']})")
        print(f"URL: {test['url']}")
        print(f"{'='*50}")

        # Test get_info API
        cmd = (
            f"curl -s -X POST http://127.0.0.1:{test['port']}/api/get_info "
            f"-H 'Content-Type: application/json' "
            f"-d '{{\"url\": \"{test['url']}\"}}' "
            f"--max-time 60"
        )
        result = run(client, cmd)
        
        # Truncate if too long
        if len(result) > 500:
            result = result[:500] + "..."
        print(f"  API Response: {result}")

    # Also check yt-dlp version
    print(f"\n{'='*50}")
    print("yt-dlp version check:")
    ver = run(client, "/root/FreeDownloader/venv/bin/python -c 'import yt_dlp; print(yt_dlp.version.__version__)'")
    print(f"  Version: {ver}")
    
    # Check if yt-dlp needs update
    print("\nChecking if yt-dlp is latest...")
    update_check = run(client, "/root/FreeDownloader/venv/bin/pip show yt-dlp | grep -i version")
    print(f"  {update_check}")

    client.close()

if __name__ == "__main__":
    main()
