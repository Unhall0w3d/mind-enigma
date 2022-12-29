# Import the necessary libraries
import os
import paramiko
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim


def list_vms():
    # Connect to the vSphere server
    print("Enter the vSphere server hostname:")
    server = input()
    print("Enter the vSphere server username:")
    username = input()
    print("Enter the vSphere server password:")
    password = input()
    si = SmartConnect(host=server, user=username, pwd=password, port=443)

    # Retrieve a list of all virtual machines in the vSphere environment
    vm_view = si.content.viewManager.CreateContainerView(si.content.rootFolder, [vim.VirtualMachine], True)
    vm_list = vm_view.view
    vm_view.Destroy()

    # Print information about each virtual machine
    for vm in vm_list:
        print(f"Name: {vm.name}")
        print(f"Description: {vm.summary.config.annotation}")
        print(f".vmx file location: {vm.summary.config.vmPathName}")
        if vm.summary.guest is not None:
            if vm.summary.guest.toolsRunningStatus is not None:
                print(f"VMware Tools status: {vm.summary.guest.toolsRunningStatus}")
            else:
                print(f"VMware Tools status: Unknown")
            if vm.summary.guest.toolsVersionStatus2 is not None:
                print(f"VMware Tools version: {vm.summary.guest.toolsVersionStatus2}")
            else:
                print(f"VMware Tools version: Unknown")
        print()


def list_files():
    # Connect to the remote system using SCP or SFTP
    print("Enter the protocol to use (scp or sftp):")
    protocol = input()
    print("Enter the hostname of the remote system:")
    hostname = input()
    print("Enter the username to use to connect to the remote system:")
    hostuser = input()
    print("Enter the password to use to connect to the remote system:")
    hostpassword = input()
    print("Enter the directory on the remote system to list files from:")
    directory = input()
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username=hostuser, password=hostpassword)
    if protocol == 'scp':
        scp = paramiko.SFTPClient.from_transport(client.get_transport())
    elif protocol == 'sftp':
        sftp = client.open_sftp()

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
        if choices == 'q':
            break

        # Parse the user's choices
        try:
            choices = [int(c) for c in choices.split()]
        except ValueError:
            print("Invalid input. Please try again.")
            continue

        # Download the selected files
        print("Enter the local directory to download files to:")
        destination = input()
        for i, file in enumerate(file_list):
            if i + 1 in choices:
                if protocol == 'scp':
                    scp.get(os.path.join(directory, file), local_path=destination)
                elif protocol == 'sftp':
                    sftp.get(os.path.join(directory, file), local_path=destination)
                print(f"{file} downloaded.")
                print()


def generate_tech_support_file():
    # Connect to the vSphere server
    print("Enter the vSphere server hostname:")
    server = input()
    print("Enter the vSphere server username:")
    username = input()
    print("Enter the vSphere server password:")
    password = input()
    si = SmartConnect(host=server, user=username, pwd=password)

    # Generate the Tech Support file
    print("Enter the directory to save the Tech Support file to:")
    directory = input()
    file_name = si.content.sessionManager.RequestTechSupport(directory)
    print(f"Tech Support file saved as {file_name}.")

    # Download the Tech Support file
    print("Enter the local directory to download the Tech Support file to:")
    destination = input()
    print("Enter the protocol to use (scp or sftp):")
    protocol = input()
    print("Enter the hostname of the vSphere server:")
    hostname = input()
    print("Enter the username to use to connect to the vSphere server:")
    hostuser = input()
    print("Enter the password to use to connect to the vSphere server:")
    hostpassword = input()
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username=hostuser, password=hostpassword)
    if protocol == 'scp':
        scp = paramiko.SFTPClient.from_transport(client.get_transport())
    elif protocol == 'sftp':
        sftp = client.open_sftp()
    if protocol == 'scp':
        scp.get(os.path.join(directory, file_name), local_path=destination)
    elif protocol == 'sftp':
        sftp.get(os.path.join(directory, file_name), local_path=destination)
    print(f"Tech Support file downloaded to {destination}.")


while True:
    # Display the menu
    print("Menu:")
    print("1. List virtual machines")
    print("2. List and download files")
    print("3. Generate and download Tech Support file")
    print("4. Quit")

    # Prompt the user to select an option
    print("Enter your choice:")
    choice = input()

    # Perform the selected option
    if choice == '1':
        list_vms()
    elif choice == '2':
        list_files()
    elif choice == '3':
        generate_tech_support_file()
    elif choice == '4':
        break