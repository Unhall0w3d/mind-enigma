import random
import os
import pandas as pd
import glob


def get_tunnel_config(techType):
    """
    Returns the tunnel configuration based on the device type.
    """
    ssh_port = random.randint(30000, 35000)
    ssh_tunnel = f"D{ssh_port} localhost:22"

    if techType in ["Network", "Network-Voice"]:
        return ssh_tunnel
    elif techType in ["IPT", "DC-UCS", "DC-VMware"]:
        https_port = random.randint(35000, 40000)
        https_tunnel = f"D{https_port} localhost:443"
        return f"{ssh_tunnel}\n{https_tunnel}"
    elif techType == "ICM":
        rdp_port = random.randint(18000, 20000)
        rdp_tunnel = f"D{rdp_port} localhost:3389"
        return f"{ssh_tunnel}\n{rdp_tunnel}"


def create_putty_reg_file(session_name, hostname, username, ppk_path, techType, devName, descrip, site):
    # Generate random port number between 20000 and 30000
    port = random.randint(20000, 30000)

    # Get the tunnel configuration
    tunnel_config = get_tunnel_config(techType)

    # Define registry key path
    key_path = r"[HKEY_CURRENT_USER\Software\SimonTatham\PuTTY\Sessions\{}]".format(session_name)

    # Define the session details
    session_details = f"""
{key_path}
"HostName"="{hostname}"
"PortNumber"=dword:{port:08x}
"UserName"="{username}"
"PublicKeyFile"="{ppk_path}"
"Compression"=dword:00000001
"Protocol"="ssh"
"Tunnel"="{tunnel_config}"
"DeviceName"="{devName}"
"Description"="{descrip}"
"SiteName"="{site}"
"""

    # Define the filename using the session name and hostname
    filename = f"{session_name}-{hostname}.reg"

    # Write the session details to the .reg file
    with open(os.path.join('mRemoteNG Sessions - Optanix', filename), 'w') as f:
        f.write(session_details)

    print(f"Session {session_name} created successfully.")


def main():
    # Check if the directory exists, create it if it doesn't
    if not os.path.exists('mRemoteNG Sessions - Optanix'):
        os.makedirs('mRemoteNG Sessions - Optanix')

    session_name = input("Enter the session name: ")
    hostname = input("Enter the hostname/IP: ")
    username = input("Enter the username: ")
    ppk_path = input("Enter the .ppk file path: ")

    # List all .csv files in the current directory
    csv_files = glob.glob("*.csv")

    # If there are no .csv files in the directory, notify the user
    if not csv_files:
        print("No .csv files found in the current directory.")
        return

    # Print out the files for the user to choose
    for i, file in enumerate(csv_files):
        print(f"{i + 1}. {file}")

        # Get the user's choice
    choice = int(input("Enter the number of the file to use: ")) - 1
    device_list_path = xls_files[choice]

    # Read the .xls file
    df = pd.read_excel(device_list_path, skiprows=1, engine='xlrd') # Skip header row

    # Filter the data based on the device type and column "E"
    device_types = ["Network", "DC-UCS", "DC-VMware", "IPT", "ICM", "Network-Voice"]
    df = df[df['A'].isin(device_types) & (df['E'] != 'N')]

    # Iterate over each row in the filtered data
    for _, row in df.iterrows():
        techType = row['A']
        devName = row['B']
        descrip = row['D']
        site = row['K']

    create_putty_reg_file(session_name, hostname, username, ppk_path, techType, devName, descrip, site)


if __name__ == "__main__":
    main()
