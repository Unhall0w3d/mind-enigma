#!/usr/var/python
# -*- code:UTF-8 -*-

#####################################
# Script created by Ken Perry, 2022 #
#       NOC THOUGHTS BLOG           #
#    https://www.nocthoughts.com    #
#####################################

# to do
# Test "VM Snapshot" option.
# Add option to Check VM Power States, Prompt to Shut Off Each VM Gracefully.
# Add Main Menu option Enable or Disable maintenance mode.

# Import modules
import os
import re
import requests
import paramiko
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import time
from getpass import getpass
import urllib3
import ssl

# Define current time
timestr = time.strftime("%Y%m%d-%H%M%S")

# Disablement of HTTPS Insecure Request error message.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Paramiko ssh connection details
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.load_system_host_keys()

# Ignore SSL certificate warnings
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE


def cred_collect():
    # Collect login details for ESXi
    print("Enter the vSphere server hostname:")
    server = input()
    print("Enter the Port Forward port number, or 443:")
    port = input()
    print("Enter the vSphere server username:")
    username = input()
    print("Enter the vSphere server password:")
    password = getpass()

    return server, username, password, port


def list_vms(server, username, password, port):
    # Connect and collect vm details
    try:
        si = SmartConnect(host=server, user=username, pwd=password, port=port, sslContext=context)

        # Retrieve a list of all virtual machines in the vSphere environment
        vm_view = si.content.viewManager.CreateContainerView(si.content.rootFolder, [vim.VirtualMachine], True)
        vm_list = vm_view.view
        vm_view.Destroy()

        # Print information about each virtual machine
        print()
        print()
        print("-----------------------")
        i = 1
        for vm in vm_list:
            print(f"--- {i} ---")
            print(f"Name: {vm.name}")
            print(f"Power state: {vm.summary.runtime.powerState}")
            print(f"Description/Annotation: {vm.summary.config.annotation}")
            print()
            print("--- VM General Details ---")
            print(f"Virtual Machine location: {vm.summary.config.vmPathName}")
            print(f"Guest OS: {vm.summary.guest.guestFullName}")
            print(f"Virtual hardware version: {vm.config.version}")
            print()
            print("-- VMware Tools --")
            if vm.summary.guest is not None:
                if vm.summary.guest.toolsRunningStatus is not None:
                    print(f"VMware Tools status: {vm.summary.guest.toolsRunningStatus}")
                else:
                    print(f"VMware Tools status: Unknown")
                if vm.summary.guest.toolsVersionStatus2 is not None:
                    print(f"VMware Tools version: {vm.summary.guest.toolsVersionStatus2}")
                else:
                    print(f"VMware Tools version: Unknown")
            else:
                print("Unable to gather VM Tools Details")
            print()
            print("--- VM vHardware Details ---")
            # Print the virtual machine's vNIC, vSwitch, vCPU, vMem, and vDisk details
            print(f"vNICs:")
            for device in vm.config.hardware.device:
                if isinstance(device, vim.vm.device.VirtualEthernetCard):
                    print(f"{device.deviceInfo.label}: {device.deviceInfo.summary}")
            print()
            print(f"vSwitches:")
            for device in vm.config.hardware.device:
                if isinstance(device, vim.vm.device.VirtualEthernetCard):
                    if hasattr(device.backing, 'port'):
                        print(f"{device.deviceInfo.label}: {device.backing.port.portgroupKey}")
                    else:
                        print(f"{device.deviceInfo.label}: Not connected to a vSwitch")
            print()
            print(f"vCPUs: {vm.config.hardware.numCPU}")
            print()
            print(f"vMem: {vm.config.hardware.memoryMB} MB")
            print()
            print(f"vDisks:")
            for device in vm.config.hardware.device:
                if isinstance(device, vim.vm.device.VirtualDisk):
                    print(f"Name: {device.deviceInfo.label}")
                    print(f"Datastore - {device.backing.datastore}")
                    print(f"Capacity - {device.capacityInBytes} Bytes")
                    print(f"Thin Provisioned? - {device.backing.thinProvisioned}")
                    print(f"vDisk Split? - {device.backing.split}")
                    print(f"Write Through Enabled? - {device.backing.writeThrough}")
                    print(f"Disk Mode - {device.backing.diskMode}")
            print("-----------------------")
            i = i + 1
        print()
        Disconnect(si)
    except vim.fault.InvalidLogin as e:
        print(e)
        print()
        print("Incorrect Username or Password. Please try again.")
    except Exception as f:
        print(f)
        print()
        print("Contact script dev with exception details for better error handling")


