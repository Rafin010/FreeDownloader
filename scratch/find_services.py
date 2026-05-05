import paramiko
import re

hostname = "75.127.1.75"
port = 22
username = "root"
password = "OcjRMVUDAPyFWB8JuUAf"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname, port, username, password)

print("Listing all systemd services that look like our downloaders...")
stdin, stdout, stderr = client.exec_command("ls /etc/systemd/system/*.service")
services = stdout.read().decode('utf-8').splitlines()

for s in services:
    if "freedownloader" in s.lower() or "free" in s.lower() or "_d" in s.lower() or "fb" in s.lower() or "yt" in s.lower() or "tik" in s.lower() or "insta" in s.lower():
        stdin, stdout, stderr = client.exec_command(f"cat {s} | grep ExecStart")
        exec_start = stdout.read().decode('utf-8').strip()
        print(f"{s.split('/')[-1]}: {exec_start}")

client.close()
