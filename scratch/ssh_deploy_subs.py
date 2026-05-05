import paramiko

hostname = "75.127.1.75"
port = 22
username = "root"
password = "OcjRMVUDAPyFWB8JuUAf"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname, port, username, password)

cmds = [
    # Pull latest code
    "cd /root/FreeDownloader && git fetch origin && git reset --hard origin/main",
    
    # Remove old Nginx configurations
    "rm -f /etc/nginx/sites-enabled/facebook.freedownloader.top",
    "rm -f /etc/nginx/sites-available/facebook.freedownloader.top",
    "rm -f /etc/nginx/sites-enabled/youtube.freedownloader.top",
    "rm -f /etc/nginx/sites-available/youtube.freedownloader.top",
    "rm -f /etc/nginx/sites-enabled/instagram.freedownloader.top",
    "rm -f /etc/nginx/sites-available/instagram.freedownloader.top",
    "rm -f /etc/nginx/sites-enabled/tiktok.freedownloader.top",
    "rm -f /etc/nginx/sites-available/tiktok.freedownloader.top",
    "rm -f /etc/nginx/sites-enabled/porn.freedownloader.top",
    "rm -f /etc/nginx/sites-available/porn.freedownloader.top",
    
    # Setup new configs
    '''cat << 'EOF' > /etc/nginx/sites-available/f.freedownloader.top
server {
    server_name f.freedownloader.top;
    location / { proxy_pass http://127.0.0.1:8002; proxy_set_header Host $host; proxy_set_header X-Real-IP $remote_addr; }
    listen 80;
}
EOF''',

    '''cat << 'EOF' > /etc/nginx/sites-available/y.freedownloader.top
server {
    server_name y.freedownloader.top;
    location / { proxy_pass http://127.0.0.1:8001; proxy_set_header Host $host; proxy_set_header X-Real-IP $remote_addr; }
    listen 80;
}
EOF''',

    '''cat << 'EOF' > /etc/nginx/sites-available/i.freedownloader.top
server {
    server_name i.freedownloader.top;
    location / { proxy_pass http://127.0.0.1:8004; proxy_set_header Host $host; proxy_set_header X-Real-IP $remote_addr; }
    listen 80;
}
EOF''',

    '''cat << 'EOF' > /etc/nginx/sites-available/t.freedownloader.top
server {
    server_name t.freedownloader.top;
    location / { proxy_pass http://127.0.0.1:8003; proxy_set_header Host $host; proxy_set_header X-Real-IP $remote_addr; }
    listen 80;
}
EOF''',

    '''cat << 'EOF' > /etc/nginx/sites-available/p.freedownloader.top
server {
    server_name p.freedownloader.top;
    location / { proxy_pass http://127.0.0.1:8005; proxy_set_header Host $host; proxy_set_header X-Real-IP $remote_addr; }
    listen 80;
}
EOF''',

    # Enable new configs
    "ln -sf /etc/nginx/sites-available/f.freedownloader.top /etc/nginx/sites-enabled/",
    "ln -sf /etc/nginx/sites-available/y.freedownloader.top /etc/nginx/sites-enabled/",
    "ln -sf /etc/nginx/sites-available/i.freedownloader.top /etc/nginx/sites-enabled/",
    "ln -sf /etc/nginx/sites-available/t.freedownloader.top /etc/nginx/sites-enabled/",
    "ln -sf /etc/nginx/sites-available/p.freedownloader.top /etc/nginx/sites-enabled/",
    
    # Reload Nginx
    "nginx -t && systemctl reload nginx",
    
    # Run Certbot for the new domains
    "certbot --nginx -d f.freedownloader.top -d y.freedownloader.top -d i.freedownloader.top -d t.freedownloader.top -d p.freedownloader.top --non-interactive --agree-tos -m contact@freedownloader.top --redirect"
]

for cmd in cmds:
    print(f"Running: {cmd[:50]}...")
    stdin, stdout, stderr = client.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    print("STDOUT:", stdout.read().decode('utf-8'))
    err = stderr.read().decode('utf-8')
    if err:
        print("STDERR:", err)

client.close()
