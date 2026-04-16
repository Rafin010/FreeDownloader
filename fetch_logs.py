import paramiko

def fetch_logs():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, port, username, password)
        commands = [
            "journalctl -u freestore.service -n 100 --no-pager",
            "cat /etc/nginx/sites-enabled/freestore-domains.conf",
            "cat /etc/nginx/sites-enabled/freedownloader"
        ]
        
        with open("logs_output2.txt", "w", encoding="utf-8") as f:
            for cmd in commands:
                f.write(f">>> {cmd}\n")
                stdin, stdout, stderr = client.exec_command(cmd)
                stdout.channel.recv_exit_status()
                out = stdout.read().decode('utf-8', 'replace').strip()
                err = stderr.read().decode('utf-8', 'replace').strip()
                if out:
                    f.write("OUT:\n" + out + "\n")
                if err:
                    f.write("ERR:\n" + err + "\n")
                f.write("-" * 40 + "\n")
                
    except Exception as e:
        print("Exception:", e)
    finally:
        client.close()

if __name__ == "__main__":
    fetch_logs()
