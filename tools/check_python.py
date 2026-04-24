import paramiko

def upgrade_python_and_ytdlp():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, port, username, password)
        
        script = """
# Check if Python 3.10+ is available on the system
python3 --version
python3.10 --version 2>/dev/null || python3.11 --version 2>/dev/null || python3.12 --version 2>/dev/null || echo "No Python 3.10+ found"

# Check Ubuntu version
cat /etc/os-release | head -5

# Check if we can install newer Python
apt list --installed 2>/dev/null | grep python3 | head -10
"""
        
        stdin, stdout, stderr = client.exec_command(script, timeout=30)
        stdout.channel.recv_exit_status()
        out = stdout.read().decode('utf-8', 'replace').strip()
        err = stderr.read().decode('utf-8', 'replace').strip()
        print("OUT:", out.encode('ascii', 'replace').decode('ascii'))
        if err:
            print("ERR:", err.encode('ascii', 'replace').decode('ascii')[-1000:])
    except Exception as e:
        print("Exception:", e)
    finally:
        client.close()

if __name__ == "__main__":
    upgrade_python_and_ytdlp()
