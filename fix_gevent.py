import paramiko

def remove_gevent_worker():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, port, username, password)
        
        script = """
        echo "Removing -k gevent from all downloader services to use default (sync/threads) worker because gevent installation fails"
        sed -i 's/-k gevent/--threads 4/g' /etc/systemd/system/fb.service
        sed -i 's/-k gevent/--threads 4/g' /etc/systemd/system/insta.service
        sed -i 's/-k gevent/--threads 4/g' /etc/systemd/system/tiktok.service
        sed -i 's/-k gevent/--threads 4/g' /etc/systemd/system/yt.service
        sed -i 's/-k gevent/--threads 4/g' /etc/systemd/system/youtube.service 2>/dev/null || true
        
        systemctl daemon-reload
        
        systemctl restart fb.service insta.service tiktok.service yt.service free_d.service p_d.service freedownloader.service
        sleep 3
        systemctl is-active fb.service insta.service tiktok.service yt.service
        
        echo "Done checking statuses"
        """
        
        stdin, stdout, stderr = client.exec_command(script, timeout=60)
        out = stdout.read().decode('utf-8', 'replace').strip()
        print("OUTPUT:\n", out)
        err = stderr.read().decode('utf-8', 'replace').strip()
        if err:
            print("ERR:\n", err)
            
    except Exception as e:
        print("Exception:", e)
    finally:
        client.close()

if __name__ == "__main__":
    remove_gevent_worker()
