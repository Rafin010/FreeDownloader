import paramiko
import os

files_to_upload = [
    ('yt_d/app.py', '/root/FreeDownloader/yt_d/app.py'),
    ('yt_d/templates/index.html', '/root/FreeDownloader/yt_d/templates/index.html'),
    ('yt_d/static/logo.png', '/root/FreeDownloader/yt_d/static/logo.png')
]

def main():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(hostname, port, username, password)
        print("Connected to VPS!")
        
        sftp = client.open_sftp()
        for local_file, remote_file in files_to_upload:
            if os.path.exists(local_file):
                print(f"Uploading {local_file}...")
                sftp.put(local_file, remote_file)
            else:
                print(f"Skipping missing file: {local_file}")
        sftp.close()

        print("Restarting yt.service...")
        restart_cmd = "systemctl restart yt.service"
        stdin, stdout, stderr = client.exec_command(restart_cmd)
        print("STDOUT:", stdout.read().decode('utf-8'))
        err = stderr.read().decode('utf-8')
        if err:
            print("STDERR:", err)
        
        print("DONE!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
