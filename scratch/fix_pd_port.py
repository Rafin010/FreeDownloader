import paramiko

def fix():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, port, username, password)
        print("Connected to VPS")
        
        # Kill any process on 8005 and restart p_d
        commands = [
            "fuser -k 8005/tcp || true",
            "sleep 2",
            "systemctl restart p_d.service",
            "systemctl is-active p_d.service"
        ]
        
        for cmd in commands:
            print(f"Running: {cmd}")
            stdin, stdout, stderr = client.exec_command(cmd)
            print(stdout.read().decode())
            print(stderr.read().decode())
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    fix()
