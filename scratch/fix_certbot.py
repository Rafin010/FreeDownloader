import paramiko

hostname = "75.127.1.75"
port = 22
username = "root"
password = "OcjRMVUDAPyFWB8JuUAf"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname, port, username, password)

cmds = [
    # Fix the urllib3 issue breaking Certbot
    "python3 -m pip install urllib3==1.26.15 requests-toolbelt==0.10.1 chardet==4.0.0",
    
    # Retry Certbot
    "certbot --nginx -d f.freedownloader.top -d y.freedownloader.top -d i.freedownloader.top -d t.freedownloader.top -d p.freedownloader.top --non-interactive --agree-tos -m contact@freedownloader.top --redirect",
    
    # Restart Nginx
    "systemctl restart nginx",
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
