import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('75.127.1.75', 22, 'root', 'OcjRMVUDAPyFWB8JuUAf')
stdin, stdout, stderr = client.exec_command('grep -l "server_name freedownloader.top" /etc/nginx/sites-enabled/*')
print(stdout.read().decode('utf-8'))
client.close()
