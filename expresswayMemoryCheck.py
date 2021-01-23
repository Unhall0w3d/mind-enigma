#
# Script created by Ken Perry
# Script purpose is to verify memory util on Expressway Servers
# Script method is SSH to pull output of 'cat /proc/meminfo | grep Committed_AS'
#

import time
import paramiko
import os
from getpass import getpass

# Define list of IP Addresses to SSH to
hostname = [
    "ip-addr1",
    "ip-addr2"
]

# Define Variables required for file handling
timestr = time.strftime("%Y%m%d-%H%M%S")
dirname = 'temp'
dir_path = os.getcwd()
path = os.path.join(dir_path, dirname)
filename = 'ExpresswayHC' + timestr + '.txt'
tarname = 'ExpresswayHC' + timestr + '.tar.gz'

# Check if desired directory exists, create it otherwise
if os.path.exists(dirname) is False:
    os.mkdir(dirname)

# Input Requirements taken from Env Variables
username = input("Username: ")
password = getpass("Password: ")


# Command to execute
command = "cat /proc/meminfo | grep Committed_AS"

# Initialize SSH Client
client = paramiko.SSHClient()

# Add to Known Hosts
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# For each ip address in our list, SSH to the device.
# Run the defined command and log the output to a text file
# One text file per script run, script checks all required devices.


def healthcheck(filename, hostname):
    for ipaddr in hostname:
        try:
            client.connect(hostname=ipaddr, username=username, password=password)
            print("+" * 10, ipaddr, "+" * 10)
            print("=" * 10, command, "=" * 10)
            stdin, stdout, stderr = client.exec_command(command)
            print(stdout.read().decode())
            err = stderr.read().decode()
            if err:
                print(err)
            with open(os.path.join(filename), 'a+') as rdr:
                rdr.write("+" * 10 + ipaddr + "+" * 10 + '\r')
                rdr.write("=" * 10 + command + "=" * 10 + '\r')
                rdr.write(stdout.read().decode() + '\r')
                if err:
                    rdr.write(stderr.read().decode() + '\r')
        except:
            print("[!] Cannot connect to the Expressway Server " + ipaddr + ". Please manually verify access.")
            with open(os.path.join(filename), 'a+') as rdr:
                rdr.write('[!] Cannot connect to the Expressway Server ' + ipaddr + '. Please manually verify access.' + '\r')


def filehandling(filename, tarname):
    os.system('tar jcvf ' + tarname + ' ' + tarname)
    os.system('rm ' + filename)
    os.system('mv ' + tarname + ' ' + path)


Flag = True
while Flag == True:
    try:
        healthcheck(filename, hostname)
        filehandling(filename, tarname)
        print("Script ran successfully, data was tarballed and stored in //current/working/directory/temp/")
        exit()
    except KeyboardInterrupt:
        print("\r\n")
        exit()
