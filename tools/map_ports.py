import paramiko
import re

def map_ports_and_subdomains():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, port, username, password)
        
        script = """
        echo "=== BACKEND SERVICES (listening ports) ==="
        grep -E 'ExecStart.*-b|gunicorn' /etc/systemd/system/fb.service /etc/systemd/system/insta.service /etc/systemd/system/tiktok.service /etc/systemd/system/yt.service /etc/systemd/system/p_d.service /etc/systemd/system/free_d.service /etc/systemd/system/freedownloader.service || true
        
        echo "=== NGINX CONFIGS (proxy pass ports) ==="
        grep -r 'proxy_pass' /etc/nginx/sites-enabled/ || true
        """
        
        stdin, stdout, stderr = client.exec_command(script, timeout=60)
        out = stdout.read().decode('utf-8', 'replace').strip()
        print(out)
        
    except Exception as e:
        print("Exception:", e)
    finally:
        client.close()

if __name__ == "__main__":
    map_ports_and_subdomains()
