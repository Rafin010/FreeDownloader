import paramiko
import json

def test():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, port, username, password)

        script = r"""
echo "=== FB TEST ===" > /tmp/test_result.txt
/root/FreeDownloader/venv/bin/yt-dlp --print title --no-warnings "https://www.facebook.com/share/v/18THtMvMsG/" >> /tmp/test_result.txt 2>&1
echo "EXIT:$?" >> /tmp/test_result.txt

echo "=== YT TEST ===" >> /tmp/test_result.txt
/root/FreeDownloader/venv/bin/yt-dlp --print title --no-warnings "https://www.youtube.com/watch?v=dQw4w9WgXcQ" >> /tmp/test_result.txt 2>&1
echo "EXIT:$?" >> /tmp/test_result.txt

echo "=== VERSIONS ===" >> /tmp/test_result.txt
/root/FreeDownloader/venv/bin/python --version >> /tmp/test_result.txt 2>&1
/root/FreeDownloader/venv/bin/yt-dlp --version >> /tmp/test_result.txt 2>&1

cat /tmp/test_result.txt
"""
        stdin, stdout, stderr = client.exec_command(script, timeout=120)
        stdout.channel.recv_exit_status()
        raw = stdout.read()
        # Write to file instead of printing
        with open(r"e:\_free downloader Projext\scratch\test_result.txt", "wb") as f:
            f.write(raw)
        
        # Read it back with utf-8
        with open(r"e:\_free downloader Projext\scratch\test_result.txt", "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        
        # Write clean ASCII version for display
        with open(r"e:\_free downloader Projext\scratch\test_result_clean.txt", "w", encoding="utf-8") as f:
            f.write(content)
        
    except Exception as e:
        with open(r"e:\_free downloader Projext\scratch\test_result_clean.txt", "w") as f:
            f.write(f"Exception: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    test()
