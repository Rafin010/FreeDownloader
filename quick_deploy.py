import paramiko

def deploy():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, port, username, password)
        
        script = """
cd /root/FreeDownloader && git fetch origin && git reset --hard origin/main
pkill gunicorn || true
sleep 2
systemctl restart freedownloader.service fb.service insta.service tiktok.service yt.service free_d.service p_d.service
sleep 2
systemctl is-active freedownloader.service fb.service insta.service tiktok.service yt.service free_d.service p_d.service
"""
        
        stdin, stdout, stderr = client.exec_command(script, timeout=60)
        stdout.channel.recv_exit_status()
        out = stdout.read().decode('utf-8', 'replace').strip()
        err = stderr.read().decode('utf-8', 'replace').strip()
        print("OUT:", out.encode('ascii', 'replace').decode('ascii'))
        if err:
            print("ERR:", err.encode('ascii', 'replace').decode('ascii'))
        print("Done!")
            
    except Exception as e:
        print("Exception:", e)
    finally:
        client.close()

if __name__ == "__main__":
    deploy()
