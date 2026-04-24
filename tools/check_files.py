import paramiko

def check_files():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, port, username, password)

        script = r"""
echo "Checking free_d"
ls -la /root/FreeDownloader/free_d | grep -E "sw|monetag"

echo "Checking fb_downloader"
ls -la /root/FreeDownloader/fb_downloader | grep -E "sw|monetag"

echo "Checking yt_d"
ls -la /root/FreeDownloader/yt_d | grep -E "sw|monetag"

echo "Checking root"
ls -la /root/FreeDownloader/ | grep -E "sw|monetag"
"""
        stdin, stdout, stderr = client.exec_command(script, timeout=60)
        stdout.channel.recv_exit_status()
        raw = stdout.read()
        
        with open(r"e:\_free downloader Projext\scratch\file_check.txt", "wb") as f:
            f.write(raw)
            
    except Exception as e:
        with open(r"e:\_free downloader Projext\scratch\file_check.txt", "w") as f:
            f.write(f"Exception: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    check_files()
