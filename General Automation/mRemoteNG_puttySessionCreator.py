#!/usr/bin/python
#####################################
# Script created by Ken Perry, 2023 #
#       NOC THOUGHTS BLOG           #
#    https://www.nocthoughts.com    #
#####################################

import random
import os
import pandas as pd
import glob
import time
import csv
import uuid


def analyze_sanitize():
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
    device_list_path = csv_files[choice]

    # Read the .csv file
    read_in = pd.read_csv(device_list_path, header=None)  # Indicate that there is no header

    # Filter the data based on the device type and column "E"
    device_types = ["Network", "DC-UCS", "DC-VMWare", "IPT", "Network-Voice", "Video-TelePresence"]
    filtered = read_in[read_in[0].isin(device_types)]
    return filtered


def generate_chaos():
    return str(uuid.uuid4())


class HiveMind:
    def __init__(self):
        self.filename = None
        self.folderuuid = generate_chaos()

        # Check if the directory exists, create it if it doesn't
        if not os.path.exists('mRemoteNG Sessions'):
            os.makedirs('mRemoteNG Sessions')

        # Establish list to contain port forwarding information
        self.port_forwardings = []
        self.timestr = time.strftime("%Y%m%d-%H%M%S")

        # Collect some data
        self.session_name = input("Enter the session name: ")
        self.hostname = input("Enter the hostname/IP: ")
        self.username = input("Enter the username: ")

    def get_tunnel_config(self, tech_type, ip_addr, dev_name, descrip, site):
        """
        Returns the tunnel configuration based on the device type.
        """
        ssh_port = random.randint(30000, 35000)
        ssh_tunnel = f"L{ssh_port}={ip_addr}:22"

        if tech_type in ["Network", "Network-Voice"]:
            self.port_forwardings.append(ssh_tunnel)
            sshuuid = generate_chaos()
            with open(
                    os.path.join('mRemoteNG Sessions', (self.session_name + '-' + self.timestr + '-importFile.csv')),
                    'a') as f:
                writer = csv.writer(f, delimiter=";")
                data = [
                    f"{tech_type}_{dev_name}_SSH", f"{sshuuid}", f"{self.folderuuid}", "Connection",
                    f"{site}_{descrip}", "SSH", "General", f"localhost", "", "SSH2",
                    "DefaultSettings", f"{ssh_port}", "False", "True", "False", "IE",
                    "EncrBasic", "NoAuth", "", "Colors16Bit", "FitToWindow",
                    "TRUE", "FALSE", "FALSE", "FALSE",
                    "FALSE", "FALSE", "FALSE", "FALSE",
                    " FALSE", "FALSE", "FALSE", "DoNotPlay", "FALSE",
                    "", "", "", "", "", "FALSE", "CompNone",
                    "EncHextile", "AuthVNC", "ProxyNone", "", "0", "",
                    "", "ColNormal", "SmartSAspect", "False", "Never",
                    "", "Yes", "", "",
                    "", "FALSE", "Highest"
                ]
                writer.writerow(data)
        elif tech_type in ["IPT", "DC-UCS", "DC-VMware"]:
            https_port = random.randint(35000, 40000)
            https_tunnel = f"L{https_port}={ip_addr}:443"
            self.port_forwardings.append(f"{ssh_tunnel},{https_tunnel}")
            sshuuid = generate_chaos()
            httpsuuid = generate_chaos()
            with open(os.path.join('mRemoteNG Sessions', (self.session_name + '-' + self.timestr + '-importFile.csv')),
                      'a') as f:
                writer = csv.writer(f, delimiter=";")
                sshdata = [
                    f"{tech_type}_{dev_name}_SSH", f"{sshuuid}", f"{self.folderuuid}", "Connection",
                    f"{site}_{descrip}", "SSH", "General", f"localhost", "", "SSH2",
                    "DefaultSettings", f"{ssh_port}", "False", "True", "False", "IE",
                    "EncrBasic", "NoAuth", "", "Colors16Bit", "FitToWindow",
                    "TRUE", "FALSE", "FALSE", "FALSE",
                    "FALSE", "FALSE", "FALSE", "FALSE",
                    "FALSE", "FALSE", "FALSE", "DoNotPlay", "FALSE",
                    "", "", "", "", "", "FALSE", "CompNone",
                    "EncHextile", "AuthVNC", "ProxyNone", "", "0", "",
                    "", "ColNormal", "SmartSAspect", "False", "Never",
                    "", "Yes", "", "",
                    "", "FALSE", "Highest"
                ]
                writer.writerow(sshdata)
                httpsdata = [
                    f"{tech_type}_{dev_name}_HTTPS", f"{httpsuuid}", f"{self.folderuuid}", "Connection",
                    f"{site}_{descrip}", "Web Server", "General", f"localhost", "", "HTTPS",
                    "DefaultSettings", f"{https_port}", "False", "True", "False", "IE",
                    "EncrBasic", "NoAuth", "", "Colors16Bit", "FitToWindow",
                    "TRUE", "FALSE", "FALSE", "FALSE",
                    "FALSE", "FALSE", "FALSE", "FALSE",
                    "FALSE", "FALSE", "FALSE", "DoNotPlay", "FALSE",
                    "", "", "", "", "", "FALSE", "CompNone",
                    "EncHextile", "AuthVNC", "ProxyNone", "", "0", "",
                    "", "ColNormal", "SmartSAspect", "False", "Never",
                    "", "Yes", "", "",
                    "", "FALSE", "Highest"
                ]
                writer.writerow(httpsdata)

    def construct_port_forwards(self, tech_type, ip_addr, dev_name, descrip, site):
        # Get the tunnel configuration
        self.get_tunnel_config(tech_type, ip_addr, dev_name, descrip, site)

    def construct_reg_key(self):

        # Define registry key path
        key_path = r"[HKEY_CURRENT_USER\Software\SimonTatham\PuTTY\Sessions\{}]".format(self.session_name)

        # Define the session details
        session_details = f"""Windows Registry Editor Version 5.00 

{key_path}

"HostName"="{self.hostname}"
"PortNumber"=dword:{22:08x}
"UserName"="{self.username}"
"Protocol"="ssh"
"SshProt"=dword:3
"""

        # Define the filename using the session name and hostname
        self.filename = f"{self.session_name}-SSH-Tunnels-{self.timestr}.reg"

        # Create a new file and write the session details
        with open(os.path.join('mRemoteNG Sessions', self.filename), 'w') as f:
            f.write(session_details)

        # Inform user that the .reg file was created successfully
        print(f"Reg file {self.session_name} created successfully.")

    def mremoteng_import_generator(self):
        # Create .csv file
        with open(os.path.join('mRemoteNG Sessions', (self.session_name + "-" + self.timestr +
                                                      '-importFile.csv')), 'w+') as f:
            writer = csv.writer(f, delimiter=";")
            header = [
                "Name", "Id", "Parent", "NodeType", "Description", "Icon", "Panel", "Hostname", "VmId", "Protocol",
                "PuttySession", "Port", "ConnectToConsole", "UseCredSsp", "UseVmId", "RenderingEngine",
                "ICAEncryptionStrength", "RDPAuthenticationLevel", "LoadBalanceInfo", "Colors", "Resolution",
                "AutomaticResize", "DisplayWallpaper", "DisplayThemes", "EnableFontSmoothing",
                "EnableDesktopComposition", "CacheBitmaps", "RedirectDiskDrives", "RedirectPorts",
                "RedirectPrinters", "RedirectClipboard", "RedirectSmartCards", "RedirectSound", "RedirectKeys",
                "PreExtApp", "PostExtApp", "MacAddress", "UserField", "ExtApp", "Favorite", "VNCCompression",
                "VNCEncoding", "VNCAuthMode", "VNCProxyType", "VNCProxyIP", "VNCProxyPort", "VNCProxyUsername",
                "VNCProxyPassword", "VNCColors", "VNCSmartSizeMode", "VNCViewOnly", "RDGatewayUsageMethod",
                "RDGatewayHostname", "RDGatewayUseConnectionCredentials", "RDGatewayUsername", "RDGatewayPassword",
                "RDGatewayDomain", "RedirectAudioCapture", "RdpVersion"
            ]
            writer.writerow(header)
            parentfolder = [
                f"{self.session_name}", f"{self.folderuuid}", "a1c0d02c-6d1d-4c23-b8af-c2d75ce96b8d", "Container",
                "", "mRemoteNG", "General", "", "", "RDP",
                "DefaultSettings", "3389", "False", "True", "False", "IE",
                "EncrBasic", "NoAuth", "", "Colors16Bit", "FitToWindow",
                "TRUE", "FALSE", "FALSE", "FALSE",
                "FALSE", "FALSE", "FALSE", "FALSE",
                "FALSE", "FALSE", "FALSE", "DoNotPlay", "FALSE",
                "", "", "", "", "", "FALSE", "CompNone",
                "EncHextile", "AuthVNC", "ProxyNone", "", "0", "",
                "", "ColNormal", "SmartSAspect", "False", "Never",
                "", "Yes", "", "",
                "", "FALSE", "Highest"
            ]
            writer.writerow(parentfolder)

    def director(self):
        print(f"Constructing reg key for PuTTY {self.session_name} session...")

        # Construct the base reg key to add a session to the end device for tunneling
        self.construct_reg_key()

        print("Constructing template .csv file for mRemoteNG import...")
        # Construct the template csv file with proper headers for mRemoteNG import
        self.mremoteng_import_generator()

        print("Filtering input data...")
        # Read in and parse .csv file to gather interesting data
        filtered = analyze_sanitize()

        print("Iterating through sanitized data...")
        # Iterate over each row in the filtered data
        for _, row in filtered.iterrows():
            tech_type = row[0]
            ip_addr = row[2]
            dev_name = row[1]
            descrip = row[3]
            site = row[9]

            self.construct_port_forwards(tech_type, ip_addr, dev_name, descrip, site)

        # Generate port forward string from list
        pfwdlist = ",".join(self.port_forwardings)

        print("Putting in the final touches...")
        # Add in port forwards
        with open(os.path.join('mRemoteNG Sessions', self.filename), 'a') as f:
            f.write(f""""PortForwardings"="{pfwdlist}"
                                            """)

        print("Job completed! Please check ./mRemoteNG Sessions/ for .reg and .csv!")


if __name__ == "__main__":
    print("Starting up...")
    HiveMind().director()
