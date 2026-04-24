import paramiko

def check_all():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, port, username, password)

        script = r"""
echo "===== YT SERVICE =====" 
journalctl -u yt.service -n 20 --no-pager 2>&1
echo ""
echo "===== TIKTOK SERVICE =====" 
journalctl -u tiktok.service -n 20 --no-pager 2>&1
echo ""
echo "===== P_D SERVICE =====" 
journalctl -u p_d.service -n 20 --no-pager 2>&1
echo ""
echo "===== PORT CHECK ====="
ss -tlnp | grep -E '800[0-9]' 2>&1
echo ""
echo "===== CURL TESTS ====="
curl -s -o /dev/null -w "YT(8004): %{http_code}\n" http://127.0.0.1:8004/ 2>&1
curl -s -o /dev/null -w "TikTok(8003): %{http_code}\n" http://127.0.0.1:8003/ 2>&1
curl -s -o /dev/null -w "P_D(8009): %{http_code}\n" http://127.0.0.1:8009/ 2>&1
curl -s -o /dev/null -w "FB(8001): %{http_code}\n" http://127.0.0.1:8001/ 2>&1
curl -s -o /dev/null -w "Insta(8002): %{http_code}\n" http://127.0.0.1:8002/ 2>&1
"""
        stdin, stdout, stderr = client.exec_command(script, timeout=30)
        stdout.channel.recv_exit_status()
        raw = stdout.read()
        
        with open(r"e:\_free downloader Projext\scratch\service_check.txt", "wb") as f:
            f.write(raw)
            
    except Exception as e:
        with open(r"e:\_free downloader Projext\scratch\service_check.txt", "w") as f:
            f.write(f"Exception: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    check_all()
