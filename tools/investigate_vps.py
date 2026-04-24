import paramiko

def run_investigation():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, port, username, password)
        commands = [
            "systemctl status nginx",
            "nginx -t",
            "grep -rnw '/etc/nginx/sites-enabled/' -e 'server_name'",
            "pm2 list || true",
            "systemctl status free_d.service || true",
            "systemctl status freedownloader.service || true",
            "cat /etc/nginx/sites-enabled/freedownloader"
        ]
        
        for cmd in commands:
            print(f">>> {cmd}")
            stdin, stdout, stderr = client.exec_command(cmd)
            stdout.channel.recv_exit_status()
            out = stdout.read().decode('utf-8', 'replace').strip()
            err = stderr.read().decode('utf-8', 'replace').strip()
            if out:
                print("OUT:", out.encode('ascii', 'replace').decode('ascii'))
            if err:
                print("ERR:", err.encode('ascii', 'replace').decode('ascii'))
            
    except Exception as e:
        print("Exception:", e)
    finally:
        client.close()

if __name__ == "__main__":
    run_investigation()
