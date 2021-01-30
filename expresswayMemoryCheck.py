#
# Script created by Ken Perry
# Script purpose is to verify memory util on Expressway Servers
# Script method is SSH to pull output of 'cat /proc/meminfo | grep Committed_AS'
# Script is set to run every 12 hours to provide feedback.
# If you need this script to check your expressway memory in this manner, you likely need to do it 1-2 times daily.
#

import time
import paramiko
import os
from getpass import getpass

# Define list of IP Addresses to SSH to.
# Replace the ip-addr# in quotes with an IP address (e.g. 10.161.1.133), one per line.
# Follow the syntax below to add additional entries

hostname = [
    "ip-addr1",
    "ip-addr2"
]

# Define Variables required for file handling
timestr = time.strftime("%Y%m%d-%H%M%S")
dirname = 'temp'
dir_path = os.getcwd()
path = os.path.join(dir_path, dirname)
filename = 'ExpresswayHC.txt'
timestampedfn = 'ExpresswayHC' + timestr + '.txt'

# Check if desired directory exists, create it otherwise
if os.path.exists(dirname) is False:
    os.mkdir(dirname)

# Input Requirements taken from Env Variables
username = input("Username: ")
password = getpass("Password: ")


# Command to execute
command = "cat /proc/meminfo | grep Committed_AS"

# Initialize SSH Client & Add to Known Hosts
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# For each ip address in our list, SSH to the device.
# Run the defined command and log the output to a text file
# One text file per script run, script checks all required devices.


def healthcheck():
    for ipaddr in hostname:
        try:
            client.connect(hostname=ipaddr, username=username, password=password)
            stdin, stdout, stderr = client.exec_command(command)
            err = stderr.read().decode()
            with open(os.path.join(path, filename), 'a+') as rdr:
                rdr.write("+" * 5 + ipaddr + "+" * 5 + '\r')
                rdr.write(command + '\r')
                rdr.write(stdout.read().decode() + '\r')
                if err:
                    rdr.write(stderr.read().decode() + '\r')
        except:
            with open(os.path.join(path, filename), 'a+') as rdr:
                rdr.write('[!] Cannot connect to ' + ipaddr + '. Please verify reachability & Credentials.' + '\r')


def filehandling():
    # The below allows you to email the file to your email, or a distro list if you have smtp configured on your linux machine.
    # "mail" command should work before trying to use it through this script.
    # os.system('mail -s "Expressway Healthchecks" email@domain.com < ' + path + filename + '')
    os.system('cp ' + path + filename + ' ' + path + timestampedfn + '')
    os.system('rm ' + path + filename)


while True:
    try:
        healthcheck()
        filehandling()
        # Uncomment the line below if you use the email function above.
        # print("Email has been sent.")
    except:
        print("Oh no! We failed somewhere. We'll try again in 6 hours. Use Email function for better notifications.")
        # os.system('mail -s "Script Stopped" email@domain.com')
    finally:
        time.sleep(43200)
