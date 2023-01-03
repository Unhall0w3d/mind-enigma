#!/usr/var/python
# -*- code:UTF-8 -*-

#####################################
# Script created by Ken Perry, 2022 #
#       NOC THOUGHTS BLOG           #
#    https://www.nocthoughts.com    #
#####################################

# to do
# Test VM Snapshot "API" option. Failed in testing due to insufficient licensing on ESXi.

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


class ESXi:
    def __init__(self):
        # SSL
        # Ignore SSL certificate warnings
        self.context = ssl.create_default_context()
        # Disable hostname checking
        self.context.check_hostname = False
        # Disable SSL Verification
        self.context.verify_mode = ssl.CERT_NONE

        # SSH
        # Create a new SSH client
        self.ssh = paramiko.SSHClient()
        # Set the missing host key policy to "AutoAddPolicy"
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # Load existing set of host keys
        self.ssh.load_system_host_keys()

        # HTTPs
        # Disable HTTPS Insecure Request error message
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Collect login details for ESXi
        self.server = input("Enter the vSphere server hostname: ")
        self.port = int(input("Enter the Port Forward port number, or 443: "))
        self.username = input("Enter the vSphere server username: ")
        self.password = input("Enter the vSphere server password: ")
        print()

        # Set login parameters for failed login tracking and max attempts
        self.failed_login = 0
        self.max_attempts = 2

        # Connect on port 22 & 443
        self.si = self.httpsconn()
        self.sshconn = self.sshconn()

    def httpsconn(self):
        try:
            print(f"Connecting to {self.server} via HTTPS/{self.port}...")
            si = SmartConnect(host=self.server, user=self.username, pwd=self.password, port=self.port,
                              sslContext=self.context)
            print(f"Connected to {self.server} on port {self.port}")
            return si
        except vim.fault.InvalidLogin:
            self.failed_login += 1
            if self.failed_login < self.max_attempts:
                print(f"Failed to connect to {self.server}. Authentication failed.")
                print(f"Let's confirm the credentials for {self.server} are correct.")
                self.username = input("Enter the vSphere server username: ")
                self.password = getpass("Enter the vSphere server password: ")
            else:
                print("Max login attempts exceeded")
                exit()

    def sshconn(self):
        try:
            # Connect to the ESXi host using SSH
            print(f"Connecting to {self.server} via SSH/22...")
            self.ssh.connect(hostname=self.server, username=self.username, password=self.password)
            print(f"Connected to {self.server}.")
            return self.ssh
        except paramiko.ssh_exception.AuthenticationException:
            print(f"Failed to connect to {self.server}. Authentication failed.")
            print("Check the credentials entered when the script was started.")
            print("Exiting...")
            Disconnect(self.si)
            exit()
        except TimeoutError:
            print(f"Failed to connect to host {self.server} due to Connection Timeout.")
            print(f"Please ensure that {self.server} is reachable.")
            Disconnect(self.si)
            exit()
        except paramiko.ssh_exception.NoValidConnectionsError as f:
            print(f"Failed to connect to {self.server} due to {f}.")
            print(f"Please ensure the TSM/TSM-SSH Services are started on {self.server}.")
            Disconnect(self.si)
            exit()

    # Function to list virtual machines and useful details
    def list_vms(self):
        # Retrieve a list of all virtual machines in the vSphere environment
        vm_view = self.si.content.viewManager.CreateContainerView(self.si.content.rootFolder,
                                                                        [vim.VirtualMachine],
                                                                        True)
        vm_list = vm_view.view
        vm_view.Destroy()

        host_view = self.si.content.viewManager.CreateContainerView(self.si.content.rootFolder, [vim.HostSystem], True)
        host_list = host_view.view
        host_view.Destroy()

        # Find the host that we want to manage
        for h in host_list:
            host = h
            break
        print(host.runtime.healthSystemRuntime.hardwareStatusInfo.memoryStatusInfo)
        print(host.runtime.healthSystemRuntime.hardwareStatusInfo.cpuStatusInfo)
        print(host.runtime.healthSystemRuntime.hardwareStatusInfo.storageStatusInfo)
        exit()
        # Print information about each virtual machine
        print(f"Performing data pull for device {self.server}. Please wait...")
        with open(os.path.join(os.path.expanduser('~'),
                               'Downloads/' + self.server + '_' + timestr + '_' + 'VMDetails.txt'),
                  'w+') as f:
            for vm in vm_list:
                f.write(f"--- ESXi Report for {host.name} ---\n")
                f.write(f"Power state: {host.runtime.powerState}\n")
                f.write(f"Connection State: {host.runtime.connectionState}\n")
                f.write(f"Maintenance Mode: {host.runtime.inMaintenanceMode}\n")
                f.write(f"Boot Time: {host.runtime.bootTime}\n")
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
        time.sleep(4)
        print()

    # Function to list and allow download of log files in /var/log/
    def list_files(self):
        # Connect to the remote system using SCP or SFTP
        print("Enter the protocol to use (scp or sftp):")
        protocol = input().lower()
        directory = "/var/log/"

        # List the files in the specified directory
        file_list = []

        # Set up SCP or SFTP connection
        if protocol == 'scp':
            scp = paramiko.SFTPClient.from_transport(self.ssh.get_transport())
            file_list = scp.listdir(directory)
        elif protocol == 'sftp':
            sftp = self.ssh.open_sftp()
            file_list = sftp.listdir(directory)

        # Print the list of files
        print("Files:")
        for i, file in enumerate(file_list):
            print(f"{i + 1}. {file}")
        print()

        # Prompt the user to select the files to download
        while True:
            choices = input("Enter the numbers of the files to download, "
                            "separated by spaces (or enter 'q' to quit): ").lower()
            if choices == "q":
                break
            else:
                try:
                    verify = input(f"Are you sure you want files {choices}? (Y/n):").lower()
                    if verify == "n":
                        choices = input("Please re-enter the numbers of the files to download.")
                except Exception as a:
                    print(a)
                    self.ssh.close()
                    exit()

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

    # Function to perform health check data collection
    def esxihc(self):
        print(f"Gathering Health Check Output From {self.server}. Please standby.")

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
                stdin, stdout, stderr = self.ssh.exec_command(command)
                output = stdout.read().decode('utf-8')
                print(f"Gathering output from command {command}...")
                f.write(f"- {command} -\n")
                f.write(output)
                f.write("\n\n")
        print(f"--- Finished ---")
        print(f"Output has been collected and stored in {f.name} for review and backup.")

    def vmsnapshot(self):
        while True:
            vm_list = self.si.content.viewManager.CreateContainerView(self.si.content.rootFolder,
                                                                            [vim.VirtualMachine], True)
            vm_names = [vm.name for vm in vm_list.view]

            # Print the list of virtual machines and prompt the user to select one
            print("Virtual machines on host:")
            for i, vm_name in enumerate(vm_names):
                print(f"{i + 1}: {vm_name}")
            selected_vm_index = int(input("Enter the number of the virtual machine to snapshot: ")) - 1
            selected_vm = vm_list.view[selected_vm_index]

            # Collect snapshot name, description, memory dump, and fs quiesce
            name = input("Please enter a name for the snapshot: ")
            description = input("Please provide a description for the snapshot: ")
            memory = input("Do you want to include a memory dump in the snapshot? (y/N): ")
            if memory == "y":
                memory = True
            else:
                memory = False
            quiesce = input("Do you want to enable file system quiesce? (y/N): ")
            if quiesce == "y":
                quiesce = True
            else:
                quiesce = False
            # Perform a snapshot on the selected virtual machine
            snapshot_task = selected_vm.CreateSnapshot_Task(name=name, description=description, memory=memory,
                                                            quiesce=quiesce)
            print(f"Snapshot complete for Virtual Machine {selected_vm.name}!")

            doagain = input("Do you want to take another snapshot? (y/N)").lower()
            if doagain == 'y':
                continue
            else:
                break

    # Function to perform a configuration sync, backup and download locally
    def configbackup(self):
        # Issue the "vim-cmd hostsvc/firmware/sync_config" command
        print("Issuing Config Sync...")
        stdin, stdout, stderr = self.ssh.exec_command('vim-cmd hostsvc/firmware/sync_config')
        print("Config Synced!")

        # Issue the "vim-cmd hostsvc/firmware/backup_config" command
        print("Issuing Config Backup...")
        stdin, stdout, stderr = self.ssh.exec_command('vim-cmd hostsvc/firmware/backup_config')
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
            self.ssh.close()
            Disconnect(self.si)
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

    def vmpower(self):
        vm_view = self.si.content.viewManager.CreateContainerView(self.si.content.rootFolder,
                                                                  [vim.VirtualMachine],
                                                                  True)
        vm_list = vm_view.view
        vm_view.Destroy()
        # Get a list of all the VMs on the host
        vms = self.si.content.rootFolder.childEntity[0].vmFolder.childEntity

        # Print the name and power state of each VM
        vm_dict = {}
        vmid = []
        print(f"Reporting VMs on {self.server}.")
        print(f"-------------------------------")
        for i, vm in enumerate(vms):
            vm_dict[i] = vm
            print(f"{i} - {vm.summary.config.name}: {vm.summary.runtime.powerState}")
            if vm.summary.guest.toolsRunningStatus is not None:
                runstate = vm.summary.guest.toolsRunningStatus
                if runstate != "guestToolsRunning":
                    print(f"Virtual Machine {vm.summary.config.name} is showing a VMTools status of {runstate}.")
                    print(f"As such, the script cannot manipulate the power state on VM {vm.summary.config.name}.")
                    vmid.append(i)
        while True:
            try:
                # Prompt the user to select a VM
                print(vmid)
                selection = int(input("Select a VM by number, or (q)uit: "))
                if selection in vmid:
                    print(f"You cannot perform a power action on {vm.summary.config.name}.")
                    continue
                else:
                    vm = vm_dict[selection]
                    # Get the current power state of the VM
                    power_state = vm.summary.runtime.powerState
                    print(f"The power state for selection {selection} is {power_state}.")
                    if power_state == "poweredOn":
                        verify = input(f"Do you want to proceed with powering off VM {selection}? (y/n): ").lower()
                        if verify == "y":
                            # Power off the VM
                            vm.PowerOff()
                            print(f"VM {selection} powered off")
                            print("Giving time for task to complete... standby...")
                            time.sleep(60)
                            print("Verifying VM power states...")
                            # Get a list of all the VMs on the host
                            vms = self.si.content.rootFolder.childEntity[0].vmFolder.childEntity

                            # Print the name and power state of each VM
                            vm_dict = {}
                            print(f"Reporting VMs on {self.server}.")
                            print(f"-------------------------------")
                            for i, vm in enumerate(vms):
                                summary = vm.summary
                                vm_dict[i] = vm
                                print(f"{i} - {summary.config.name}: {summary.runtime.powerState}")
                            print("--------------------------------")
                            print("Please verify the VM Power State matches the desired state.")
                            print("Some VMs take longer than others, check the vSphere Web Page if concerned.")
                            print("Returning to menu...")
                            time.sleep(5)
                            break
                        else:
                            print("Returning to menu...")
                            break
                    else:
                        verify = input(f"Do you want to proceed with powering on VM {selection}? (y/n): ").lower()
                        if verify == "y":
                            # Power on the VM
                            vm.PowerOn()
                            print(f"VM {selection} powered on.")
                            print("Giving time for task to complete... standby...")
                            time.sleep(60)
                            print("Verifying VM power states...")
                            # Get a list of all the VMs on the host
                            vms = self.si.content.rootFolder.childEntity[0].vmFolder.childEntity

                            # Print the name and power state of each VM
                            vm_dict = {}
                            print(f"Reporting VMs on {self.server}.")
                            print(f"-------------------------------")
                            for i, vm in enumerate(vms):
                                summary = vm.summary
                                vm_dict[i] = vm
                                print(f"{i} - {summary.config.name}: {summary.runtime.powerState}")
                            print("--------------------------------")
                            print("Please verify the VM Power State matches the desired state.")
                            print("Some VMs take longer than others, check the vSphere Web Page if concerned.")
                            print("Returning to menu...")
                            time.sleep(5)
                            break
                        else:
                            break
            except ValueError:
                print("Returning to menu...")
                time.sleep(1)
                break

    # Function to check status of maint mode, enable/disable, and recheck status
    def maintmode(self):
        vm_view = self.si.content.viewManager.CreateContainerView(self.si.content.rootFolder, [vim.HostSystem], True)
        vm_list = vm_view.view
        vm_view.Destroy()

        # Find the host that we want to manage
        for h in vm_list:
            host = h
            break

        # Check the current state of Maintenance Mode
        if host.runtime.inMaintenanceMode:
            print(f"Maintenance Mode is currently enabled on {self.server}.")
            opt = input("Do you want to disable Maintenance Mode? (y/n): ")
            if opt == 'y':
                opt = input(f"Are you sure you want to disable Maintenance Mode on {self.server}? (y/n): ")
                if opt == 'y':
                    host.ExitMaintenanceMode(timeout=0)
                    print(f"Exiting Maintenance Mode on {self.server}")
                    time.sleep(2)
                else:
                    print(f"Maintenance Mode will remain enabled on {self.server}")
                    time.sleep(1)
            else:
                print(f"Maintenance Mode will remain enabled on {self.server}")
                time.sleep(1)
        else:
            print(f"Maintenance Mode is currently disabled on {self.server}")
            opt = input("Do you want to enable Maintenance Mode? (y/n): ")
            if opt == 'y':
                opt = input(f"Are you sure you want to enable Maintenance Mode on {self.server}? (y/n): ")
                if opt == 'y':
                    host.EnterMaintenanceMode(timeout=0)
                    print(f"Entering Maintenance Mode on {self.server}")
                    time.sleep(2)
                else:
                    print(f"Maintenance Mode will remain disabled {self.server}")
                    time.sleep(1)
            else:
                print(f"Maintenance Mode will remain disabled {self.server}")
                time.sleep(1)


# Run the main function
if __name__ == "__main__":
    ESXi = ESXi()
    while True:
        # Display the menu
        print()
        print()
        print("Select an option:")
        print("-----------------")
        print("1. List VMs & Details")
        print("2. List And Download Log Files")
        print("3. Collect ESXi HealthCheck")
        print("4. Perform a VM Snapshot")
        print("5. Perform an ESXi Config Backup")
        print("6. Power Off/On VM")
        print("7. Enable/Disable Maintenance Mode")
        print("8. Quit")
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
            ESXi.configbackup()
        elif choice == '6':
            ESXi.vmpower()
        elif choice == '7':
            ESXi.maintmode()
        elif choice == '8':
            ESXi.ssh.close()
            Disconnect(ESXi.si)
            exit()
        else:
            print("Invalid choice. Please try again.")
        print()
