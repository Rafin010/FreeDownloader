import paramiko
client=paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('75.127.1.75', 22, 'root', 'OcjRMVUDAPyFWB8JuUAf')
script="""
cat /root/FreeDownloader/backend/utils/db.py | grep DEFAULT_SITES -A 10
"""
stdin, stdout, stderr = client.exec_command(script)
out = stdout.read().decode('utf-8', errors='ignore')
err = stderr.read().decode('utf-8', errors='ignore')
with open('temp_db.txt', 'w', encoding='utf-8') as f:
    f.write("OUT:\n" + out + "\nERR:\n" + err)
client.close()
