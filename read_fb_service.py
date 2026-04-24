import paramiko

def read_full_service():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, port, username, password)
        stdin, stdout, stderr = client.exec_command("cat /etc/systemd/system/fb.service")
        print(stdout.read().decode('utf-8', 'replace'))
    except Exception as e:
        print("Exception:", e)
    finally:
        client.close()

if __name__ == "__main__":
    read_full_service()
