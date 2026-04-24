import paramiko

def inspect_services():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, port, username, password)
        
        script = """
        grep ExecStart /etc/systemd/system/fb.service
        grep ExecStart /etc/systemd/system/insta.service
        grep ExecStart /etc/systemd/system/tiktok.service
        cat /etc/systemd/system/p_d.service | grep ExecStart
        """
        
        stdin, stdout, stderr = client.exec_command(script, timeout=30)
        out = stdout.read().decode('utf-8', 'replace').strip()
        print(out)
        
    except Exception as e:
        print("Exception:", e)
    finally:
        client.close()

if __name__ == "__main__":
    inspect_services()
