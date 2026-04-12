import paramiko

def try_python_versions():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, port, username, password)
        
        # Check what pythons are available from deadsnakes
        script = """
export DEBIAN_FRONTEND=noninteractive
apt-cache search python3 | grep -E "^python3\.[0-9]+ " | sort
"""
        stdin, stdout, stderr = client.exec_command(script, timeout=30)
        stdout.channel.recv_exit_status()
        out = stdout.read().decode('utf-8', 'replace').strip()
        print("Available Python versions:")
        print(out)
        
        # Try installing python3.10 or python3.9
        script2 = """
export DEBIAN_FRONTEND=noninteractive
apt-get install -y python3.10 python3.10-venv 2>&1 || apt-get install -y python3.9 python3.9-venv 2>&1
python3.10 --version 2>&1 || python3.9 --version 2>&1 || echo "NO NEW PYTHON"
"""
        print("\nTrying to install Python 3.10 or 3.9...")
        stdin, stdout, stderr = client.exec_command(script2, timeout=120)
        exit_code = stdout.channel.recv_exit_status()
        out = stdout.read().decode('utf-8', 'replace').strip()
        print("EXIT:", exit_code)
        print("OUT:", out.encode('ascii', 'replace').decode('ascii')[-1500:])
        
    except Exception as e:
        print("Exception:", e)
    finally:
        client.close()

if __name__ == "__main__":
    try_python_versions()
