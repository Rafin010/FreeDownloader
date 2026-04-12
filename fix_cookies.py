import paramiko

def fix_fb():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, port, username, password)
        
        script = """
# 1. The broken cookies.txt files are CAUSING the errors!
#    Remove/rename them so yt-dlp works WITHOUT cookies (for public videos)
mv /root/FreeDownloader/fb_downloader/cookies.txt /root/FreeDownloader/fb_downloader/cookies.txt.broken 2>/dev/null || true
mv /root/FreeDownloader/yt_d/cookies.txt /root/FreeDownloader/yt_d/cookies.txt.broken 2>/dev/null || true
mv /root/FreeDownloader/insta_d/cookies.txt /root/FreeDownloader/insta_d/cookies.txt.broken 2>/dev/null || true
mv /root/FreeDownloader/tik_d/cookies.txt /root/FreeDownloader/tik_d/cookies.txt.broken 2>/dev/null || true

# 2. Test Facebook download WITHOUT cookies
/root/FreeDownloader/venv/bin/yt-dlp --dump-json --no-warnings "https://www.facebook.com/share/v/18THtMvMsG/" 2>&1 | head -3

# 3. Restart all services
pkill gunicorn || true
sleep 2
systemctl restart fb.service insta.service tiktok.service yt.service free_d.service p_d.service freedownloader.service
sleep 2
systemctl is-active fb.service insta.service tiktok.service yt.service free_d.service p_d.service freedownloader.service
"""
        
        stdin, stdout, stderr = client.exec_command(script, timeout=60)
        stdout.channel.recv_exit_status()
        out = stdout.read().decode('utf-8', 'replace').strip()
        err = stderr.read().decode('utf-8', 'replace').strip()
        print("OUT:", out.encode('ascii', 'replace').decode('ascii')[-3000:])
        if err:
            print("ERR:", err.encode('ascii', 'replace').decode('ascii')[-2000:])
        print("Done!")
            
    except Exception as e:
        print("Exception:", e)
    finally:
        client.close()

if __name__ == "__main__":
    fix_fb()
