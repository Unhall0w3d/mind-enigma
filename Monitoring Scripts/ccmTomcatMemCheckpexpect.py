from datetime import datetime
import time
import os
from getpass import getpass
import pexpect

# Directories
path = os.getcwd()

# Prompts
prompt = 'admin:'


# Collect IP Address, Username and Password for CCM Publisher
def infocollect():
    ip = str(input("Collect: CCM Pub IP? : "))
    un = str(input("Collect: OS Username? : "))
    pw = getpass("Collect: OS Password? : ")
    return ip, un, pw


# Heavy lifting
def backsquats():
    now = datetime.now()
    timestr = now.strftime("%Y%m%d-%H%M%S")
    client = pexpect.spawn('ssh -o StrictHostKeyChecking=no %s@%s' % (un, ip))
    index = client.expect_exact(['assword:', 'Connection refused', pexpect.EOF, pexpect.TIMEOUT], timeout=60)
    if index != 0:
        print("Warning: Failed to log in to ", ip, " please check IP information or device status.")
        exit()
    client.sendline(pw)
    index = client.expect_exact([prompt, 'assword:', 'Connection closed', pexpect.EOF, pexpect.TIMEOUT], timeout=60)
    if index != 0:
        print("Warning: Failed to log in to ", ip, " please check IP information or device status.")
        exit()
    time.sleep(5)
    client.sendline("set cli pagination off\n")
    time.sleep(2)
    client.sendline('show perf query class "Cisco AXL Tomcat Web Application"\r')
    client.expect([prompt, pexpect.EOF, pexpect.TIMEOUT])
    axl = client.before
    time.sleep(2)
    client.sendline('show perf query class "Cisco Tomcat Web Application"\r')
    client.expect([prompt, pexpect.EOF, pexpect.TIMEOUT])
    tomcat = client.before
    time.sleep(2)
    client.sendline("show process using-most memory\r")
    client.expect([prompt, pexpect.EOF, pexpect.TIMEOUT])
    usingmost = client.before
    time.sleep(2)
    client.sendline("show tech runtime memory\r")
    client.expect([prompt, pexpect.EOF, pexpect.TIMEOUT])
    runtime = client.before
    client.close()
    with open('HealthCheck_' + timestr + '.txt', 'w+') as filewrite:
        filewrite.write("Health Check Output\n")
        filewrite.write('\n\n')
        filewrite.write(usingmost)
        filewrite.write('\n\n')
        filewrite.write(runtime)
        filewrite.write('\n\n')
        filewrite.write(axl)
        filewrite.write('\n\n')
        filewrite.write(tomcat)
    filewrite.close()


if __name__ == "__main__":
    ip, un, pw = infocollect()
    while True:
        backsquats()
        time.sleep(86340)
