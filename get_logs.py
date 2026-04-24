import paramiko

def get_logs():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, port, username, password)
        
        # Check logs of fb.service and insta.service
        script = """
        echo "=== FB Service ==="
        journalctl -u fb.service -n 30 --no-pager
        echo "=== Insta Service ==="
        journalctl -u insta.service -n 30 --no-pager
        echo "=== YT Service ==="
        journalctl -u yt.service -n 30 --no-pager
        """
        
        stdin, stdout, stderr = client.exec_command(script, timeout=30)
        out = stdout.read().decode('utf-8', 'replace').strip()
        print(out)
        
    except Exception as e:
        print("Exception:", e)
    finally:
        client.close()

if __name__ == "__main__":
    get_logs()
