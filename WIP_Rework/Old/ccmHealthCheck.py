#
# Script created by Ken Perry
#

import paramiko
from paramiko_expect import SSHClientInteraction
from getpass import getpass
import time
import os

# Input Requirements taken from User Input
username = input("Username: ")
password = getpass("Password: ")

# Define Variables required for file handling
dirname = 'temp'
dir_path = os.getcwd()
path = os.path.join(dir_path, dirname)
timestr = time.strftime("%Y%m%d-%H%M%S")

# Check if desired directory exists, create it otherwise
if os.path.exists(dirname) is False:
    os.mkdir(dirname)

# Define list of IP Addresses to SSH to.
# Replace the ip-addr# in quotes with an IP address (e.g. 10.161.1.133), one per line.
# Follow the syntax below to add additional entries
hostname = [
    "ip-addr1",
    "ip-addr2"
]

# Commands to execute against the CLI
commands = [
    'set cli pagination off',  # Turns off pagination so the script doesn't fail.
    'show status',  # Shows the uptime, cpu/mem/disk util and other misc. system info.
    'show version active',  # Verifies the active version.
    # Useful for upgrade/downgrade tasks and seeing installed cop files.
    'show version inactive',  # Verifies the inactive version.
    # Useful for upgrade/downgrade tasks and seeing installed cop files.
    'show hardware',  # Virtual hardware nowadays, may be important when you least expect it.
    'show network cluster',  # Reports cluster node IPs/Hostname or FQDN and date of last connectivity state change.
    'show perf query class Processor',  # Performance monitoring statistics for CPU.
    'show perf query class Memory',  # Performance monitoring statistics for Memory.
    'utils service list',  # Verify the running services. Compare pre and post change output for service state.
    'utils ntp status',  # Verify NTP status. Pub should be Stratum 3 maximum, Sub should be Stratum 4 maximum.
    'utils disaster_recovery history backup',  # Check the simple status of the last 10 or so days of backups.
    'utils disaster_recovery status backup',  # Check the status of the last backup.
    'utils dbreplication runtimestate',  # Verify dbreplication state as per last run of status command.
    # Table sync details only available from Pub. Will show connectivity state/dbrepl queue as of *now*.
    'utils core active list',  # Verify if any core files exist. Check dates, if recent, review.
    'show risdb query misc phone phonefailed cmnode cmgroup cti ctiextn uone huntlist ctimlist gateway sip '
    'mediaresource h323',  # Checks many things, including registered phones, sip trunks, hunt lists and more.
    'utils diagnose test',  # Built in diagnostics. Output is ugly, remove this line if you don't require this.
    'exit'
]

# For each ip address in our list, SSH to the device.
# Run the defined command and log the output to a text file
# One text file per node. File name contains both node IP and timestamp.


def session():
    try:
        sshconnect = paramiko.SSHClient()
        sshconnect.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        for ipaddr in hostname:
            filename = 'CCMHealthCheck_' + ipaddr.replace('.', '_') + '_' + timestr
            outputfile = '{}.txt'.format(filename)
            sshconnect.connect(hostname=ipaddr, username=username, password=password)
            interact = SSHClientInteraction(sshconnect, timeout=60, display=True)
            for command in commands:
                interact.expect('admin:')
                interact.send(command)
                devoutput = interact.current_output_clean
                with open(os.path.join(path, outputfile), 'a') as filewrite:
                    filewrite.write('#' * 5 + command + '#' * 5)
                    filewrite.write(devoutput)
        sshconnect.close()
    except paramiko.ssh_exception.AuthenticationException as a:
        print(a)
    except paramiko.ssh_exception.SSHException as c:
        print(c)
    except Exception as e:
        print(e)

session()
print('\r' * 2)
print('The script has completed. Please check the Health Check files for valid output.')
exit()
