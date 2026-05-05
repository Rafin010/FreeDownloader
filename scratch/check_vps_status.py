import paramiko

hostname = "75.127.1.75"
port = 22
username = "root"
password = "OcjRMVUDAPyFWB8JuUAf"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname, port, username, password)

cmds = [
    "cat /etc/nginx/sites-enabled/f.freedownloader.top",
    "cat /etc/nginx/sites-enabled/y.freedownloader.top",
    "systemctl status yt_d fb_downloader tik_d insta_d p_d --no-pager",
]

for cmd in cmds:
    print(f"\n--- {cmd} ---")
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode('utf-8'))
    err = stderr.read().decode('utf-8')
    if err:
        print("STDERR:", err)

client.close()
