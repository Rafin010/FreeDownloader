import paramiko

hostname = "75.127.1.75"
port = 22
username = "root"
password = "OcjRMVUDAPyFWB8JuUAf"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname, port, username, password)

cmds = [
    "cd /root/FreeDownloader && git fetch origin && git reset --hard origin/main",
    "systemctl restart yt",
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
print("Done!")
