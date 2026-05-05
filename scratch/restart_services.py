import paramiko

hostname = "75.127.1.75"
port = 22
username = "root"
password = "OcjRMVUDAPyFWB8JuUAf"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname, port, username, password)

cmds = [
    "systemctl restart yt_d fb_downloader tik_d insta_d p_d --no-pager || true",
    "systemctl restart fb insta tiktok yt p_d", # using correct service names
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
