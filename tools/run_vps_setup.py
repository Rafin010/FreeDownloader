import paramiko
import sys

def main():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(hostname, port, username, password)
        print("Connected to VPS!")
        
        print("Running setup_infrastructure.py, this will take some time...")
        cmd = "cd /root/FreeDownloader && python3 setup_infrastructure.py"
        stdin, stdout, stderr = client.exec_command(cmd)
        
        for line in stdout:
            # Safely encode/decode to print in Windows terminal
            safe_line = line.encode('ascii', 'replace').decode('ascii')
            print(safe_line, end="")
            
        for line in stderr:
            safe_line = line.encode('ascii', 'replace').decode('ascii')
            print("STDERR: ", safe_line, end="")
            
        print("VPS SETUP COMPLETE!")
        
    except Exception as e:
        print(f"Deployment error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
