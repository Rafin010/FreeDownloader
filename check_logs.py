import paramiko

def main():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port, username, password)
    
    stdin, stdout, stderr = client.exec_command('systemctl list-units --type=service | grep -E "tik|yt|p_d|insta|fb"')
    print(stdout.read().decode('utf-8'))
    client.close()

if __name__ == "__main__":
    main()
