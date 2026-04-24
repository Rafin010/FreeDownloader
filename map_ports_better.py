import paramiko

def better_map_ports():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, port, username, password)
        
        script = """
        echo "=== ALL SERVICE PORTS ==="
        grep "\-b" /etc/systemd/system/*.service || true
        
        echo "=== NGINX PROXY PORTS ==="
        grep -r "proxy_pass" /etc/nginx/sites-enabled/ || true
        """
        
        stdin, stdout, stderr = client.exec_command(script, timeout=30)
        out = stdout.read().decode('utf-8', 'replace').strip()
        print(out)
        
    except Exception as e:
        print("Exception:", e)
    finally:
        client.close()

if __name__ == "__main__":
    better_map_ports()
