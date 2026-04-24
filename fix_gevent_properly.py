import paramiko

def fix_gevent_properly():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print("Connecting to server...")
        client.connect(hostname, port, username, password)
        
        # Install build dependencies, gevent, and restart
        install_cmd = """
        echo "Installing build dependencies..."
        export DEBIAN_FRONTEND=noninteractive
        apt-get update -y
        apt-get install -y python3.9-dev build-essential gcc
        
        echo "Installing gevent in the virtual environment..."
        /root/FreeDownloader/venv/bin/pip install --upgrade pip
        /root/FreeDownloader/venv/bin/pip install gevent wheel
        
        echo "Restarting backend services..."
        systemctl daemon-reload
        systemctl reset-failed
        systemctl restart fb.service insta.service tiktok.service yt.service free_d.service p_d.service freedownloader.service
        sleep 5
        systemctl is-active fb.service insta.service tiktok.service yt.service
        systemctl restart nginx
        echo "All Done!"
        """
        
        stdin, stdout, stderr = client.exec_command(install_cmd, timeout=300)
        
        # We read lines as they come to avoid freezing on charmap issues
        for line in stdout:
            print("OUT:", line.strip())
            
        err = stderr.read().decode('utf-8', 'replace').strip()
        if err:
            print("ERR:\n", err)
            
    except Exception as e:
        print("Exception:", e)
    finally:
        client.close()

if __name__ == "__main__":
    fix_gevent_properly()
