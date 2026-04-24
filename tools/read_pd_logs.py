import paramiko

def check_pd_logs():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, port, username, password)
        
        script = """
        journalctl -u p_d.service -n 15 --no-pager
        """
        
        stdin, stdout, stderr = client.exec_command(script, timeout=30)
        out = stdout.read().decode('utf-8', 'replace').strip()
        print(out.encode('ascii', 'replace').decode('ascii'))
        
    except Exception as e:
        print("Exception:", e)
    finally:
        client.close()

if __name__ == "__main__":
    check_pd_logs()
