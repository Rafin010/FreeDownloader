import paramiko
client=paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('75.127.1.75', 22, 'root', 'OcjRMVUDAPyFWB8JuUAf')
script="""
cd /root/FreeDownloader/backend
/root/FreeDownloader/venv/bin/python -c "from utils.db import initialize_database; initialize_database()"
"""
stdin, stdout, stderr = client.exec_command(script)
out = stdout.read().decode('utf-8', errors='ignore')
err = stderr.read().decode('utf-8', errors='ignore')
with open('temp_db.txt', 'w', encoding='utf-8') as f:
    f.write("OUT:\n" + out + "\nERR:\n" + err)
client.close()
