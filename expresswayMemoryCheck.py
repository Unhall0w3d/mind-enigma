#
# Script created by Ken Perry
# Script purpose is to verify memory util on Expressway Servers
# Script method is SSH to pull output of 'cat /proc/meminfo | grep Committed_AS'
#

import time
import paramiko
import os

# Define list of IP Addresses to SSH to
hostname = [
    "ip-addr1",
    "ip-addr2"
]

# Define Variables required for file creation
timestr = time.strftime("%Y%m%d-%H%M%S")
dirname = 'temp'
dir_path = os.getcwd()
path = os.path.join(dir_path, dirname)

# Check if desired directory exists, create it otherwise
if os.path.exists(dirname) is False:
    os.mkdir(dirname)

# Input Requirements taken from Env Variables
try:
    username = os.environ['expwyun']
    password = os.environ['expwypw']
except:
    sys.exit()

# Command to execute
command = "cat /proc/meminfo | grep Committed_AS"

# Initialize SSH Client
client = paramiko.SSHClient()

# Add to Known Hosts
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# For each ip address in our list, SSH to the device.
# Run the defined command and log the output to a text file
# One text file per script run, script checks all required devices.

for ipaddr in hostname:
    try:
        client.connect(hostname=ipaddr, username=username, password=password)
        # print("+" * 10, ipaddr, "+" * 10)
        # print("=" * 10, command, "=" * 10)
        stdin, stdout, stderr = client.exec_command(command)
        # print(stdout.read().decode())
        err = stderr.read().decode()
        # if err:
            # print(err)
        with open(os.path.join(path, 'ExpresswayHC' + timestr + '.txt'), 'a+') as rdr:
            rdr.write("+" * 10 + ipaddr + "+" * 10 + '\n')
            rdr.write("=" * 10 + command + "=" * 10 + '\n')
            rdr.write(stdout.read().decode() + '\n')
            if err:
                # print(err)
                rdr.write(stderr.read().decode() + '\n')
    except:
        # print("[!] Cannot connect to the Expressway Server " + ipaddr + ". Please manually verify access.")
        with open(os.path.join(path, 'ExpresswayHC' + timestr + '.txt'), 'a+') as rdr:
            rdr.write("[!] Cannot connect to the Expressway Server " + ipaddr + ". Please manually verify access." + '\n')
