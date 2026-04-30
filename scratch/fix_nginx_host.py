import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('75.127.1.75', 22, 'root', 'OcjRMVUDAPyFWB8JuUAf')

fix = (
    "for f in /etc/nginx/sites-available/facebook.freedownloader.top "
    "/etc/nginx/sites-available/youtube.freedownloader.top "
    "/etc/nginx/sites-available/instagram.freedownloader.top "
    "/etc/nginx/sites-available/tiktok.freedownloader.top "
    "/etc/nginx/sites-available/porn.freedownloader.top; do "
    "sed -i 's/Host System.Management.Automation.Internal.Host.InternalHost/Host \\$host/g' $f; "
    "done; "
    "nginx -t && systemctl reload nginx && echo FIXED"
)

stdin, stdout, stderr = client.exec_command(fix, timeout=15)
stdout.channel.recv_exit_status()
print(stdout.read().decode())
print(stderr.read().decode())
client.close()
