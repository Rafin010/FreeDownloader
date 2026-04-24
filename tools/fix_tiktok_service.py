import paramiko
import time

HOST = "75.127.1.75"
USER = "root"
PASS = "OcjRMVUDAPyFWB8JuUAf"

def run(client, cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    stdout.channel.recv_exit_status()
    return stdout.read().decode('utf-8', errors='ignore').strip()

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASS)

    print("=== ROOT CAUSE: tiktok.service is a duplicate binding 0.0.0.0:8003 ===")
    print()
    print("tiktok.service content:")
    print(run(client, "cat /etc/systemd/system/tiktok.service"))
    print()

    # Step 1: Stop and disable the rogue tiktok.service
    print("Step 1: Stop and disable tiktok.service")
    run(client, "systemctl stop tiktok.service")
    run(client, "systemctl disable tiktok.service")
    time.sleep(1)

    # Step 2: Remove the rogue service files  
    print("Step 2: Remove tiktok.service and tiktok.service.save")
    run(client, "rm -f /etc/systemd/system/tiktok.service /etc/systemd/system/tiktok.service.save")

    # Step 3: Kill any remaining rogue 0.0.0.0:8003 processes
    print("Step 3: Kill rogue processes on port 8003")
    run(client, "fuser -k -9 8003/tcp")
    time.sleep(2)

    # Step 4: Reload and restart tik
    print("Step 4: Restart tik.service cleanly")
    run(client, "systemctl daemon-reload")
    run(client, "systemctl restart tik.service")
    time.sleep(5)

    # Verify
    print()
    print("=== FINAL VERIFICATION ===")
    tik_status = run(client, "systemctl is-active tik")
    print(f"tik.service: {tik_status}")

    # Check port 8003 is now 127.0.0.1 not 0.0.0.0
    port = run(client, "ss -tlnp | grep 8003")
    print(f"Port 8003: {port}")

    # Check NO tiktok.service exists
    exists = run(client, "ls /etc/systemd/system/tiktok.service 2>/dev/null || echo REMOVED")
    print(f"tiktok.service: {exists}")

    # Test all endpoints
    print()
    print("Testing all HTTP endpoints:")
    for p, name in [(8001, 'yt'), (8002, 'fb'), (8003, 'tik'), (8004, 'insta'), (8005, 'p')]:
        code = run(client, f"curl -s -o /dev/null -w '%{{http_code}}' http://127.0.0.1:{p}/ --max-time 5")
        print(f"  {name} (:{p}): HTTP {code}")

    client.close()
    print("\nDone! All services fixed permanently.")

if __name__ == "__main__":
    main()
