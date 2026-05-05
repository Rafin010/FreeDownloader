import paramiko

def fix_nginx_port():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print("Connecting to server...")
        client.connect(hostname, port, username, password)
        
        # Change 8009 to 8005 in p.freedownloader.top nginx config
        script = """
        sed -i 's/8009/8005/g' /etc/nginx/sites-available/p.freedownloader.top
        sed -i 's/8009/8005/g' /etc/nginx/sites-enabled/p.freedownloader.top 2>/dev/null || true
        systemctl restart nginx
        echo "Nginx updated and restarted successfully."
        """
        
        stdin, stdout, stderr = client.exec_command(script, timeout=30)
        out = stdout.read().decode('utf-8', 'replace').strip()
        print("OUTPUT:\n", out)
        err = stderr.read().decode('utf-8', 'replace').strip()
        if err:
            print("ERR:\n", err)
            
    except Exception as e:
        print("Exception:", e)
    finally:
        client.close()

if __name__ == "__main__":
    fix_nginx_port()
