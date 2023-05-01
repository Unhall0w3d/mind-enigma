import subprocess


def run_command(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    while True:
        output = process.stdout.readline().decode().strip()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output)

    return process.returncode


def install_liquorix_kernel():
    command = "curl -s 'https://liquorix.net/install-liquorix.sh' | sudo bash"
    return_code = run_command(command)
    print(f"\nCommand exited with return code: {return_code}")


def install_zen_kernel():
    gpu_info_command = "lspci -vnn | grep VGA"
    gpu_info_process = subprocess.run(gpu_info_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    gpu_info_output = gpu_info_process.stdout.decode().strip()

    if "NVIDIA" in gpu_info_output:
        print("Installing Linux Zen Kernel for NVIDIA GPU...")
        command = "sudo pacman -S linux-firmware linux-zen linux-zen-headers nvidia-dkms"
        return_code = run_command(command)
        print(f"\nCommand exited with return code: {return_code}")
    elif "AMD" in gpu_info_output:
        print("Installing Linux Zen Kernel for AMD GPU...")
        command = "sudo pacman -S linux-firmware linux-zen linux-zen-headers"
        return_code = run_command(command)
        print(f"\nCommand exited with return code: {return_code}")
    else:
        print("Unsupported GPU detected.")


def install_default_kernel():
    gpu_info_command = "lspci -vnn | grep VGA"
    gpu_info_process = subprocess.run(gpu_info_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    gpu_info_output = gpu_info_process.stdout.decode().strip()

    if "NVIDIA" in gpu_info_output:
        print("Installing Default Kernel for NVIDIA GPU...")
        command = "sudo pacman -S linux-firmware linux linux-headers nvidia-dkms"
        return_code = run_command(command)
        print(f"\nCommand exited with return code: {return_code}")
    elif "AMD" in gpu_info_output:
        print("Installing Default Kernel for AMD GPU...")
        command = "sudo pacman -S linux-firmware linux linux-headers"
        return_code = run_command(command)
        print(f"\nCommand exited with return code: {return_code}")
    else:
        print("Unsupported GPU detected.")


def install_lxde():
    command = "sudo pacman -S lxde --needed"
    return_code = run_command(command)
    print(f"\nCommand exited with return code: {return_code}")


def install_gnome():
    command = "sudo pacman -S gnome --needed"
    return_code = run_command(command)
    print(f"\nCommand exited with return code: {return_code}")


def install_kde():
    command = "sudo pacman -S plasma-meta kde-applications --needed"
    return_code = run_command(command)
    print(f"\nCommand exited with return code: {return_code}")


def install_xfce():
    command = "sudo pacman -S xfce4 xfce4-goodies --needed"
    return_code = run_command(command)
    print(f"\nCommand exited with return code: {return_code}")


def install_budgie():
    command = "sudo pacman -S budgie-desktop --needed"
    return_code = run_command(command)
    print(f"\nCommand exited with return code: {return_code}")


def install_cinnamon():
    command = "sudo pacman -S cinnamon --needed"
    return_code = run_command(command)
    print(f"\nCommand exited with return code: {return_code}")


def install_mate():
    command = "sudo pacman -S mate mate-extra --needed"
    return_code = run_command(command)
    print(f"\nCommand exited with return code: {return_code}")


def install_display_manager():
    print("Select Display Manager:")
    print("1. GDM")
    print("2. LightDM")
    print("3. LXDM")
    print("4. SDDM")
    print("5. XDM")
    print("6. Return to Main Menu")

    choice = input("Enter your choice (1-6): ")

    if choice == '1':
        command = "sudo pacman -S gdm --needed"
        return_code = run_command(command)
        print(f"\nCommand exited with return code: {return_code}")
    elif choice == '2':
        command = "sudo pacman -S lightdm lightdm-gtk-greeter --needed"
        return_code = run_command(command)
        print(f"\nCommand exited with return code: {return_code}")
    elif choice == '3':
        command = "sudo pacman -S lxdm --needed"
        return_code = run_command(command)
        print(f"\nCommand exited with return code: {return_code}")
    elif choice == '4':
        command = "sudo pacman -S sddm --needed"
        return_code = run_command(command)
        print(f"\nCommand exited with return code: {return_code}")
    elif choice == '5':
        command = "sudo pacman -S xorg xorg-xinit xterm xdm --needed"
        return_code = run_command(command)
        print(f"\nCommand exited with return code: {return_code}")
    elif choice == '6':
        return
    else:
        print("Invalid choice. Please try again.")
        install_display_manager()


def install_desktop_environment():
    print("Select Desktop Environment:")
    print("1. LXDE")
    print("2. GNOME")
    print("3. KDE Plasma")
    print("4. XFCE")
    print("5. Budgie")
    print("6. Cinnamon")
    print("7. MATE")
    print("8. Return to Main Menu")

    choice = input("Enter your choice (1-8): ")

    if choice == '1':
        install_lxde()
    elif choice == '2':
        install_gnome()
    elif choice == '3':
        install_kde()
    elif choice == '4':
        install_xfce()
    elif choice == '5':
        install_budgie()
    elif choice == '6':
        install_cinnamon()
    elif choice == '7':
        install_mate()
    elif choice == '8':
        return
    else:
        print("Invalid choice. Please try again.")
        install_desktop_environment()


def submenu():
    print("Select Kernel:")
    print("1. Install Optimized Liquorix Kernel")
    print("2. Install Linux Zen Kernel")
    print("3. Install Default Kernel")
    print("4. Return to Main Menu")

    choice = input("Enter your choice (1-4): ")

    if choice == '1':
        install_liquorix_kernel()
    elif choice == '2':
        install_zen_kernel()
    elif choice == '3':
        install_default_kernel()
    elif choice == '4':
        return
    else:
        print("Invalid choice. Please try again.")
        submenu()


def menu():
    print("***********************************")
    print("*       NOC Thoughts Arch         *")
    print("* Post-Install Script ")
    print("***********************************")
    print("Menu:")
    print("1. Install Kernel")
    print("2. Install Desktop Environment")
    print("3. Install Display Manager")
    print("4. Exit")

    choice = input("Enter your choice (1-4): ")

    if choice == '1':
        submenu()
    elif choice == '2':
        install_desktop_environment()
    elif choice == '3':
        install_display_manager()
    elif choice == '4':
        print("Exiting...")
    else:
        print("Invalid choice. Please try again.")
        menu()


menu()
