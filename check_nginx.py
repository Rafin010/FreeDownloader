import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('75.127.1.75', 22, 'root', 'OcjRMVUDAPyFWB8JuUAf')

cmds = [
    "source /root/FreeDownloader/venv/bin/activate && pip install python-dotenv requests stripe flask-cors 2>&1 | tail -3",
    "cp /root/FreeDownloader/nginx/freestore-domains.conf /etc/nginx/sites-available/freestore-domains.conf",
    "ln -sf /etc/nginx/sites-available/freestore-domains.conf /etc/nginx/sites-enabled/",
    "nginx -t && systemctl reload nginx",
    """cat << 'EOF' > /etc/systemd/system/donate.service
[Unit]
Description=Donate Payment Microservice
After=network.target

[Service]
User=root
WorkingDirectory=/root/FreeDownloader/Donate
Environment="PATH=/root/FreeDownloader/venv/bin"
ExecStart=/root/FreeDownloader/venv/bin/gunicorn -w 2 -b 127.0.0.1:5007 app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF""",
    "systemctl daemon-reload",
    "systemctl enable donate",
    "systemctl restart donate freedownloader",
    "sleep 2 && systemctl is-active donate",
]

for cmd in cmds:
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out:
        try:
            print(out)
        except:
            print(out.encode('ascii', 'replace').decode())
    if err:
        try:
            print(f"stderr: {err}")
        except:
            print("stderr: (encoding error)")

print("\n=== SERVER COMMANDS COMPLETE ===")
client.close()
