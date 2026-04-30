import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('75.127.1.75', 22, 'root', 'OcjRMVUDAPyFWB8JuUAf')

# Step 1: Show current configs
cmd = """
echo '=== NGINX DOMAIN MAP ==='
for f in /etc/nginx/sites-enabled/*.top; do
    echo "--- $(basename $f) ---"
    grep -E 'server_name|proxy_pass' "$f"
done

echo ''
echo '=== SERVICE STATUS ==='
for svc in fb insta tiktok yt p_d free_d freedownloader; do
    printf "$svc: "
    systemctl is-active $svc.service
done

echo ''
echo '=== CURL TESTS ==='
curl -s -o /dev/null -w "FB(8001): %{http_code}\\n" http://127.0.0.1:8001/
curl -s -o /dev/null -w "Insta(8002): %{http_code}\\n" http://127.0.0.1:8002/
curl -s -o /dev/null -w "Tik(8003): %{http_code}\\n" http://127.0.0.1:8003/
curl -s -o /dev/null -w "YT(8004): %{http_code}\\n" http://127.0.0.1:8004/
curl -s -o /dev/null -w "FreeD(8008): %{http_code}\\n" http://127.0.0.1:8008/
curl -s -o /dev/null -w "PD(8009): %{http_code}\\n" http://127.0.0.1:8009/

echo ''
echo '=== TITLE CHECK (which app is on which port) ==='
curl -s http://127.0.0.1:8001/ | grep -oP '<title>\\K[^<]+'
curl -s http://127.0.0.1:8002/ | grep -oP '<title>\\K[^<]+'
curl -s http://127.0.0.1:8003/ | grep -oP '<title>\\K[^<]+'
curl -s http://127.0.0.1:8004/ | grep -oP '<title>\\K[^<]+'
curl -s http://127.0.0.1:8008/ | grep -oP '<title>\\K[^<]+'
curl -s http://127.0.0.1:8009/ | grep -oP '<title>\\K[^<]+'
"""

stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
stdout.channel.recv_exit_status()
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print("STDERR:", err)
client.close()
