import paramiko

hostname = "75.127.1.75"
port = 22
username = "root"
password = "OcjRMVUDAPyFWB8JuUAf"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname, port, username, password)

cmds = [
    # Fix the proxy_pass ports
    "sed -i 's/127.0.0.1:8001;/127.0.0.1:8004;/' /etc/nginx/sites-available/y.freedownloader.top",
    "sed -i 's/127.0.0.1:8002;/127.0.0.1:8001;/' /etc/nginx/sites-available/f.freedownloader.top",
    "sed -i 's/127.0.0.1:8004;/127.0.0.1:8002;/' /etc/nginx/sites-available/i.freedownloader.top",
    "sed -i 's/127.0.0.1:8005;/127.0.0.1:8009;/' /etc/nginx/sites-available/p.freedownloader.top",
    
    # Add X-Forwarded-Proto header to all 5 configs
    "sed -i 's/proxy_set_header X-Real-IP $remote_addr;/proxy_set_header X-Real-IP $remote_addr; proxy_set_header X-Forwarded-Proto $scheme; proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;/' /etc/nginx/sites-available/y.freedownloader.top",
    "sed -i 's/proxy_set_header X-Real-IP $remote_addr;/proxy_set_header X-Real-IP $remote_addr; proxy_set_header X-Forwarded-Proto $scheme; proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;/' /etc/nginx/sites-available/f.freedownloader.top",
    "sed -i 's/proxy_set_header X-Real-IP $remote_addr;/proxy_set_header X-Real-IP $remote_addr; proxy_set_header X-Forwarded-Proto $scheme; proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;/' /etc/nginx/sites-available/i.freedownloader.top",
    "sed -i 's/proxy_set_header X-Real-IP $remote_addr;/proxy_set_header X-Real-IP $remote_addr; proxy_set_header X-Forwarded-Proto $scheme; proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;/' /etc/nginx/sites-available/t.freedownloader.top",
    "sed -i 's/proxy_set_header X-Real-IP $remote_addr;/proxy_set_header X-Real-IP $remote_addr; proxy_set_header X-Forwarded-Proto $scheme; proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;/' /etc/nginx/sites-available/p.freedownloader.top",
    
    # Reload Nginx
    "nginx -t && systemctl reload nginx",
]

for cmd in cmds:
    print(f"Running: {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    print("STDOUT:", stdout.read().decode('utf-8'))
    err = stderr.read().decode('utf-8')
    if err:
        print("STDERR:", err)

client.close()
