import pexpect
import os
import time


def portcheck():
    child = pexpect.spawn('telnet 1.1.1.1 3804')
    index = child.expect_exact(['closed', pexpect.EOF, pexpect.TIMEOUT], timeout=2)
    if index != 0:
        child.close()
        exit()
    else:
        os.system('echo "The CAPF Port is down. The Cisco CAPF Service needs to be restarted." | mail -s '
                  '"CAPF Port Check" email@domain.com')


while True:
    try:
        print("Performing the port check for CAPF Port 3804.")
        portcheck()
        print("Port check has been completed.")
        print("Email has been sent.")
    except Exception as (e):
        print("Oh no! We failed somewhere. We'll try again in 30 minutes.")
        with open('error.txt', 'w') as filewrite:
            filewrite.write(e)
        os.system('echo "The script hit an exception. Check error.txt." | mail -s "CAPF Script" email@domain.com')
    finally:
        time.sleep(1800)
