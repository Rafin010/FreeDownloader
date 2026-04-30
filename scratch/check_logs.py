import paramiko

def check_logs():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, port, username, password, timeout=10)
        
        print("--- yt.service Status ---")
        stdin, stdout, stderr = client.exec_command("systemctl status yt.service --no-pager")
        print(stdout.read().decode('utf-8', errors='replace').encode('ascii', errors='replace').decode('ascii'))
        
        print("\n--- yt.service Logs ---")
        stdin, stdout, stderr = client.exec_command("journalctl -u yt.service -n 50 --no-pager")
        print(stdout.read().decode('utf-8', errors='replace').encode('ascii', errors='replace').decode('ascii'))
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    check_logs()
