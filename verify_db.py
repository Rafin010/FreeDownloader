import paramiko

client=paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('75.127.1.75', 22, 'root', 'OcjRMVUDAPyFWB8JuUAf')

script="""
mysql downloader_analytics -e \"SELECT event_type, COUNT(*) FROM events WHERE created_at >= NOW() - INTERVAL 1 HOUR GROUP BY event_type;\"
"""
stdin, stdout, stderr = client.exec_command(script)
db_out = stdout.read().decode()
db_err = stderr.read().decode()

with open('db_status.txt', 'w', encoding='utf-8') as f:
    f.write("EVENTS:\n")
    f.write(db_out if db_out else "EMPTY OR ERROR\n")
    f.write("\nERRORS:\n")
    f.write(db_err)

client.close()
