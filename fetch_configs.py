import paramiko
import json
import os

def run_ssh_commands():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    results = {}
    
    try:
        client.connect(hostname, port, username, password)
        
        commands = [
            "cat /etc/nginx/sites-enabled/*",
            "cat /etc/systemd/system/freedownloader.service || true",
            "cat /etc/systemd/system/fb.service || true",
            "cat /etc/systemd/system/insta.service || true",
            "cat /etc/systemd/system/tiktok.service || true",
            "ls -la /root/FreeDownloader"
        ]
        
        for cmd in commands:
            stdin, stdout, stderr = client.exec_command(cmd)
            stdout.channel.recv_exit_status()
            out = stdout.read().decode('utf-8')
            results[cmd] = out
            
        with open("scratch/remote_configs.json", "w", encoding='utf-8') as f:
            json.dump(results, f, indent=4)
            print("Saved to scratch/remote_configs.json")
                
    except Exception as e:
        print("Exception:", e)
    finally:
        client.close()

if __name__ == "__main__":
    run_ssh_commands()