def list_files(server, username, password):
    # Connect to the remote system using SCP or SFTP
    print("Enter the protocol to use (scp or sftp):")
    protocol = input()
    directory = "/var/log/"
    try:
        # Connect to the ESXi host using SSH
        print(f"Connecting to {server} via SSH. Standby.")
        ssh.connect(hostname=server, username=username, password=password)
        print(f"Connected to {server}.")
    except paramiko.ssh_exception.AuthenticationException:
        print(f"Failed to connect to {server}. Authentication failed.")
        print("Check the credentials entered when the script was started.")
        print("Exiting...")
        exit()
    if protocol == 'scp':
        scp = paramiko.SFTPClient.from_transport(ssh.get_transport())
    elif protocol == 'sftp':
        sftp = ssh.open_sftp()

    # List the files in the specified directory
    file_list = []
    if protocol == 'scp':
        file_list = scp.listdir(directory)
    elif protocol == 'sftp':
        file_list = sftp.listdir(directory)

    # Print the list of files
    print("Files:")
    for i, file in enumerate(file_list):
        print(f"{i + 1}. {file}")
    print()

    # Prompt the user to select the files to download
    while True:
        print("Enter the numbers of the files to download, separated by spaces (or enter 'q' to quit):")
        choices = input()
        try:
            verify = input(f"Are you sure you want files {choices}? (Y/n/q):").lower
            if verify == "y":
                continue
            elif verify == "n":
                choices = input("Please re-enter the numbers of the files to download.")
                continue
            elif verify == "q":
                break
        except Exception as a:
            print(a)
            exit()
        if choices == 'q':
            break

        # Parse the user's choices
        try:
            choices = [int(c) for c in choices.split()]
        except ValueError:
            print("Invalid input. Please try again.")
            continue

        # Download the selected files
        for i, file in enumerate(file_list):
            fname = str(file)
            destination = os.path.join(os.path.expanduser('~'), 'Downloads/' + server + '_'
                                       + timestr + '_' + fname)
            if i + 1 in choices:
                if protocol == 'scp':
                    scp.get(os.path.join(directory, file), localpath=destination)
                elif protocol == 'sftp':
                    sftp.get(os.path.join(directory, file), localpath=destination)
                print(f"{file} downloaded.")
                print()
        break
    ssh.close()


def esxihc(server, username, password):
    print(f"Gathering Health Check Output From {server}. Please standby.")
    try:
        # Connect to the ESXi host using SSH
        print(f"Connecting to {server} via SSH. Standby.")
        ssh.connect(hostname=server, username=username, password=password)
        print(f"Connected to {server}.")
    except paramiko.ssh_exception.AuthenticationException:
        print(f"Failed to connect to {server}. Authentication failed.")
        print("Check the credentials entered when the script was started.")
        print("Exiting...")
        exit()

    # Open the file in append mode
    with open(os.path.join(os.path.expanduser('~'), 'Downloads/' + server + '_'
                           + timestr + '_' + 'HealthCheck.txt'), 'a') as f:
        f.write(f"--- {server} ESXi Health Checks @ {timestr} ---\n\n")
        f.write("\n")
        # Execute each command and write the output to the file
        for command in ['esxcli system hostname get', 'esxcli system version get', 'vim-cmd vimsvc/license --show',
                        'esxcfg-scsidevs -l | egrep -i "display name|vendor"', 'vim-cmd vmsvc/getallvms',
                        'esxcfg-vmknic -l', 'esxcli hardware platform get', 'esxcli hardware cpu global get',
                        'esxcli hardware memory get', 'esxcli hardware clock get', 'esxcli system time get',
                        'esxcli vm process list', 'esxcli network vm list', 'esxcli network vswitch standard list',
                        'esxcli storage vmfs extent list', 'esxcli storage filesystem list',
                        'esxcli storage vmfs snapshot list', 'esxcli storage core adapter list',
                        'esxcli storage core device list', 'esxcli system boot device get',
                        'esxcfg-advcfg -j iovDisableIR', 'cat /etc/chkconfig.db',
                        'vmkload_mod -s megaraid_sas | grep Version', 'vmkload_mod -s igb | grep Version',
                        'vmkload_mod -s fnic', 'vmkload_mod -s enic', 'vim-cmd hostsvc/hostsummary']:
            stdin, stdout, stderr = ssh.exec_command(command)
            output = stdout.read().decode('utf-8')
            print(f"Gathering output from command {command}...")
            f.write(f"- {command} -\n")
            f.write(output)
            f.write("\n\n")
    print(f"--- Finished ---")
    print(f"Output has been collected and stored in {f.name} for review and backup.")
    ssh.close()
    print(f"To run another Health Check, please restart the script.")


