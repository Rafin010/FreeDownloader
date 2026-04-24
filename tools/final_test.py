import paramiko

def final_test():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, port, username, password)

        script = r"""
echo "=== TESTING YOUTUBE API ==="
curl -X POST http://127.0.0.1:8004/api/get_info -H "Content-Type: application/json" -d '{"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ"}' 2>/dev/null

echo ""
echo "=== TESTING TIKTOK API ==="
curl -X POST http://127.0.0.1:8003/api/get_info -H "Content-Type: application/json" -d '{"url":"https://www.tiktok.com/@scout2015/video/6718335390845095173"}' 2>/dev/null

echo ""
echo "=== TESTING P_D API (Universal) ==="
curl -X POST http://127.0.0.1:8009/api/get_info -H "Content-Type: application/json" -d '{"url":"https://www.xvideos.com/video71650371/tease_to_please_p1"}' 2>/dev/null
"""
        stdin, stdout, stderr = client.exec_command(script, timeout=60)
        stdout.channel.recv_exit_status()
        raw = stdout.read()
        
        with open(r"e:\_free downloader Projext\scratch\final_test.txt", "wb") as f:
            f.write(raw)
            
    except Exception as e:
        with open(r"e:\_free downloader Projext\scratch\final_test.txt", "w") as f:
            f.write(f"Exception: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    final_test()
