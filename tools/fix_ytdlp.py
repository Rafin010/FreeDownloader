import paramiko

def fix_ytdlp():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, port, username, password)
        
        commands = [
            # Force reinstall yt-dlp
            "/root/FreeDownloader/venv/bin/pip install --force-reinstall yt-dlp",
            "/root/FreeDownloader/venv/bin/yt-dlp --version",
            # Check python version
            "/root/FreeDownloader/venv/bin/python --version",
            # Restart all services
            "pkill gunicorn; sleep 1; systemctl restart freedownloader.service fb.service insta.service tiktok.service yt.service free_d.service p_d.service",
            "systemctl is-active freedownloader.service fb.service insta.service tiktok.service yt.service free_d.service p_d.service"
        ]
        
        for cmd in commands:
            print(f">>> {cmd[:80]}...")
            stdin, stdout, stderr = client.exec_command(cmd, timeout=120)
            stdout.channel.recv_exit_status()
            out = stdout.read().decode('utf-8', 'replace').strip()
            err = stderr.read().decode('utf-8', 'replace').strip()
            if out:
                print("OUT:", out.encode('ascii', 'replace').decode('ascii'))
            if err:
                print("ERR:", err.encode('ascii', 'replace').decode('ascii'))
        
        print("Done!")
    except Exception as e:
        print("Exception:", e)
    finally:
        client.close()

if __name__ == "__main__":
    fix_ytdlp()