def vmsnapshot(server, username, password, port):
    while True:
        # Connect to the ESXi host
        si = SmartConnect(host=server, user=username, pwd=password, port=port, sslContext=context)

        # Get the list of virtual machines on the host
        vm_list = si.content.viewManager.CreateContainerView(si.content.rootFolder,
                                                         [vim.VirtualMachine], True)
        vm_names = [vm.name for vm in vm_list.view]

        # Print the list of virtual machines and prompt the user to select one
        print("Virtual machines on host:")
        for i, vm_name in enumerate(vm_names):
            print(f"{i + 1}: {vm_name}")
        selected_vm_index = int(input("Enter the number of the virtual machine to snapshot: ")) - 1
        selected_vm = vm_list.view[selected_vm_index]

        # Perform a snapshot on the selected virtual machine
        snapshot_task = selected_vm.CreateSnapshot_Task(name="Snapshot", description="Snapshot of VM", memory=False,
                                                        quiesce=False)
        snapshot_task.wait()
        print(f"Snapshot complete for Virtual Machine {selected_vm}!")

        doagain = input("Do you want to take another snapshot? (y/N)").lower
        if doagain == 'y':
            continue
        else:
            break

    # Disconnect from the ESXi host
    Disconnect(si)


def configbackup(server, username, password):
    try:
        # Connect to the ESXi host using SSH
        print(f"Connecting to {server} via SSH. Standby.")
        ssh.connect(hostname=server, username=username, password=password)
        print(f"Connected to {server}.")
    except paramiko.ssh_exception.AuthenticationException:
        print(f"Failed to connect to {server}. Authentication failed.")
        print("Check the credentials entered when the script was started.")
        print("Exiting...")
        exit()

    # Issue the "vim-cmd hostsvc/firmware/sync_config" command
    print("Issuing Config Sync...")
    stdin, stdout, stderr = ssh.exec_command('vim-cmd hostsvc/firmware/sync_config')
    print("Config Synced!")

    # Issue the "vim-cmd hostsvc/firmware/backup_config" command
    print("Issuing Config Backup...")
    stdin, stdout, stderr = ssh.exec_command('vim-cmd hostsvc/firmware/backup_config')
    print("Config Backup Completed!")
    output = stdout.read().decode()

    # Find the URL in the output
    url_pattern = r'http://[^/]*/downloads/[^\s]+'
    url_match = re.search(url_pattern, output)

    if url_match is None:
        print("URL Match did not work.")
        print(f"Search Pattern: {url_pattern}")
        print(f"Output Searched: {output}")
        print(f"RE Search Result: {url_match}")
        print("Please provide the above output to the script dev to review and address.")
        quit()
    elif url_match:
        # Extract the URL
        url = url_match.group(0)

        # Perform the substitution to replace "*" with the hostname
        url = url.replace('*', server)

        # Download the file at the URL
        print(f"Downloading configBundle from {server}...")
        r = requests.get(url, verify=False)

        # Save the file to the current directory
        print("Writing file locally...")
        with open(os.path.join(os.path.expanduser('~'), 'Downloads/' + server + '_'
                                                        + timestr + '_' + 'configBundle.tgz'), 'wb+') as f:
            f.write(r.content)

    # Close the SSH connection
    print(f"Disconnecting from {server}")
    ssh.close()


# Main function
def main():
    server, username, password, port = cred_collect()
    while True:
        # Display the menu
        print("Select an option:")
        print("-----------------")
        print("1. List VMs & Details")
        print("2. List And Download Log Files")
        print("3. Collect ESXi HealthCheck")
        print("4. Perform a VM Snapshot (UNTESTED)")
        print("5. Perform an ESXi Config Backup")
        print("6. Quit")
        print("-----------------")
        print()
        choice = input("Choice: ")

        # Call the selected function
        if choice == '1':
            list_vms(server, username, password, port)
        elif choice == '2':
            list_files(server, username, password)
        elif choice == '3':
            esxihc(server, username, password)
        elif choice == '4':
            vmsnapshot(server, username, password, port)
        elif choice == '5':
            configbackup(server, username, password)
        elif choice == '6':
            exit()
        else:
            print("Invalid choice. Please try again.")
        print()


# Run the main function
if __name__ == "__main__":
    main()
