import paramiko

def research_fb():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, port, username, password)
        commands = [
            "cat /root/FreeDownloader/fb_downloader/app.py",
            "journalctl -u fb.service -n 100 --no-pager",
            "/root/FreeDownloader/venv/bin/pip install --upgrade yt-dlp" # Let's try to update it as a fix part of research or just check
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
    research_fb()
