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
        print("Connecting...")
        client.connect(hostname, port, username, password)
        print("Connected!")
        
        commands = [
            "ls -la /var/www",
            "ls -la /etc/nginx/sites-enabled",
            "pm2 list || true",
            "ps aux | grep gunicorn | grep -v grep || true"
        ]
        
        for cmd in commands:
            print(f"\n--- Running: {cmd} ---")
            stdin, stdout, stderr = client.exec_command(cmd)
            stdout.channel.recv_exit_status() # wait for end
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
