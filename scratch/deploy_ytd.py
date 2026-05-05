import os
import subprocess
import paramiko

# 1. Commit and push local changes
print("Committing local changes...")
subprocess.run(['git', 'add', 'yt_d/app.py', 'yt_d/templates/index.html'], cwd=r'e:\_free downloader Projext')
subprocess.run(['git', 'commit', '-m', 'Update yt_d: Add GeoIP, Infinite Scroll, Dark Mode UI'], cwd=r'e:\_free downloader Projext')
subprocess.run(['git', 'push', 'origin', 'main'], cwd=r'e:\_free downloader Projext')

# 2. SSH to VPS and deploy
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
    "systemctl restart yt yt_d || true",
    "systemctl restart freedownloader"
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
print("Deployment complete.")
