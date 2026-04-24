import paramiko

def emergency_fix():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, port, username, password)
        
        # Step 1: Restore old venv
        script1 = """
cd /root/FreeDownloader
# Restore old venv
mv venv_old_py38 venv 2>/dev/null || true
ls venv/bin/python 2>/dev/null && echo "VENV RESTORED" || echo "VENV NOT FOUND"
"""
        print("Step 1: Restoring old venv...")
        stdin, stdout, stderr = client.exec_command(script1, timeout=15)
        stdout.channel.recv_exit_status()
        print(stdout.read().decode('utf-8', 'replace').strip())

        # Step 2: Install Python 3.11 properly
        script2 = """
export DEBIAN_FRONTEND=noninteractive
apt-get install -y software-properties-common
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update -y
apt-get install -y python3.11 python3.11-venv python3.11-dev python3.11-distutils
python3.11 --version
"""
        print("\nStep 2: Installing Python 3.11...")
        stdin, stdout, stderr = client.exec_command(script2, timeout=180)
        exit_code = stdout.channel.recv_exit_status()
        out = stdout.read().decode('utf-8', 'replace').strip()
        print("EXIT:", exit_code)
        print("OUT:", out.encode('ascii', 'replace').decode('ascii')[-400:])

        # Step 3: Check if python3.11 exists now
        script3 = "which python3.11 && python3.11 --version || echo 'FAILED'"
        stdin, stdout, stderr = client.exec_command(script3, timeout=10)
        stdout.channel.recv_exit_status()
        result = stdout.read().decode('utf-8', 'replace').strip()
        print("\nPython 3.11 check:", result)

        if "FAILED" in result:
            # Python 3.11 couldn't install, just use old venv and restart
            print("\nPython 3.11 not available. Using old Python 3.8 venv...")
            script_restart = """
pkill gunicorn || true
sleep 2
systemctl restart fb.service insta.service tiktok.service yt.service free_d.service p_d.service freedownloader.service
sleep 2
systemctl is-active fb.service insta.service tiktok.service yt.service free_d.service p_d.service freedownloader.service
"""
            stdin, stdout, stderr = client.exec_command(script_restart, timeout=30)
            stdout.channel.recv_exit_status()
            print(stdout.read().decode('utf-8', 'replace').strip())
        else:
            # Python 3.11 available! Create new venv
            print("\nPython 3.11 available! Creating new venv...")
            script_venv = """
cd /root/FreeDownloader
mv venv venv_py38_backup || true
python3.11 -m venv venv
/root/FreeDownloader/venv/bin/pip install --upgrade pip
/root/FreeDownloader/venv/bin/pip install flask flask-cors gunicorn yt-dlp requests python-dotenv
/root/FreeDownloader/venv/bin/yt-dlp --version
/root/FreeDownloader/venv/bin/python --version
pkill gunicorn || true
sleep 2
systemctl restart fb.service insta.service tiktok.service yt.service free_d.service p_d.service freedownloader.service
sleep 2
systemctl is-active fb.service insta.service tiktok.service yt.service free_d.service p_d.service freedownloader.service
"""
            stdin, stdout, stderr = client.exec_command(script_venv, timeout=180)
            exit_code = stdout.channel.recv_exit_status()
            out = stdout.read().decode('utf-8', 'replace').strip()
            err = stderr.read().decode('utf-8', 'replace').strip()
            print("EXIT:", exit_code)
            print("OUT:", out.encode('ascii', 'replace').decode('ascii')[-1500:])

        print("\nDone!")
            
    except Exception as e:
        print("Exception:", e)
    finally:
        client.close()

if __name__ == "__main__":
    emergency_fix()
