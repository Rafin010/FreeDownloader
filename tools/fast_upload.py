import paramiko
import os

files_to_upload = [
    ('fb_downloader/app.py', '/root/FreeDownloader/fb_downloader/app.py'),
    ('fb_downloader/sitemap.xml', '/root/FreeDownloader/fb_downloader/sitemap.xml'),
    ('insta_d/app.py', '/root/FreeDownloader/insta_d/app.py'),
    ('insta_d/sitemap.xml', '/root/FreeDownloader/insta_d/sitemap.xml'),
    ('p_d/app.py', '/root/FreeDownloader/p_d/app.py'),
    ('p_d/sitemap.xml', '/root/FreeDownloader/p_d/sitemap.xml'),
    ('tik_d/app.py', '/root/FreeDownloader/tik_d/app.py'),
    ('tik_d/sitemap.xml', '/root/FreeDownloader/tik_d/sitemap.xml'),
    ('yt_d/app.py', '/root/FreeDownloader/yt_d/app.py'),
    ('yt_d/sitemap.xml', '/root/FreeDownloader/yt_d/sitemap.xml'),
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

        print("Restarting services...")
        restart_cmd = "systemctl restart fb.service yt.service free_d.service p_d.service tik_d.service insta.service freedownloader.service freestore.service"
        stdin, stdout, stderr = client.exec_command(restart_cmd)
        print(stdout.read().decode('utf-8'))
        
        print("DONE!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
