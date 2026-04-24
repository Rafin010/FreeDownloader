import paramiko

def upgrade_server():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, port, username, password)
        
        # Step 1: Install Python 3.11 from deadsnakes PPA
        script1 = """
apt-get update -y
add-apt-repository ppa:deadsnakes/ppa -y
apt-get update -y
apt-get install -y python3.11 python3.11-venv python3.11-dev
python3.11 --version
"""
        print("Step 1: Installing Python 3.11...")
        stdin, stdout, stderr = client.exec_command(script1, timeout=120)
        exit_code = stdout.channel.recv_exit_status()
        out = stdout.read().decode('utf-8', 'replace').strip()
        err = stderr.read().decode('utf-8', 'replace').strip()
        print("EXIT:", exit_code)
        # Only print last portion
        print("OUT:", out.encode('ascii', 'replace').decode('ascii')[-500:])

        # Step 2: Create new venv with Python 3.11
        script2 = """
cd /root/FreeDownloader
# Backup old venv
mv venv venv_old_py38 2>/dev/null || true
# Create new venv with Python 3.11
python3.11 -m venv venv
# Install all requirements
source venv/bin/activate
pip install --upgrade pip
pip install flask flask-cors gunicorn yt-dlp requests python-dotenv
pip install yt-dlp --upgrade
yt-dlp --version
python --version
deactivate
"""
        print("\nStep 2: Creating new venv with Python 3.11...")
        stdin, stdout, stderr = client.exec_command(script2, timeout=180)
        exit_code = stdout.channel.recv_exit_status()
        out = stdout.read().decode('utf-8', 'replace').strip()
        err = stderr.read().decode('utf-8', 'replace').strip()
        print("EXIT:", exit_code)
        print("OUT:", out.encode('ascii', 'replace').decode('ascii')[-800:])
        if err:
            print("ERR:", err.encode('ascii', 'replace').decode('ascii')[-500:])

        # Step 3: Test Facebook download with new yt-dlp
        script3 = """
/root/FreeDownloader/venv/bin/yt-dlp --version
/root/FreeDownloader/venv/bin/python --version
/root/FreeDownloader/venv/bin/yt-dlp --dump-json --no-warnings "https://www.facebook.com/share/v/18THtMvMsG/" 2>&1 | head -2
"""
        print("\nStep 3: Testing Facebook with new yt-dlp...")
        stdin, stdout, stderr = client.exec_command(script3, timeout=60)
        exit_code = stdout.channel.recv_exit_status()
        out = stdout.read().decode('utf-8', 'replace').strip()
        err = stderr.read().decode('utf-8', 'replace').strip()
        print("EXIT:", exit_code)
        print("OUT:", out.encode('ascii', 'replace').decode('ascii')[-1000:])
        if err:
            print("ERR:", err.encode('ascii', 'replace').decode('ascii')[-500:])

        # Step 4: Restart all services
        script4 = """
pkill gunicorn || true
sleep 2
systemctl restart fb.service insta.service tiktok.service yt.service free_d.service p_d.service freedownloader.service
sleep 2
systemctl is-active fb.service insta.service tiktok.service yt.service free_d.service p_d.service freedownloader.service
"""
        print("\nStep 4: Restarting services...")
        stdin, stdout, stderr = client.exec_command(script4, timeout=30)
        exit_code = stdout.channel.recv_exit_status()
        out = stdout.read().decode('utf-8', 'replace').strip()
        print("OUT:", out.encode('ascii', 'replace').decode('ascii'))
        print("\nDone!")
            
    except Exception as e:
        print("Exception:", e)
    finally:
        client.close()

if __name__ == "__main__":
    upgrade_server()
