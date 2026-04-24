import paramiko
import sys

def run_diagnostics():
    hostname = "75.127.1.75"
    port = 22
    username = "root"
    password = "OcjRMVUDAPyFWB8JuUAf"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname, port, username, password)
        
        # Check services
        services = ["yt", "fb", "tik", "insta", "p_d", "redis-server"]
        check_cmds = []
        for svc in services:
            check_cmds.append(f"echo '--- {svc} ---'; systemctl is-active {svc} || echo 'INACTIVE'; systemctl status {svc} --no-pager -n 5")
        
        # Check Celery workers too
        for svc in ["yt", "fb", "tik", "insta", "p_d"]:
            check_cmds.append(f"echo '--- celery-{svc} ---'; systemctl is-active celery-{svc} || echo 'INACTIVE'")

        # Check listening ports
        check_cmds.append("echo '--- LISTENING PORTS ---'; ss -tlnp | grep -E '800|6379'")
        
        # Check Nginx error logs (last 20 lines)
        check_cmds.append("echo '--- NGINX ERRORS ---'; tail -n 20 /var/log/nginx/error.log")
        
        # Check Nginx configs to find the subdomains
        check_cmds.append("echo '--- NGINX SUBDOMAINS ---'; grep -rn 'server_name' /etc/nginx/sites-enabled/ /etc/nginx/conf.d/")

        full_script = " && ".join([f"({c})" for c in check_cmds])
        
        print("Running diagnostics on VPS...")
        stdin, stdout, stderr = client.exec_command(full_script)
        
        out = stdout.read().decode('utf-8', 'replace')
        err = stderr.read().decode('utf-8', 'replace')
        
        # Output results
        print("\n=== DIAGNOSTIC OUTPUT ===\n")
        # Handle encoding issues in Windows console
        safe_out = out.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
        print(safe_out)
        
        if err:
            print("\n=== ERRORS ===\n")
            safe_err = err.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
            print(safe_err)
            
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    run_diagnostics()
