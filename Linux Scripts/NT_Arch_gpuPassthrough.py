#!/usr/bin/env python3

import os
import subprocess


def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = process.communicate()
    return stdout.decode('utf-8'), stderr.decode('utf-8'), process.returncode


def run_command_interactive(command):
    process = subprocess.run(command, shell=True)
    return process.returncode


def check_virtualization_enabled():
    stdout, _, _ = run_command('dmesg | grep -E "VT-d|AMD-Vi"')
    if 'VT-d' in stdout or 'AMD-Vi' in stdout:
        return True
    return False


def get_bootloader_and_cpu():
    stdout, _, _ = run_command('bootctl')
    bootloader = 'systemd' if 'systemd-boot' in stdout else 'grub'

    stdout, _, _ = run_command('lscpu')
    cpu = 'intel' if 'Intel' in stdout else 'amd'

    return bootloader, cpu


def install_packages():
    packages = 'qemu ovmf virt-manager virt-viewer dnsmasq vde2 bridge-utils openbsd-netcat'
    stdout, stderr, returncode = run_command(f'pacman -Syu --needed --noconfirm {packages}')
    if returncode != 0:
        print(f'Error installing packages: {stderr}')
        return False
    return True


def enable_iommu(bootloader, cpu):
    if bootloader == 'grub':
        grub_config = '/etc/default/grub'
        with open(grub_config, 'r') as file:
            lines = file.readlines()

        iommu_enabled = False
        for index, line in enumerate(lines):
            if line.startswith('GRUB_CMDLINE_LINUX_DEFAULT'):
                if cpu == 'intel':
                    iommu_option = 'intel_iommu=on'
                else:
                    iommu_option = 'amd_iommu=on'

                if iommu_option not in line:
                    lines[index] = line.rstrip()[:-1] + f' {iommu_option}"\n'
                    iommu_enabled = True
                break

        if iommu_enabled:
            with open(grub_config, 'w') as file:
                file.writelines(lines)
            stdout, stderr, returncode = run_command('grub-mkconfig -o /boot/grub/grub.cfg')
            if returncode != 0:
                print(f'Error updating GRUB configuration: {stderr}')
                return False
    else:
        if cpu == 'intel':
            iommu_option = 'intel_iommu=on'
        else:
            iommu_option = 'amd_iommu=on'
        stdout, stderr, returncode = run_command(f'sudo kernelstub --add-options "{iommu_option}"')
        if returncode != 0:
            print(f'Error updating kernelstub: {stderr}')
            return False

    return True


def identify_iommu_groups():
    iommu_groups = {}

    for group_folder in os.listdir('/sys/kernel/iommu_groups'):
        group_path = os.path.join('/sys/kernel/iommu_groups', group_folder)
        group_number = os.path.basename(group_path)

        for device_folder in os.listdir(group_path + '/devices'):
            device_path = os.path.join(group_path, 'devices', device_folder)
        bus_id = os.path.basename(device_path)
        device_name = os.readlink(os.path.join(device_path, 'class'))
        device_class = os.path.basename(device_name)

        if any(keyword in device_class for keyword in ['VGA', 'Audio', 'USB']):
            iommu_groups[bus_id] = int(group_number)
        print(f'IOMMU Group {group_number}, Bus ID {bus_id}: {device_class}')

        return iommu_groups


def setup_libvirt_hook_helper():
    print("Installing libvirt hook helper...")
    returncode = run_command_interactive(
        "sudo wget 'https://raw.githubusercontent.com/PassthroughPOST/VFIO-Tools/master/libvirt_hooks/qemu' -O "
        "/etc/libvirt/hooks/qemu")
    if returncode != 0:
        print("Error downloading libvirt hook helper")
        return False

    returncode = run_command_interactive("sudo chmod +x /etc/libvirt/hooks/qemu")
    if returncode != 0:
        print("Error setting executable permissions for libvirt hook helper")
        return False

    print("Restarting libvirtd service...")
    returncode = run_command_interactive("sudo service libvirtd restart")
    if returncode != 0:
        print("Error restarting libvirtd service")
        return False

    print("Libvirt hook helper installed and libvirtd service restarted.")
    return True


def convert_bus_identifiers(iommu_groups):
    converted_ids = {}
    for bus_id, group_number in iommu_groups.items():
        converted_id = 'pci_0000_' + bus_id.replace(':', '_').replace('.', '_')
        device_path = os.path.join('/sys/kernel/iommu_groups', str(group_number), 'devices', bus_id, 'class')
        device_class = os.path.basename(os.readlink(device_path))
        print(f'IOMMU Group {group_number}, Converted Bus ID {converted_id}: {device_class}')
        converted_ids[bus_id, device_class] = converted_id
        return converted_ids


def create_kvm_conf(vga_bus_id=None, audio_bus_id=None, usb_bus_id=None):
    kvm_conf_path = '/etc/libvirt/hooks/kvm.conf'
    with open(kvm_conf_path, 'w') as file:
        file.write('## virsh devices\n')
        if vga_bus_id:
            file.write(f'VIRSH_GPU_VIDEO={vga_bus_id}\n')
        if audio_bus_id:
            file.write(f'VIRSH_GPU_AUDIO={audio_bus_id}\n')
        if usb_bus_id:
            file.write(f'VIRSH_GPU_USB={usb_bus_id}\n')


def main():
    print('Checking if virtualization is enabled...')
    if not check_virtualization_enabled():
        print(
            'Error: Virtualization not enabled on your CPU. Please enable Intel VT-d or AMD-Vi in your BIOS/UEFI '
            'settings.')
        return

    bootloader, cpu = get_bootloader_and_cpu()

    print('Installing required packages...')
    if not install_packages():
        print('Error during installation. Exiting...')
        return

    print('Enabling IOMMU...')
    if not enable_iommu(bootloader, cpu):
        print('Error during IOMMU setup. Exiting...')
        return

    print('Identifying IOMMU groups...')
    iommu_groups = identify_iommu_groups()

    print('Converting Bus Identifiers...')
    converted_ids = convert_bus_identifiers(iommu_groups)

    # Replace the following lines with the user's selected Bus IDs for VGA, Audio, and USB devices
    selected_vga_bus_id = converted_ids.get("VGA")  # Example Bus ID for VGA
    selected_audio_bus_id = converted_ids.get("Audio")  # Example Bus ID for Audio
    selected_usb_bus_id = converted_ids.get("USB")  # Example Bus ID for USB

    print('Creating kvm.conf...')
    create_kvm_conf(selected_vga_bus_id, selected_audio_bus_id, selected_usb_bus_id)

    print('Setting up libvirt hook helper...')
    if not setup_libvirt_hook_helper():
        print('Error during libvirt hook helper setup. Exiting...')
        return

    print('VFIO and GPU PCI passthrough setup complete. Please reboot your system for the changes to take effect.')
    print('Visit https://github.com/Unhall0w3d/mind-enigma/tree/master/Linux%20Scripts/VFIO/ and download the two '
          '*_vfio.sh files. Place the bind_vfio.sh file in /etc/libvirt/hooks/qemu.d/<vm name>/prepare/begin/ and '
          'place the unbind_vfio.sh file in /etc/libvirt/hooks/qemu.d/<vm name>/prepare/end/ in order to dynamically '
          'bind the VFIO drivers before the VM starts and unbind them after. ')
    print('You are ready to install, configure, and tweak your Virtual Machine.')

    while True:
        done = input("Save the above instructions in a notepad. Press 'y' to Quit...").lower
        if done == "y":
            exit()
        else:
            print(f"That wasn't Y. You pressed {done}. Please try again.")


if __name__ == "__main__":
    main()
