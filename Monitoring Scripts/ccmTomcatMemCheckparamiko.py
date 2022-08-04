from datetime import datetime
import time
import os
from getpass import getpass
import paramiko

# Directories
path = os.getcwd()


# Collect IP Address, Username and Password for CCM Publisher
def infocollect():
    ip = str(input("Collect: CCM Pub IP? : "))
    un = str(input("Collect: OS Username? : "))
    pw = getpass("Collect: OS Password? : ")
    return ip, un, pw


# Processing command input, needed in netrequests()
def receivestr(sshconn, cmd):
    buffer = ''
    prompt = 'admin:'
    if cmd != '':
        sshconn.send(cmd)
    while not sshconn.recv_ready():
        time.sleep(.5)
        buffer += str(sshconn.recv(65535), 'utf-8')
        if buffer.endswith(prompt):
            break
    return buffer


# Heavy Lifting
def netrequests():
    _sshconn = paramiko.SSHClient()
    _sshconn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        # Time
        now = datetime.now()
        timestr = now.strftime("%Y%m%d-%H%M%S")
        _sshconn.connect(hostname=ip, port=22, username=un, password=pw, timeout=300,
                             banner_timeout=300)
        invokeshell = _sshconn.invoke_shell()
        receivestr(invokeshell, '')
        # print("Disabling Pagination")
        buffer = receivestr(invokeshell, 'set cli pagination off\n')
        # print("Collecting Using-Most")
        buffer = receivestr(invokeshell, 'show process using-most memory\n')
        usingmost = buffer.split('\r\n')
        # print("Collecting Runtime Memory")
        buffer = receivestr(invokeshell, 'show tech runtime memory\n')
        runtime = buffer.split('\r\n')
        # print("Collecting AXL Stats")
        buffer = receivestr(invokeshell, 'show perf query class "Cisco AXL Tomcat Web Application"\n')
        axl = buffer.split('\r\n')
        # print("Collecting Tomcat Stats")
        buffer = receivestr(invokeshell, 'show perf query class "Cisco Tomcat Web Application"\n')
        tomcat = buffer.split('\r\n')
        _sshconn.close()
        # print("SSH Closed. Constructing report.")
        with open('HealthCheck_' + timestr + '.txt', 'w+') as filewrite:
            filewrite.write("Health Check Output\n")
            filewrite.write('\n\n')
            for line in usingmost:
                filewrite.write(line + '\n')
            filewrite.write('\n\n')
            for line in runtime:
                filewrite.write(line + '\n')
            filewrite.write('\n\n')
            for line in axl:
                filewrite.write(line + '\n')
            filewrite.write('\n\n')
            for line in tomcat:
                filewrite.write(line + '\n')
        filewrite.close()
    except Exception as e:
        print(e)
        exit()


if __name__ == "__main__":
    ip, un, pw = infocollect()
    while True:
        netrequests()
        time.sleep(86348)
