import paramiko
import os

def main():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port, username, password)
    
    sftp = client.open_sftp()
    local_file = 'tik_d/sitemap.xml'
    remote_file = '/root/FreeDownloader/tik_d/sitemap.xml'
    if os.path.exists(local_file):
        print(f"Uploading {local_file}...")
        sftp.put(local_file, remote_file)
    sftp.close()

    stdin, stdout, stderr = client.exec_command('systemctl restart tiktok.service')
    print("Restarted tiktok.service:", stdout.read().decode('utf-8'))
    client.close()

if __name__ == "__main__":
    main()
