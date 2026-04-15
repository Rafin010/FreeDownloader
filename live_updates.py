import paramiko

def deploy():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print("Connecting to Server...")
        client.connect(hostname, port, username, password)
        print("Connected!")
        
        script = """
echo "Pulling latest changes from GitHub..."
cd /root/FreeDownloader && git fetch origin && git reset --hard origin/main

echo "Installing curl-cffi for TLS Impersonation and updating yt-dlp..."
/root/FreeDownloader/venv/bin/pip install --upgrade curl-cffi yt-dlp

echo "Stopping gunicorn..."
pkill gunicorn || true
sleep 2

echo "Restarting all services..."
systemctl restart freedownloader.service fb.service insta.service tiktok.service yt.service free_d.service p_d.service
sleep 2

echo "Checking the status of services..."
systemctl is-active freedownloader.service fb.service insta.service tiktok.service yt.service free_d.service p_d.service
"""
        
        print("Executing deployment script on VPS\\n---")
        stdin, stdout, stderr = client.exec_command(script, timeout=120)
        
        out = stdout.read().decode('utf-8', 'ignore').strip()
        print(out.encode('ascii', 'ignore').decode('ascii'))
            
        err = stderr.read().decode('utf-8', 'ignore').strip()
        if err:
            print("ERRORS/WARNINGS:\\n", err.encode('ascii', 'ignore').decode('ascii'))
            
        print("---")
        print("Deployment completed successfully!")
            
    except Exception as e:
        print("Exception during deployment:", e)
    finally:
        client.close()

if __name__ == "__main__":
    deploy()
