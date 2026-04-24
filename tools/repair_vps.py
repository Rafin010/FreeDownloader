import paramiko

def fix_server():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, port, username, password)
        
        # We will use python over SSH to rewrite the /etc/nginx/sites-available/freedownloader file.
        # But wait, it's easier to just recreate the configs from scratch and re-run certbot.
        # It's safest because they want new subdomains!
        
        script = """
# 1. Clean up old conflicting config
rm -f /etc/nginx/sites-enabled/freedownloader
rm -f /etc/nginx/sites-available/freedownloader
rm -f /etc/nginx/sites-enabled/freedownloader.top
rm -f /etc/nginx/sites-available/freedownloader.top

# 2. Write new configs for ALL subdomains separately for cleanliness

cat << 'EOF' > /etc/nginx/sites-available/freedownloader.top
server {
    server_name freedownloader.top www.freedownloader.top;
    location / { proxy_pass http://127.0.0.1:8008; proxy_set_header Host $host; }
    listen 80;
}
EOF

cat << 'EOF' > /etc/nginx/sites-available/admin.freedownloader.top
server {
    server_name admin.freedownloader.top;
    location / { proxy_pass http://127.0.0.1:8000; proxy_set_header Host $host; }
    listen 80;
}
EOF

cat << 'EOF' > /etc/nginx/sites-available/porn.freedownloader.top
server {
    server_name porn.freedownloader.top;
    location / { proxy_pass http://127.0.0.1:8009; proxy_set_header Host $host; }
    listen 80;
}
EOF

cat << 'EOF' > /etc/nginx/sites-available/facebook.freedownloader.top
server {
    server_name facebook.freedownloader.top f.freedownloader.top;
    location / { proxy_pass http://127.0.0.1:8001; proxy_set_header Host $host; }
    listen 80;
}
EOF

cat << 'EOF' > /etc/nginx/sites-available/instagram.freedownloader.top
server {
    server_name instagram.freedownloader.top i.freedownloader.top;
    location / { proxy_pass http://127.0.0.1:8002; proxy_set_header Host $host; }
    listen 80;
}
EOF

cat << 'EOF' > /etc/nginx/sites-available/tiktok.freedownloader.top
server {
    server_name tiktok.freedownloader.top t.freedownloader.top;
    location / { proxy_pass http://127.0.0.1:8003; proxy_set_header Host $host; }
    listen 80;
}
EOF

cat << 'EOF' > /etc/nginx/sites-available/youtube.freedownloader.top
server {
    server_name youtube.freedownloader.top yt.freedownloader.top y.freedownloader.top;
    location / { proxy_pass http://127.0.0.1:8004; proxy_set_header Host $host; }
    listen 80;
}
EOF

# Remove all from sites-enabled
rm -f /etc/nginx/sites-enabled/*

# Link them explicitly
ln -sf /etc/nginx/sites-available/freedownloader.top /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/admin.freedownloader.top /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/porn.freedownloader.top /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/facebook.freedownloader.top /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/instagram.freedownloader.top /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/tiktok.freedownloader.top /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/youtube.freedownloader.top /etc/nginx/sites-enabled/


# 3. Reload Nginx
systemctl restart nginx

# 4. Restart gunicorns
systemctl restart freedownloader.service
systemctl restart fb.service
systemctl restart insta.service
systemctl restart tiktok.service
# Wait, youtube service is yt_d? Let's restart all python
pkill gunicorn || true
systemctl restart fb.service insta.service tiktok.service freedownloader.service free_d.service p_d.service

# 5. Run Certbot for ALL domains to ensure SSL is perfectly aligned!
certbot --nginx -d freedownloader.top -d www.freedownloader.top -d admin.freedownloader.top -d porn.freedownloader.top -d facebook.freedownloader.top -d f.freedownloader.top -d instagram.freedownloader.top -d i.freedownloader.top -d tiktok.freedownloader.top -d t.freedownloader.top -d youtube.freedownloader.top -d yt.freedownloader.top -d y.freedownloader.top --non-interactive --agree-tos -m admin@freedownloader.top --expand
"""
        stdin, stdout, stderr = client.exec_command(script)
        stdout.channel.recv_exit_status()
        out = stdout.read().decode('utf-8', 'replace').strip()
        err = stderr.read().decode('utf-8', 'replace').strip()
        print("OUT:", out.encode('ascii', 'replace').decode('ascii'))
        print("ERR:", err.encode('ascii', 'replace').decode('ascii'))
            
    except Exception as e:
        print("Exception:", e)
    finally:
        client.close()

if __name__ == "__main__":
    fix_server()
