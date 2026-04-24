import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('75.127.1.75', 22, 'root', 'OcjRMVUDAPyFWB8JuUAf')
stdin, stdout, stderr = client.exec_command('systemctl list-units --type=service | grep -E "yt|fb|free|porn|tiktok|insta|d.service"')
print("OUT:", stdout.read().decode())
print("ERR:", stderr.read().decode())
client.close()
