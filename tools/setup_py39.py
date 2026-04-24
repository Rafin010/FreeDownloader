import paramiko

def setup_py39():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, port, username, password)

        # Create new venv with Python 3.9 and install latest yt-dlp
        script = """
cd /root/FreeDownloader

# Backup the old venv
mv venv venv_py38_backup 2>/dev/null || true

# Create new venv with Python 3.9
python3.9 -m venv venv

# Upgrade pip
/root/FreeDownloader/venv/bin/pip install --upgrade pip 2>&1 | tail -1

# Install all required packages
/root/FreeDownloader/venv/bin/pip install flask flask-cors gunicorn yt-dlp requests python-dotenv 2>&1 | tail -3

# Verify versions
echo "=== VERSIONS ==="
/root/FreeDownloader/venv/bin/python --version
/root/FreeDownloader/venv/bin/yt-dlp --version

# Test Facebook
echo "=== TESTING FACEBOOK ==="
/root/FreeDownloader/venv/bin/yt-dlp --dump-json --no-warnings "https://www.facebook.com/share/v/18THtMvMsG/" 2>&1 | head -1

# Test YouTube
echo "=== TESTING YOUTUBE ==="
/root/FreeDownloader/venv/bin/yt-dlp --dump-json --no-warnings "https://www.youtube.com/watch?v=dQw4w9WgXcQ" 2>&1 | head -1

# Restart services
pkill gunicorn || true
sleep 2
systemctl restart fb.service insta.service tiktok.service yt.service free_d.service p_d.service freedownloader.service
sleep 2
echo "=== SERVICE STATUS ==="
systemctl is-active fb.service insta.service tiktok.service yt.service free_d.service p_d.service freedownloader.service
"""
        print("Setting up Python 3.9 + latest yt-dlp (this will take a minute)...")
        stdin, stdout, stderr = client.exec_command(script, timeout=180)
        exit_code = stdout.channel.recv_exit_status()
        out = stdout.read().decode('utf-8', 'replace').strip()
        err = stderr.read().decode('utf-8', 'replace').strip()
        print("EXIT:", exit_code)
        print("OUT:", out.encode('ascii', 'replace').decode('ascii')[-3000:])
        if err:
            print("ERR:", err.encode('ascii', 'replace').decode('ascii')[-500:])
        print("\nDone!")
        
    except Exception as e:
        print("Exception:", e)
    finally:
        client.close()

if __name__ == "__main__":
    setup_py39()
