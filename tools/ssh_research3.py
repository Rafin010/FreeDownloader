import paramiko
import sys

def run_ssh_commands():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, port, username, password)
        
        commands = [
            "ls -la /etc/nginx/sites-enabled",
            "cat /etc/nginx/sites-enabled/*",
            "ls -la /etc/systemd/system | grep -i free",
            "ls -la /etc/systemd/system | grep -i fb",
            "ls -la /etc/systemd/system | grep -i insta",
            "ls -la /etc/systemd/system | grep -i yt",
            "ls -la /etc/systemd/system | grep -i tik",
        ]
        
        for cmd in commands:
            print(f"\n--- Running: {cmd} ---")
            stdin, stdout, stderr = client.exec_command(cmd)
            stdout.channel.recv_exit_status()
            print(stdout.read().decode('utf-8'))
            err = stderr.read().decode('utf-8')
            if err:
                print("Error:", err)
                
    except Exception as e:
        print("Exception:", e)
    finally:
        client.close()

if __name__ == "__main__":
    run_ssh_commands()
