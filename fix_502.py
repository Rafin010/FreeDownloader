import paramiko

def fix_502_install_gevent():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print("Connecting to server...")
        client.connect(hostname, port, username, password)
        
        # Install gevent in the virtual environment
        install_cmd = """
        echo "Installing missing gevent module..."
        /root/FreeDownloader/venv/bin/pip install gevent
        
        echo "Restarting backend services..."
        systemctl restart fb.service insta.service tiktok.service yt.service p_d.service free_d.service freedownloader.service
        sleep 3
        systemctl restart nginx
        echo "Done!"
        """
        
        stdin, stdout, stderr = client.exec_command(install_cmd, timeout=120)
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
    fix_502_install_gevent()
