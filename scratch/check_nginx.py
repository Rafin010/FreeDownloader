import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('75.127.1.75', username='root', password='OcjRMVUDAPyFWB8JuUAf')

stdin, stdout, stderr = client.exec_command('grep -rn "freedownloader.top" /etc/nginx/sites-enabled/')
print("== MATCHES IN SITES-ENABLED ==")
print(stdout.read().decode('utf-8'))
