#!/usr/var/python
# -*- code:UTF-8 -*-

#####################################
# Script created by Ken Perry, 2022 #
#       NOC THOUGHTS BLOG           #
#    https://www.nocthoughts.com    #
#####################################

# to do
# Test "VM Snapshot" option.
# Add "Take an ESXI Backup"
# Check VM Power States, Prompt to Shut Off Gracefully, Prompt for Maint Mode Y

# Import modules
import os
import paramiko
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import time
from getpass import getpass

# Define current time
timestr = time.strftime("%Y%m%d-%H%M%S")

# Paramiko ssh connection details
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.load_system_host_keys()

def cred_collect():
    # Collect login details for ESXi
    print("Enter the vSphere server hostname:")
    server = input()
    print("Enter the vSphere server username:")
    username = input()
    print("Enter the vSphere server password:")
    password = getpass()
    return server, username, password


def list_vms(server, username, password):
    # Connect and collect vm details
    try:
        si = SmartConnect(host=server, user=username, pwd=password, port=443)

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
                    print(f"{device.deviceInfo.label}: {device.capacityInKB} KB")
            print("-----------------------")
            i = i + 1
        print()
        Disconnect(si)
        while True:
            menuprompt = input("Return to Menu? [Y(es)/Q(uit)]: ")
            if menuprompt == "Y":
                print("Returning to menu...")
                print()
                break
            elif menuprompt == "Q":
                exit()
            else:
                print("Invalid choice. Please try again.")
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
    ssh.connect(server, username=username, password=password)
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
    # Connect to the ESXi host
    ssh.connect(server, username=username, password=password)

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
                        'vmkload_mod -s fnic', 'vmkload_mod -s enic']:
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


def vmsnapshot(server, username, password):
    while True:
        # Connect to the ESXi host
        si = SmartConnect(host=server, user=username, pwd=password, port=443)

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

# Main function
def main():
    server, username, password = cred_collect()
    while True:
        # Display the menu
        print()
        print("Select an option:")
        print("-----------------")
        print("1. List Virtual Machines")
        print("2. List And Download Files")
        print("3. Run ESXi HealthCheck")
        print("4. Perform a VM Snapshot (UNTESTED)")
        print("5. Quit")
        print("-----------------")
        print()
        choice = input("Choice: ")

        # Call the selected function
        if choice == '1':
            list_vms(server, username, password)
        elif choice == '2':
            list_files(server, username, password)
        elif choice == '3':
            esxihc(server, username, password)
        elif choice == '4':
            vmsnapshot(server, username, password)
        elif choice == '5':
            exit()
        else:
            print("Invalid choice. Please try again.")
        print()


# Run the main function
if __name__ == "__main__":
    main()
