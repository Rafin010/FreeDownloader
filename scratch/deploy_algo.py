import os
import subprocess
import paramiko

print("Committing local changes...")
subprocess.run(['git', 'add', '-A'], cwd=r'e:\_free downloader Projext')
subprocess.run(['git', 'commit', '-m', 'Fix yt_d infinite scroll UI, instant scroll, and add User Algorithm'], cwd=r'e:\_free downloader Projext')
subprocess.run(['git', 'push', 'origin', 'main'], cwd=r'e:\_free downloader Projext')

print("Deploying to VPS...")
hostname = "75.127.1.75"
port = 22
username = "root"
password = "OcjRMVUDAPyFWB8JuUAf"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname, port, username, password)

cmds = [
    "cd /root/FreeDownloader && git fetch origin && git reset --hard origin/main",
    "systemctl restart yt"
]

for cmd in cmds:
    print(f"Running: {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    print("STDOUT:", stdout.read().decode('utf-8'))
    err = stderr.read().decode('utf-8')
    if err:
        print("STDERR:", err)

client.close()
print("Deployment complete.")
