#!/usr/var/python
# -*- code:UTF-8 -*-

#####################################
# Script created by Ken Perry, 2022 #
#       NOC THOUGHTS BLOG           #
#    https://www.nocthoughts.com    #
#####################################

# to do
# Test "VM Snapshot" option. Failed in testing due to insufficient licensing on ESXi.
# Add Main Menu option Enable or Disable maintenance mode.

# Import modules
import os
import re
import ssl
import time
from getpass import getpass

import paramiko
import requests
import urllib3
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

# Define current time
timestr = time.strftime("%d-%m-%Y_%H-%M-%S")

# SSH
# Create a new SSH client
ssh = paramiko.SSHClient()
# Set the missing host key policy to "AutoAddPolicy"
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
# Load existing set of host keys
ssh.load_system_host_keys()

# SSL
# Ignore SSL certificate warnings
context = ssl.create_default_context()
# Disable hostname checking
context.check_hostname = False
# Disable SSL Verification
context.verify_mode = ssl.CERT_NONE

# HTTPs
# Disable HTTPS Insecure Request error message
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ESXi:
    def __init__(self):
        # Collect login details for ESXi
        print("Enter the vSphere server hostname:")
        self.server = input()
        print("Enter the Port Forward port number, or 443:")
        self.port = int(input())
        print("Enter the vSphere server username:")
        self.username = input()
        print("Enter the vSphere server password:")
        self.password = getpass()

    # Function to list virtual machines and useful details
    def list_vms(self):
        try:
            print(f"Attempting to connect to {self.server} on port {self.port}...")
            si = SmartConnect(host=self.server, user=self.username, pwd=self.password, port=self.port,
                              sslContext=context)

            # Retrieve a list of all virtual machines in the vSphere environment
            vm_view = si.content.viewManager.CreateContainerView(si.content.rootFolder, [vim.VirtualMachine], True)
            vm_list = vm_view.view
            vm_view.Destroy()

            # Print information about each virtual machine
            print(f"Performing data pull for device {self.server}. Please wait...")
            with open(os.path.join(os.path.expanduser('~'),
                                   'Downloads/' + self.server + '_' + timestr + '_' + 'VMDetails.txt'),
                      'w+') as f:
                for vm in vm_list:
                    f.write(f"--- VM Report for {vm.name} ---\n")
                    f.write(f"Name: {vm.name}\n")
                    f.write(f"Power state: {vm.summary.runtime.powerState}\n")
                    f.write(f"Description/Annotation: {vm.summary.config.annotation}\n")
                    f.write("\n")
                    f.write("--- VM General Details ---\n")
                    f.write(f"Virtual Machine location: {vm.summary.config.vmPathName}\n")
                    f.write(f"Guest OS: {vm.summary.guest.guestFullName}\n")
                    f.write(f"Virtual hardware version: {vm.config.version}\n")
                    f.write("\n")
                    f.write("-- VMware Tools --\n")
                    if vm.summary.guest is not None:
                        if vm.summary.guest.toolsRunningStatus is not None:
                            f.write(f"VMware Tools status: {vm.summary.guest.toolsRunningStatus}\n")
                        else:
                            f.write(f"VMware Tools status: Unknown\n")
                        if vm.summary.guest.toolsVersionStatus2 is not None:
                            f.write(f"VMware Tools version: {vm.summary.guest.toolsVersionStatus2}\n")
                        else:
                            f.write(f"VMware Tools version: Unknown\n")
                    else:
                        f.write("Unable to gather VM Tools Details\n")
                    f.write("\n")
                    f.write("--- VM vHardware Details ---\n")
                    # Print the virtual machine's vNIC, vSwitch, vCPU, vMem, and vDisk details
                    f.write(f"vNICs:\n")
                    for device in vm.config.hardware.device:
                        if isinstance(device, vim.vm.device.VirtualEthernetCard):
                            f.write(f"Device - {device.deviceInfo.label}\n")
                            f.write(f"Name - {device.deviceInfo.summary}\n")
                            f.write(f"Network - {device.backing.network}\n")
                            if isinstance(device, vim.vm.device.VirtualVmxnet3):
                                f.write(f"MAC Address - {device.macAddress}\n")
                            else:
                                f.write(f"MAC Address - Unknown\n")
                            if isinstance(device, vim.vm.device.VirtualVmxnet3):
                                f.write(f"Connect on Boot - {device.connectable.startConnected}\n")
                                f.write(f"Connected - {device.connectable.connected}\n")
                                f.write(f"Status - {device.connectable.status}\n")
                            else:
                                f.write(f"Connect on Boot - Unknown\n")
                                f.write(f"Connected - Unknown\n")
                                f.write(f"Status - Unknown\n")
                    f.write("\n")
                    f.write(f"vCPU/vMem:\n")
                    f.write(f"Sockets Assigned - {vm.config.hardware.numCPU}\n")
                    f.write(f"Cores per Socket - {vm.config.hardware.numCoresPerSocket}\n")
                    f.write(f"Virtual Memory - {vm.config.hardware.memoryMB} MB\n")
                    f.write("\n")
                    f.write(f"vDisks:\n")
                    for device in vm.config.hardware.device:
                        if isinstance(device, vim.vm.device.VirtualDisk):
                            f.write(f"Name: {device.deviceInfo.label}\n")
                            f.write(f"Datastore - {device.backing.datastore}\n")
                            f.write(f"Capacity - {device.deviceInfo.summary}\n")
                            f.write(f"Thin Provisioned? - {device.backing.thinProvisioned}\n")
                            f.write(f"vDisk Split? - {device.backing.split}\n")
                            f.write(f"Write Through Enabled? - {device.backing.writeThrough}\n")
                            f.write(f"Disk Mode - {device.backing.diskMode}\n")
                    f.write("-----------------------\n\n\n")
                print(f"Data pull has been completed for device {self.server}.")
                print(f"Output can be found in {f.name}.")
                f.close()
            Disconnect(si)
            print(f"Disconnected from device {self.server}.")
            time.sleep(4)
            print()
        except vim.fault.InvalidLogin as e:
            print(e)
            print(f"Failed to connect to {self.server}. Authentication failed.")
            print("Check the credentials entered when the script was started.")
            print("Exiting...")
        except Exception as f:
            print(f)
            print()
            print("Contact script dev with exception details for better error handling")

    # Function to list and allow download of log files in /var/log/
    def list_files(self):
        # Connect to the remote system using SCP or SFTP
        print("Enter the protocol to use (scp or sftp):")
        protocol = input()
        directory = "/var/log/"
        try:
            # Connect to the ESXi host using SSH
            print(f"Connecting to {self.server} via SSH. Standby.")
            ssh.connect(hostname=self.server, username=self.username, password=self.password)
            print(f"Connected to {self.server}.")
        except paramiko.ssh_exception.AuthenticationException:
            print(f"Failed to connect to {self.server}. Authentication failed.")
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
                destination = os.path.join(os.path.expanduser('~'), 'Downloads/' + self.server + '_'
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

    # Function to perform health check data collection
    def esxihc(self):
        print(f"Gathering Health Check Output From {self.server}. Please standby.")
        try:
            # Connect to the ESXi host using SSH
            print(f"Connecting to {self.server} via SSH. Standby.")
            ssh.connect(hostname=self.server, username=self.username, password=self.password)
            print(f"Connected to {self.server}.")
        except paramiko.ssh_exception.AuthenticationException:
            print(f"Failed to connect to {self.server}. Authentication failed.")
            print("Check the credentials entered when the script was started.")
            print("Exiting...")
            exit()

        # Open the file in append mode
        with open(os.path.join(os.path.expanduser('~'), 'Downloads/' + self.server + '_'
                                                        + timestr + '_' + 'HealthCheck.txt'), 'a') as f:
            f.write(f"--- {self.server} ESXi Health Checks @ {timestr} ---\n\n")
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

    def vmsnapshot(self):
        while True:
            # Connect to the ESXi host
            si = SmartConnect(host=self.server, user=self.username, pwd=self.password, port=self.port,
                              sslContext=context)

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

    # Function to perform a configuration sync, backup and download locally
    def configbackup(self):
        try:
            # Connect to the ESXi host using SSH
            print(f"Connecting to {self.server} via SSH. Standby.")
            ssh.connect()
            print(f"Connected to {self.server}.")
        except paramiko.ssh_exception.AuthenticationException:
            print(f"Failed to connect to {self.server}. Authentication failed.")
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
            url = url.replace('*', self.server)

            # Download the file at the URL
            print(f"Downloading configBundle from {self.server}...")
            r = requests.get(url, verify=False)

            # Save the file to the current directory
            print("Writing file locally...")
            with open(os.path.join(os.path.expanduser('~'), 'Downloads/' + self.server + '_'
                                                            + timestr + '_' + 'configBundle.tgz'), 'wb+') as f:
                f.write(r.content)

        # Close the SSH connection
        print(f"Disconnecting from {self.server}")
        ssh.close()

    # Function to perform a VM snapshot using CLI/SSH
    def clisnapshot(self):
        try:
            # Connect to the ESXi host using SSH
            print(f"Connecting to {self.server} via SSH. Standby.")
            ssh.connect(hostname=self.server, username=self.username, password=self.password)
            print(f"Connected to {self.server}.")
        except paramiko.ssh_exception.AuthenticationException:
            print(f"Failed to connect to {self.server}. Authentication failed.")
            print("Check the credentials entered when the script was started.")
            print("Exiting...")
            exit()

        # Gather VMs and IDs
        stdin, stdout, stderr = ssh.exec_command("vim-cmd vmsvc/getallvms")
        vms = stdout.readlines()
        print("ID\tName")
        for vm in vms:
            print(vm)

        while True:
            # Prompt the user to select a VM
            vm_id = input("Enter the ID of the VM to snapshot: ")
            snapshot_name = input("Enter the name of the VM snapshot: ")
            verify = input(f"Are you sure you want to snapshot VM {vm_id}?").lower()
            if verify == 'y':
                # Run snapshot against relevant VM
                cmd = "vim-cmd vmsvc/snapshot.create %s %s" % (vm_id, snapshot_name)
                stdin, stdout, stderr = ssh.exec_command(cmd)
                print(stdout.read())
                verify = input("Would you like to perform another snapshot?").lower()
                if verify == 'y':
                    continue
                else:
                    break
            else:
                break
        ssh.close()

        # Function to get a list of all virtual machines and their power state

    def getvms(self):
        try:
            # Connect to the ESXi host using SSH
            print(f"Connecting to {self.server} via SSH. Standby.")
            ssh.connect(hostname=self.server, username=self.username, password=self.password)
            print(f"Connected to {self.server}.")
        except paramiko.ssh_exception.AuthenticationException:
            print(f"Failed to connect to {self.server}. Authentication failed.")
            print("Check the credentials entered when the script was started.")
            print("Exiting...")
            exit()

        # Execute the "vim-cmd vmsvc/getallvms" command to get a list of all virtual machines and their power state
        stdin, stdout, stderr = ssh.exec_command("vim-cmd vmsvc/getallvms")

        # Read the command output
        output = stdout.readlines()

        # Create a list to store the virtual machines and their power state
        vm_list = []

        # Parse the command output
        for line in output:

            # Split the line into fields
            fields = line.split()

            # Check if the line contains a virtual machine
            if len(fields) == 2:
                # Get the virtual machine ID and name
                vm_id = fields[0]
                vm_name = fields[1]

                # Get the power state of the virtual machine
                stdin, stdout, stderr = ssh.exec_command("vim-cmd vmsvc/power.getstate {}".format(vm_id))
                power_state = stdout.read().strip()

                # Add the virtual machine and its power state to the list
                vm_list.append((vm_id, vm_name, power_state))
        return vm_list

    def vmchoice(self, vm_list):
        print(f"Current VM Status on {self.server}:")
        for vm in vm_list:
            vm_id, vm_name, power_state = vm
            print("ID: {} Name: {} Power state: {}".format(vm_id, vm_name, power_state))
            while True:
                onoroff = input("Do you want to power a VM ON, or OFF? (ON/OFF): ").lower
                if onoroff == "on":
                    vm_id = input("Enter the ID of the virtual machine you want to power on: ")
                    return vm_id, onoroff
                elif onoroff == "off":
                    vm_id = input("Enter the ID of the virtual machine you want to power off: ")
                    proceed = input(f"Are you sure you want to power off VM {vm_id}? (y/n): ").lower
                    if proceed == "y":
                        return vm_id, onoroff
                    else:
                        vm_id == "menu"
                        onoroff == "menu"
                        return vm_id, onoroff

    # Function to power off a virtual machine gracefully
    def power_onoff_vm(self, vm_id, onoroff):
        if onoroff == "on":
            # Execute the "vim-cmd vmsvc/power.shutdown" command to power on the virtual machine gracefully
            stdin, stdout, stderr = ssh.exec_command("vim-cmd vmsvc/power.on {}".format(vm_id))

            # Read the command output
            output = stdout.read().strip()

            # Check if the virtual machine was powered on successfully
            if output == "True":
                print("Virtual machine was powered on successfully.")
            else:
                print("Failed to power on virtual machine.")
                print("Please use the Admin Webpage instead and report issues and error messages to the script dev.")
            time.sleep(5)

        elif onoroff == "off":
            # Execute the "vim-cmd vmsvc/power.shutdown" command to power off the virtual machine gracefully
            stdin, stdout, stderr = ssh.exec_command("vim-cmd vmsvc/power.shutdown {}".format(vm_id))

            # Read the command output
            output = stdout.read().strip()

            # Check if the virtual machine was powered off successfully
            if output == "True":
                print("Virtual machine was powered off successfully.")
            else:
                print("Failed to power off virtual machine.")
                print("Please use the Admin Webpage instead and report issues and error messages to the script dev.")
            time.sleep(5)

    # Quick function to verify VM power state
    def vmpowercheck(self, vm_list):
        print(f"Current VM Status on {self.server}:")
        for vm in vm_list:
            vm_id, vm_name, power_state = vm
            print("ID: {} Name: {} Power state: {}".format(vm_id, vm_name, power_state))
        print()
        print("Please verify that the reported power state (above) matches expected VM power state.")
        print("For any issues, such as VM remaining ON after Power Down, please check the Admin Webpage. ")
        print("Returning to menu...")
        time.sleep(7)

    # Function to check status of maint mode, enable/disable, and recheck status
    def maintmode(self):
        print(f"Attempting to connect to {self.server} on port {self.port}...")
        si = SmartConnect(host=self.server, user=self.username, pwd=self.password, port=self.port,
                              sslContext=context)

        # Get the Maintenance Mode status
        host_system = si.content.rootFolder.childEntity[0]
        if host_system.inMaintenanceMode:
            print(f"The host {self.server} is currently in Maintenance Mode.")
        else:
            print(f"The host {self.server} is not in Maintenance Mode.")

        # Prompt the user to enable or disable Maintenance Mode
        response = input("Would you like to enable or disable Maintenance Mode? (e/d): ")
        if response.lower() == 'e':
            host_system.EnterMaintenanceMode_Task(timeout=0)
            print('Maintenance Mode enabled.')
        else:
            host_system.ExitMaintenanceMode_Task(timeout=0)
            print('Maintenance Mode disabled.')

        # Check the Maintenance Mode status again
        if host_system.inMaintenanceMode:
            print(f"The host {self.server} is currently in Maintenance Mode.")
        else:
            print(f"The host {self.server} is not in Maintenance Mode.")
        print("Please manually verify maintenance mode is enabled as needed.")
        print("Returning to menu...")
        print()
        time.sleep(3)

    # Main function
    def main(self):
        while True:
            # Display the menu
            print("Select an option:")
            print("-----------------")
            print("1. List VMs & Details")
            print("2. List And Download Log Files")
            print("3. Collect ESXi HealthCheck")
            print("4. Perform a VM Snapshot via API (Testing)")
            print("5. Perform a VM Snapshot via CLI (Testing)")
            print("6. Perform an ESXi Config Backup")
            print("7. Power Off/On VM (Testing)")
            print("8. Enable/Disable Maintenance Mode (Testing)")
            print("9. Quit")
            print("-----------------")
            print()
            choice = input("Choice: ")

            # Call the selected function
            if choice == '1':
                ESXi.list_vms()
            elif choice == '2':
                ESXi.list_files()
            elif choice == '3':
                ESXi.esxihc()
            elif choice == '4':
                ESXi.vmsnapshot()
            elif choice == '5':
                ESXi.clisnapshot()
            elif choice == '6':
                ESXi.configbackup()
            elif choice == '7':
                vm_list = ESXi.getvms()
                vm_id, onoroff = ESXi.vmchoice(vm_list)
                if vm_id != "menu":
                    ESXi.power_onoff_vm(vm_id, onoroff)
                    ESXi.vmpowercheck(vm_list)
            elif choice == '8':
                ESXi.maintmode()
            elif choice == '9':
                exit()
            else:
                print("Invalid choice. Please try again.")
            print()


# Run the main function
if __name__ == "__main__":
    ESXi = ESXi()
    ESXi.main()
