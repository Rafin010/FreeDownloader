import paramiko

def run_certbot():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, port, username, password)
        commands = [
            "certbot --nginx -d admin.freedownloader.top --non-interactive --agree-tos -m admin@freedownloader.top",
            "certbot --nginx -d p.freedownloader.top --non-interactive --agree-tos -m admin@freedownloader.top",
            "certbot --nginx -d freedownloader.top -d www.freedownloader.top --non-interactive --agree-tos -m admin@freedownloader.top || true"
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
    run_certbot()
