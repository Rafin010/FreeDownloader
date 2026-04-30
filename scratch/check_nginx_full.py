import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('75.127.1.75', 22, 'root', 'OcjRMVUDAPyFWB8JuUAf')

# Check ALL nginx configs - including SSL blocks
cmd = """
echo '=== ALL NGINX FILES ==='
ls -la /etc/nginx/sites-enabled/

echo ''
echo '=== FULL CONFIG FOR EACH DOMAIN ==='
for f in /etc/nginx/sites-enabled/*; do
    echo "============ $(basename $f) ============"
    cat "$f"
    echo ''
done

echo '=== DEFAULT CONFIG ==='
cat /etc/nginx/sites-enabled/default 2>/dev/null || echo 'no default'

echo ''
echo '=== CURL DOMAIN TESTS (via Host header) ==='
curl -sk -o /dev/null -w "youtube.freedownloader.top: %{http_code} -> %{redirect_url}\\n" -H "Host: youtube.freedownloader.top" http://127.0.0.1/
curl -sk -o /dev/null -w "facebook.freedownloader.top: %{http_code} -> %{redirect_url}\\n" -H "Host: facebook.freedownloader.top" http://127.0.0.1/
curl -sk -o /dev/null -w "instagram.freedownloader.top: %{http_code} -> %{redirect_url}\\n" -H "Host: instagram.freedownloader.top" http://127.0.0.1/
curl -sk -o /dev/null -w "freedownloader.top: %{http_code} -> %{redirect_url}\\n" -H "Host: freedownloader.top" http://127.0.0.1/
"""

stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
stdout.channel.recv_exit_status()
out = stdout.read().decode('utf-8', 'replace')

with open(r'e:\_free downloader Projext\scratch\nginx_full_dump.txt', 'w', encoding='utf-8') as f:
    f.write(out)

print(out[:5000])
client.close()
