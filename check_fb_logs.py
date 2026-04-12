import paramiko

def check_logs():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, port, username, password)
        
        commands = [
            "journalctl -u fb.service -n 80 --no-pager",
            # Test a real facebook video URL with yt-dlp directly
            '/root/FreeDownloader/venv/bin/yt-dlp --dump-json "https://www.facebook.com/reel/1234567890" 2>&1 | tail -5 || true',
            # Check what extractors are available
            '/root/FreeDownloader/venv/bin/yt-dlp --list-extractors 2>/dev/null | grep -i facebook',
        ]
        
        for cmd in commands:
            print(f">>> {cmd[:80]}...")
            stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
            stdout.channel.recv_exit_status()
            out = stdout.read().decode('utf-8', 'replace').strip()
            err = stderr.read().decode('utf-8', 'replace').strip()
            if out:
                print("OUT:", out.encode('ascii', 'replace').decode('ascii')[-2000:])
            if err:
                print("ERR:", err.encode('ascii', 'replace').decode('ascii')[-1000:])
            print("---")
    except Exception as e:
        print("Exception:", e)
    finally:
        client.close()

if __name__ == "__main__":
    check_logs()
