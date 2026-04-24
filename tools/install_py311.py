import paramiko

def install_py311():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, port, username, password)
        
        # Install software-properties-common first, then Python 3.11
        script = """
export DEBIAN_FRONTEND=noninteractive
apt-get update -y > /dev/null 2>&1
apt-get install -y software-properties-common > /dev/null 2>&1
echo "=== software-properties-common installed ==="
add-apt-repository -y ppa:deadsnakes/ppa > /dev/null 2>&1
echo "=== PPA added ==="
apt-get update -y > /dev/null 2>&1
apt-get install -y python3.11 python3.11-venv python3.11-dev 2>&1
echo "=== Python 3.11 install attempted ==="
python3.11 --version 2>&1
"""
        print("Installing Python 3.11 (this may take 1-2 minutes)...")
        stdin, stdout, stderr = client.exec_command(script, timeout=300)
        exit_code = stdout.channel.recv_exit_status()
        out = stdout.read().decode('utf-8', 'replace').strip()
        print("EXIT:", exit_code)
        print("OUT:", out.encode('ascii', 'replace').decode('ascii')[-2000:])
        
    except Exception as e:
        print("Exception:", e)
    finally:
        client.close()

if __name__ == "__main__":
    install_py311()
