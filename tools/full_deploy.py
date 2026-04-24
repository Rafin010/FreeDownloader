import paramiko

def full_deploy():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, port, username, password)
        
        script = """
# 1. Pull latest code
cd /root/FreeDownloader && git fetch origin && git reset --hard origin/main

# 2. Update yt-dlp to latest version (CRITICAL for anti-bot bypass)
/root/FreeDownloader/venv/bin/pip install --upgrade yt-dlp

# 3. Create YouTube systemd service if it doesn't exist
cat << 'EOF' > /etc/systemd/system/yt.service
[Unit]
Description=YouTube Downloader
After=network.target

[Service]
User=root
WorkingDirectory=/root/FreeDownloader/yt_d
ExecStart=/root/FreeDownloader/venv/bin/gunicorn app:app -b 0.0.0.0:8004 --timeout 300 --workers 2
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 4. Update existing services with increased timeout for large video downloads
cat << 'EOF' > /etc/systemd/system/fb.service
[Unit]
Description=Facebook Downloader
After=network.target

[Service]
User=root
WorkingDirectory=/root/FreeDownloader/fb_downloader
ExecStart=/root/FreeDownloader/venv/bin/gunicorn app:app -b 0.0.0.0:8001 --timeout 300 --workers 2
Restart=always

[Install]
WantedBy=multi-user.target
EOF

cat << 'EOF' > /etc/systemd/system/insta.service
[Unit]
Description=Instagram Downloader
After=network.target

[Service]
User=root
WorkingDirectory=/root/FreeDownloader/insta_d
ExecStart=/root/FreeDownloader/venv/bin/gunicorn app:app -b 0.0.0.0:8002 --timeout 300 --workers 2
Restart=always

[Install]
WantedBy=multi-user.target
EOF

cat << 'EOF' > /etc/systemd/system/tiktok.service
[Unit]
Description=TikTok Downloader
After=network.target

[Service]
User=root
WorkingDirectory=/root/FreeDownloader/tik_d
ExecStart=/root/FreeDownloader/venv/bin/gunicorn app:app -b 0.0.0.0:8003 --timeout 300 --workers 2
Restart=always

[Install]
WantedBy=multi-user.target
EOF

cat << 'EOF' > /etc/systemd/system/freedownloader.service
[Unit]
Description=FreeDownloader Backend (Admin)
After=network.target

[Service]
User=root
WorkingDirectory=/root/FreeDownloader/backend
ExecStart=/root/FreeDownloader/venv/bin/gunicorn app:app -b 0.0.0.0:8000 --timeout 300 --workers 2
Restart=always

[Install]
WantedBy=multi-user.target
EOF

cat << 'EOF' > /etc/systemd/system/free_d.service
[Unit]
Description=Free_D Frontend
After=network.target

[Service]
User=root
WorkingDirectory=/root/FreeDownloader/free_d
ExecStart=/root/FreeDownloader/venv/bin/gunicorn app:app -b 0.0.0.0:8008 --timeout 300 --workers 2
Restart=always

[Install]
WantedBy=multi-user.target
EOF

cat << 'EOF' > /etc/systemd/system/p_d.service
[Unit]
Description=P_D Downloader
After=network.target

[Service]
User=root
WorkingDirectory=/root/FreeDownloader/p_d
ExecStart=/root/FreeDownloader/venv/bin/gunicorn app:app -b 0.0.0.0:8009 --timeout 300 --workers 2
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 5. Reload systemd and restart all services
systemctl daemon-reload
pkill gunicorn || true
sleep 2
systemctl enable yt.service
systemctl restart freedownloader.service fb.service insta.service tiktok.service yt.service free_d.service p_d.service
sleep 2

# 6. Check status
systemctl is-active freedownloader.service fb.service insta.service tiktok.service yt.service free_d.service p_d.service

# 7. Confirm yt-dlp version
/root/FreeDownloader/venv/bin/yt-dlp --version
"""
        
        print("Deploying to VPS...")
        stdin, stdout, stderr = client.exec_command(script, timeout=120)
        stdout.channel.recv_exit_status()
        out = stdout.read().decode('utf-8', 'replace').strip()
        err = stderr.read().decode('utf-8', 'replace').strip()
        print("OUT:", out.encode('ascii', 'replace').decode('ascii'))
        print("ERR:", err.encode('ascii', 'replace').decode('ascii'))
        print("Done!")
            
    except Exception as e:
        print("Exception:", e)
    finally:
        client.close()

if __name__ == "__main__":
    full_deploy()
