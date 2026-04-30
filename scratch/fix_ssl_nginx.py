import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('75.127.1.75', 22, 'root', 'OcjRMVUDAPyFWB8JuUAf')

# All domains need SSL with the shared wildcard cert
configs = {
    'facebook.freedownloader.top': {
        'server_name': 'facebook.freedownloader.top f.freedownloader.top',
        'port': 8001
    },
    'instagram.freedownloader.top': {
        'server_name': 'instagram.freedownloader.top i.freedownloader.top',
        'port': 8002
    },
    'tiktok.freedownloader.top': {
        'server_name': 'tiktok.freedownloader.top t.freedownloader.top',
        'port': 8003
    },
    'youtube.freedownloader.top': {
        'server_name': 'youtube.freedownloader.top yt.freedownloader.top y.freedownloader.top',
        'port': 8004
    },
    'porn.freedownloader.top': {
        'server_name': 'porn.freedownloader.top sex.freedownloader.top p.freedownloader.top',
        'port': 8009
    },
}

for filename, cfg in configs.items():
    conf = f"""server {{
    listen 80;
    listen 443 ssl;
    server_name {cfg['server_name']};

    ssl_certificate /etc/letsencrypt/live/freedownloader.top/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/freedownloader.top/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {{
        proxy_pass http://127.0.0.1:{cfg['port']};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""
    # Write config via heredoc
    escaped = conf.replace("'", "'\\''")
    cmd = f"echo '{escaped}' > /etc/nginx/sites-available/{filename}"
    stdin, stdout, stderr = client.exec_command(cmd, timeout=10)
    stdout.channel.recv_exit_status()
    print(f"Wrote: {filename} -> port {cfg['port']}")

# Test and reload nginx
stdin, stdout, stderr = client.exec_command('nginx -t && systemctl reload nginx && echo SUCCESS', timeout=15)
stdout.channel.recv_exit_status()
print(stdout.read().decode())
print(stderr.read().decode())

client.close()
print("DONE!")
