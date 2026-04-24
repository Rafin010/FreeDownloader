import paramiko

def fix_nginx_subdomains():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print("Connecting to server...")
        client.connect(hostname, port, username, password)
        
        # We need to map:
        # Facebook (fb.service) -> 8002
        # Instagram (insta.service) -> 8004
        # YouTube (yt.service) -> 8001
        
        script = """
        echo "Fixing facebook proxy port to 8002..."
        sed -i -E 's/proxy_pass http:\/\/127.0.0.1:[0-9]+;/proxy_pass http:\/\/127.0.0.1:8002;/g' /etc/nginx/sites-available/facebook.freedownloader.top
        
        echo "Fixing instagram proxy port to 8004..."
        sed -i -E 's/proxy_pass http:\/\/127.0.0.1:[0-9]+;/proxy_pass http:\/\/127.0.0.1:8004;/g' /etc/nginx/sites-available/instagram.freedownloader.top
        
        echo "Fixing youtube proxy port to 8001..."
        sed -i -E 's/proxy_pass http:\/\/127.0.0.1:[0-9]+;/proxy_pass http:\/\/127.0.0.1:8001;/g' /etc/nginx/sites-available/youtube.freedownloader.top
        
        echo "Fixing tiktok proxy port to 8003 (just in case)..."
        sed -i -E 's/proxy_pass http:\/\/127.0.0.1:[0-9]+;/proxy_pass http:\/\/127.0.0.1:8003;/g' /etc/nginx/sites-available/tiktok.freedownloader.top

        # Ensure the symlinks exist/are correct (sometimes sites-enabled has the copied file instead of symlink so fix it there too just in case)
        sed -i -E 's/proxy_pass http:\/\/127.0.0.1:[0-9]+;/proxy_pass http:\/\/127.0.0.1:8002;/g' /etc/nginx/sites-enabled/facebook.freedownloader.top 2>/dev/null || true
        sed -i -E 's/proxy_pass http:\/\/127.0.0.1:[0-9]+;/proxy_pass http:\/\/127.0.0.1:8004;/g' /etc/nginx/sites-enabled/instagram.freedownloader.top 2>/dev/null || true
        sed -i -E 's/proxy_pass http:\/\/127.0.0.1:[0-9]+;/proxy_pass http:\/\/127.0.0.1:8001;/g' /etc/nginx/sites-enabled/youtube.freedownloader.top 2>/dev/null || true
        sed -i -E 's/proxy_pass http:\/\/127.0.0.1:[0-9]+;/proxy_pass http:\/\/127.0.0.1:8003;/g' /etc/nginx/sites-enabled/tiktok.freedownloader.top 2>/dev/null || true
        
        echo "Restarting nginx..."
        systemctl restart nginx
        
        echo "NGINX CONFIGURATIONS AFTER FIX:"
        grep "proxy_pass" /etc/nginx/sites-available/*.freedownloader.top
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
    fix_nginx_subdomains()
