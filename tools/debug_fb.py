import paramiko

def check_fb_logs():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, port, username, password)
        # ৫৪ নম্বর লাইনের আশেপাশে বা এরর মেসেজ দেখার জন্য শেষ ৫০ টি লগ চেক করছি
        commands = [
            "journalctl -u fb.service -n 50 --no-pager",
            "/root/FreeDownloader/venv/bin/pip show yt-dlp || true",
            "/root/FreeDownloader/venv/bin/yt-dlp --version || true"
        ]
        
        for cmd in commands:
            print(f">>> {cmd}")
            stdin, stdout, stderr = client.exec_command(cmd)
            stdout.channel.recv_exit_status()
            print("OUT:", stdout.read().decode('utf-8', 'replace').strip())
            print("ERR:", stderr.read().decode('utf-8', 'replace').strip())
            
    except Exception as e:
        print("Exception:", e)
    finally:
        client.close()

if __name__ == "__main__":
    check_fb_logs()
