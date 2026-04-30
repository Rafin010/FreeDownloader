import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('75.127.1.75', 22, 'root', 'OcjRMVUDAPyFWB8JuUAf')

cmd = """
echo '=== HTTPS CURL TESTS ==='
curl -sk -o /dev/null -w "youtube.freedownloader.top HTTPS: %{http_code}\\n" https://youtube.freedownloader.top/
curl -sk -o /dev/null -w "facebook.freedownloader.top HTTPS: %{http_code}\\n" https://facebook.freedownloader.top/
curl -sk -o /dev/null -w "instagram.freedownloader.top HTTPS: %{http_code}\\n" https://instagram.freedownloader.top/
curl -sk -o /dev/null -w "tiktok.freedownloader.top HTTPS: %{http_code}\\n" https://tiktok.freedownloader.top/
curl -sk -o /dev/null -w "porn.freedownloader.top HTTPS: %{http_code}\\n" https://porn.freedownloader.top/

echo ''
echo '=== PAGE TITLE CHECK (HTTPS) ==='
curl -sk https://youtube.freedownloader.top/ | grep -oP '<title>\\K[^<]+'
curl -sk https://facebook.freedownloader.top/ | grep -oP '<title>\\K[^<]+'
curl -sk https://instagram.freedownloader.top/ | grep -oP '<title>\\K[^<]+'
curl -sk https://tiktok.freedownloader.top/ | grep -oP '<title>\\K[^<]+'
curl -sk https://porn.freedownloader.top/ | grep -oP '<title>\\K[^<]+'
"""

stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
stdout.channel.recv_exit_status()
print(stdout.read().decode())
client.close()
