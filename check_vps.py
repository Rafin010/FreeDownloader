import paramiko
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('75.127.1.75', username='root', password='OcjRMVUDAPyFWB8JuUAf')

_, out1, _ = c.exec_command('ls /etc/systemd/system/ | grep tik')
print("tik service:")
print(out1.read().decode('utf-8'))

_, out2, _ = c.exec_command('ls /etc/systemd/system/ | grep p_d')
print("p_d service:")
print(out2.read().decode('utf-8'))

_, out3, _ = c.exec_command('systemctl restart tik_d.service p_d.service && systemctl status tik_d.service p_d.service --no-pager | grep Active')
print("Status after restart:")
print(out3.read().decode('utf-8'))
