import paramiko
import time

def run_ssh_commands():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print("Connecting to VPS...")
        client.connect(hostname, port, username, password)
        print("Connected!")
        
        # We will run these commands in a single shell session to keep state (like cd)
        commands = [
            # 1. Pull code
            "cd /root/FreeDownloader && git fetch origin && git reset --hard origin/main",
            
            # 2. Install packages for p_d and free_d if any
            "cd /root/FreeDownloader/p_d && ../venv/bin/pip install -r requirements.txt || true",
            "cd /root/FreeDownloader/free_d && ../venv/bin/pip install -r requirements.txt || true",
            
            # 3. Setup free_d.service (Port 8008)
            '''cat << 'EOF' > /etc/systemd/system/free_d.service
[Unit]
Description=Free_D Frontend
After=network.target

[Service]
User=root
WorkingDirectory=/root/FreeDownloader/free_d
ExecStart=/root/FreeDownloader/venv/bin/gunicorn app:app -b 0.0.0.0:8008
Restart=always

[Install]
WantedBy=multi-user.target
EOF''',
            
            # 4. Setup p_d.service (Port 8009)
            '''cat << 'EOF' > /etc/systemd/system/p_d.service
[Unit]
Description=P_D Porn Downloader
After=network.target

[Service]
User=root
WorkingDirectory=/root/FreeDownloader/p_d
ExecStart=/root/FreeDownloader/venv/bin/gunicorn app:app -b 0.0.0.0:8009
Restart=always

[Install]
WantedBy=multi-user.target
EOF''',

            # 5. Reload systemd daemon
            "systemctl daemon-reload",
            
            # 6. Enable and start new services
            "systemctl enable free_d.service",
            "systemctl restart free_d.service",
            "systemctl enable p_d.service",
            "systemctl restart p_d.service",
            
            # 7. Setup Nginx logic
            # Instead of multiple files, we'll write the single domains out
            # Remove old Nginx confs
            "rm -f /etc/nginx/sites-enabled/admin.freedownloader.top",
            "rm -f /etc/nginx/sites-available/admin.freedownloader.top",
            "rm -f /etc/nginx/sites-enabled/p.freedownloader.top",
            "rm -f /etc/nginx/sites-available/p.freedownloader.top",
            "rm -f /etc/nginx/sites-enabled/freedownloader.top",
            
            # New admin config
            '''cat << 'EOF' > /etc/nginx/sites-available/admin.freedownloader.top
server {
    server_name admin.freedownloader.top;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }
    listen 80;
}
EOF''',

            # New free_d config
            '''cat << 'EOF' > /etc/nginx/sites-available/freedownloader.top
server {
    server_name freedownloader.top www.freedownloader.top;
    location / {
        proxy_pass http://127.0.0.1:8008;
        proxy_set_header Host $host;
    }
    listen 80;
}
EOF''',

            # New porn config
            '''cat << 'EOF' > /etc/nginx/sites-available/p.freedownloader.top
server {
    server_name p.freedownloader.top;
    location / {
        proxy_pass http://127.0.0.1:8009;
        proxy_set_header Host $host;
    }
    listen 80;
}
EOF''',

            # Update existing subdomains to listen to both full and short aliases if desired 
            # Or just update it via certbot later. For now, leave old ones alone or append short alias?
            # Wait, the Facebook, Insta configs are managed by certbot already.
            # I will modify them directly using sed to add the shorter aliases!
            "sed -i 's/server_name f.freedownloader.top;/server_name f.freedownloader.top f.freedownloader.top;/' /etc/nginx/sites-enabled/f.freedownloader.top || true",
            "sed -i 's/server_name i.freedownloader.top;/server_name i.freedownloader.top i.freedownloader.top;/' /etc/nginx/sites-enabled/i.freedownloader.top || true",
            "sed -i 's/server_name t.freedownloader.top;/server_name t.freedownloader.top t.freedownloader.top;/' /etc/nginx/sites-enabled/t.freedownloader.top || true",
            "sed -i 's/server_name y.freedownloader.top;/server_name y.freedownloader.top yt.freedownloader.top y.freedownloader.top;/' /etc/nginx/sites-enabled/y.freedownloader.top || true",

            # Create symlinks
            "ln -sf /etc/nginx/sites-available/admin.freedownloader.top /etc/nginx/sites-enabled/",
            "ln -sf /etc/nginx/sites-available/freedownloader.top /etc/nginx/sites-enabled/",
            "ln -sf /etc/nginx/sites-available/p.freedownloader.top /etc/nginx/sites-enabled/",
            
            # Restart Nginx
            "systemctl restart nginx",
            
        ]
        
        for cmd in commands:
            print(f"\\n>>> Running: {cmd[:100]}...")
            stdin, stdout, stderr = client.exec_command(cmd)
            status = stdout.channel.recv_exit_status()
            out = stdout.read().decode('utf-8').strip()
            err = stderr.read().decode('utf-8').strip()
            
            if out:
                print("OUT:", out.encode('ascii', 'replace').decode('ascii'))
            if err:
                print("ERR:", err.encode('ascii', 'replace').decode('ascii'))
            print(f"Status: {status}")
            
    except Exception as e:
        print("Exception:", e)
    finally:
        client.close()

if __name__ == "__main__":
    run_ssh_commands()
