```
#####################################
# Script created by Ken Perry, 2020 #
#       NOC THOUGHTS BLOG           #
#    https://www.nocthoughts.com    #
#####################################
```

## NOTE
Script will be broken down into component parts, rather than packaged as a large toolbelt. Scripts will end up in corresponding folders for their general purpose.
# Main Menu
```
1: Cisco Phone Requests
	Leads to Option 1 Menu
2: Cisco UCM Requests
	Leads to Option 2 Menu
3: Unimplemented
	Option not yet implemented
	
Option 1 Menu:
1: Pull Cisco Phone Info
	Useful when checking for registration state on Cisco Phones (only) by IP, or collecting Serial Numbers for SmartNet True-up.
	Requires .txt file for input. See "Input Method(s)"

2: Pull Cisco Phone Logs
	Useful when needing to download logs from one or many Cisco phones. All logs as fast as possible.
	Requires phone IP addresses.
	Utilizes manual input()

3: Pull Cisco Device Registration by Device Pool
	Useful for checking device registration when the target phones are grouped by Device Pool configuration.
	Supports checking Media Resources, MGCP Gateway/MGCP Endpoint, SCCP/SIP Phones/ATAs, SCCP Voicemail Ports, Hunt Lists, Route Lists, CTI Route Points/CTI Ports.
	Performs a db dip to pull device pools available on the target system, prompts for input.
	Performs a secondary db dip to pull all devices associated with the given device pool and reports registration status.

4: Pull Cisco Device Registration by File
	Useful for checking phone registration when the target phones are not grouped by a logical configuration.
	Requires .txt file for input. See "Input Method(s)"
	Supports checking Media Resources, MGCP Gateway/MGCP Endpoint, SCCP/SIP Phones/ATAs, SCCP Voicemail Ports, Hunt Lists, Route Lists, CTI Route Points/CTI Ports.
5: Pull Cisco Device Registration for All
	Useful for checking device registration for all devices configured in the cluster, with with some exceptions. See below.
	Supports checking Media Resources, MGCP Gateway/MGCP Endpoint, SCCP/SIP Phones/ATAs, SCCP Voicemail Ports, Hunt Lists, Route Lists, CTI Route Points/CTI Ports.

Option 2 Menu:
1: Pull UCM Device Defaults
	Pulls a report (xml) from UCM for the default firmware configured in "device defaults" ONLY for phone models configured on the cluster (where count exists/is not 0).
2: Pull UCM Phones Configured
	Pulls a report (xml) from UCM for all phones configured including the associated directory number (line 1), device name, description, and line 1 associated partition.
3: Pull Jabber Last Login Time
	Pulls a report (xml) from IM&P Publisher listing userids and the last time (epoch time) the account was accessed for IM&P/Jabber logins.
4: Pull Devices w/ Static Firmware Assignment
	Pulls a report (xml) from UCM for all phones that have a static Phone Load configured.
5: Pull Home Cluster Report
	Pulls a report (xml) from UCM for all users that have Home Cluster enabled. Returns userid, home cluster enabled (islocaluser=t) and service profile assigned.
```

# Input Methods

All file input methods require a .txt file in which the device ips, or device names are provided ONE PER LINE.
The script takes each line in the file, removes carriage return, and adds each line to a list to be executed against.

# Device Coverage for Reg Check/log pull (Confirmed Working)

```
Cisco IP Communicator
Cisco 6901, 7832, 7936, 7937, 7940, 7841, 7945, 7961, 7962, 7965, 7970,
8811, 8821, 8831, 8841, 8851, 8861, 8865, 9951, 9971
Cisco DX650
Cisco ATA187
```

# Caveats
```(Cisco 7937)```

Devices such as the Cisco 7937 do not contain a serialNumber tag/attribute on the /DeviceInformationX page.
It is thus reported as "n/a".
For these instances it is recommended to verify the data manually.