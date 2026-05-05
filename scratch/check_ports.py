import paramiko

hostname = "75.127.1.75"
port = 22
username = "root"
password = "OcjRMVUDAPyFWB8JuUAf"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname, port, username, password)

cmds = [
    "cat /etc/systemd/system/yt_d.service | grep ExecStart",
    "cat /etc/systemd/system/fb_downloader.service | grep ExecStart",
    "cat /etc/systemd/system/tik_d.service | grep ExecStart",
    "cat /etc/systemd/system/insta_d.service | grep ExecStart",
    "cat /etc/systemd/system/p_d.service | grep ExecStart",
]

for cmd in cmds:
    print(f"\n--- {cmd} ---")
    stdin, stdout, stderr = client.exec_command(cmd)
    # Using replace to avoid unicode errors
    print(stdout.read().decode('utf-8', errors='replace').strip())
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if err:
        print("STDERR:", err)

client.close()
