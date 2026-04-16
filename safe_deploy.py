import os
import shutil
import subprocess
import paramiko

def run_cmd(cmd):
    print(f"Running: {cmd}")
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.stdout:
        print(f"stdout: {res.stdout}")
    if res.stderr:
        print(f"stderr: {res.stderr}")
    return res.returncode

def main():
    fb_cookie_orig = "fb_downloader/cookies.txt"
    yt_cookie_orig = "yt_d/cookies.txt"
    fb_cookie_temp = "temp_fb_cookies.txt"
    yt_cookie_temp = "temp_yt_cookies.txt"

    # 1. Backup cookies
    print("Backing up cookies...")
    if os.path.exists(fb_cookie_orig):
        shutil.copy2(fb_cookie_orig, fb_cookie_temp)
    if os.path.exists(yt_cookie_orig):
        shutil.copy2(yt_cookie_orig, yt_cookie_temp)

    # 2. Git operations
    print("Rewriting git history to exclude cookies...")
    run_cmd("git reset --soft origin/main")
    
    # Restore dummy cookies from origin/main to both working tree and index
    run_cmd(f"git checkout origin/main -- {fb_cookie_orig} {yt_cookie_orig}")
    run_cmd(f"git add {fb_cookie_orig} {yt_cookie_orig}")

    # Add all other untracked/modified files (the actual frontend/code updates)
    run_cmd("git add .")
    run_cmd("git reset HEAD temp_fb_cookies.txt temp_yt_cookies.txt")
    
    # Commit and Push
    run_cmd('git commit -m "Update frontend and deploy latest code (secrets removed)"')
    code = run_cmd("git push -f origin main")
    
    if code != 0:
        print("Push failed!")
        # restore backups
        if os.path.exists(fb_cookie_temp):
            shutil.copy2(fb_cookie_temp, fb_cookie_orig)
        if os.path.exists(yt_cookie_temp):
            shutil.copy2(yt_cookie_temp, yt_cookie_orig)
        return

    # 3. VPS Deploy
    print("Deploying to VPS...")
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(hostname, port, username, password)
        print("Connected to VPS!")
        
        # 3.1 Fetch and reset on VPS
        cmd = "cd /root/FreeDownloader && git fetch origin && git reset --hard origin/main"
        stdin, stdout, stderr = client.exec_command(cmd)
        stdout.read()
        
        # 3.2 SFTP upload the actual cookies
        print("Uploading real cookies via SFTP...")
        sftp = client.open_sftp()
        if os.path.exists(fb_cookie_temp):
            sftp.put(fb_cookie_temp, "/root/FreeDownloader/fb_downloader/cookies.txt")
        if os.path.exists(yt_cookie_temp):
            sftp.put(yt_cookie_temp, "/root/FreeDownloader/yt_d/cookies.txt")
        sftp.close()

        # 3.3 Set up Free Store Nginx & Services
        print("Setting up Free Store configs...")
        fs_setup = [
            "cp /root/FreeDownloader/nginx/freestore-domains.conf /etc/nginx/sites-available/freestore-domains.conf",
            "ln -sf /etc/nginx/sites-available/freestore-domains.conf /etc/nginx/sites-enabled/",
            "nginx -t && systemctl reload nginx",
            "cd /root/FreeDownloader/backend && source venv/bin/activate && pip install -r requirements.txt",
            "cat << 'EOF' > /etc/systemd/system/freestore.service\n[Unit]\nDescription=Free Store Application (Flask)\nAfter=network.target\n\n[Service]\nUser=root\nWorkingDirectory=/root/FreeDownloader/freeStore\nEnvironment=\"PATH=/root/FreeDownloader/backend/venv/bin\"\nExecStart=/root/FreeDownloader/backend/venv/bin/gunicorn -w 2 -b 127.0.0.1:8010 app:app\nRestart=always\n\n[Install]\nWantedBy=multi-user.target\nEOF",
            "systemctl daemon-reload",
            "systemctl enable --now freestore"
        ]
        for scmd in fs_setup:
            client.exec_command(scmd).stdout.read()

        # 3.4 Restart services
        print("Restarting services on VPS...")
        restart_cmd = "systemctl restart fb.service yt.service free_d.service p_d.service tik_d.service insta.service freedownloader.service downloader-backend.service freestore.service"
        client.exec_command(restart_cmd).stdout.read()
        
        print("VPS DEPLOYMENT COMPLETE!")
        
    except Exception as e:
        print(f"Deployment error: {e}")
    finally:
        client.close()

    # 4. Restore local copies
    print("Restoring local cookies...")
    if os.path.exists(fb_cookie_temp):
        shutil.copy2(fb_cookie_temp, fb_cookie_orig)
        os.remove(fb_cookie_temp)
    if os.path.exists(yt_cookie_temp):
        shutil.copy2(yt_cookie_temp, yt_cookie_orig)
        os.remove(yt_cookie_temp)
    print("All done!")

if __name__ == "__main__":
    main()
