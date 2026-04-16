import paramiko
import os

VPS_IP = '75.127.1.75'
VPS_USER = 'root'
VPS_PASS = '1h_5$6$O771@mK7y9L?6!s_T'

print("=== STARTING FREE STORE PRODUCTION DEPLOYMENT ===")

# Commands to run on the VPS
commands = [
    # 1. Configure Nginx Domains
    "echo 'Deploying Nginx Configs...'",
    "cp /root/FreeDownloader/nginx/freestore-domains.conf /etc/nginx/sites-available/freestore-domains.conf",
    "ln -sf /etc/nginx/sites-available/freestore-domains.conf /etc/nginx/sites-enabled/",
    
    # Reload nginx to verify config
    "nginx -t && systemctl reload nginx",

    # 2. Install Python deps for backend (APScheduler added)
    "echo 'Installing backend dependencies...'",
    "cd /root/FreeDownloader/backend && source venv/bin/activate && pip install -r requirements.txt",
    
    # 3. Create Free Store service
    "echo 'Setting up Free Store Service on port 8010...'",
    """cat << 'EOF' > /etc/systemd/system/freestore.service
[Unit]
Description=Free Store Application (Flask)
After=network.target

[Service]
User=root
WorkingDirectory=/root/FreeDownloader/freeStore
Environment="PATH=/root/FreeDownloader/backend/venv/bin"
ExecStart=/root/FreeDownloader/backend/venv/bin/gunicorn -w 2 -b 127.0.0.1:8010 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF""",
    
    # 4. Reload Systemd and Restart everything
    "echo 'Restarting Services...'",
    "systemctl daemon-reload",
    "systemctl enable --now freestore",
    "systemctl restart freestore",
    "systemctl restart downloader-backend",  # Admin panel
    "systemctl restart free_d",             # Old landing page component on 8008

    # 5. SSL / Certbot (Optional step string to request SSL for web.freedownloader.top)
    "echo 'IMPORTANT: You may need to run this manually to get SSL: certbot --nginx -d freedownloader.top -d www.freedownloader.top -d web.freedownloader.top'",
]

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS)
    for cmd in commands:
        print(f"\n> Running: {cmd}")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        
        # Wait for command to finish
        exit_status = stdout.channel.recv_exit_status()
        
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        
        if out: print(out)
        if err: print(f"ERROR: {err}")
        
except Exception as e:
    print(f"Deployment failed: {e}")
finally:
    ssh.close()

print("\n=== DEPLOYMENT COMPLETED ===")
