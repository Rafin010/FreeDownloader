import paramiko
import os

client=paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('75.127.1.75', 22, 'root', 'OcjRMVUDAPyFWB8JuUAf')

# Check .env first to be sure of the DB name
stdin, stdout, stderr = client.exec_command('cat /root/FreeDownloader/backend/.env')
env_content = stdout.read().decode()
print("ENV CONTENT:\n", env_content)

# Extract DB name from env
db_name = "downloader_analytics"
for line in env_content.splitlines():
    if line.startswith("DB_NAME="):
        db_name = line.split("=")[1].strip()

# Check websites table in that DB
stdin, stdout, stderr = client.exec_command(f'mysql -u root -e "SELECT id, name, url FROM {db_name}.websites;"')
db_out = stdout.read().decode()
db_err = stderr.read().decode()

with open('db_status.txt', 'w', encoding='utf-8') as f:
    f.write(f"DB NAME: {db_name}\n\n")
    f.write("WEBSITES TABLE:\n")
    f.write(db_out if db_out else "EMPTY OR ERROR\n")
    f.write("\nERRORS:\n")
    f.write(db_err)

client.close()
