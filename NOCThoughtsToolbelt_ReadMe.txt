READ_ME
Script written by Ken Perry, NOC Thoughts Blog
https://nocthoughts.wordpress.com
Code guidance, testing, sample and other contributions by Mark Barba, Juliana Xu, Cole Aten, Robert Phillips.

Use Case(s):
Cisco Phone Info Pull - Useful when checking for registration state on Cisco Phones by IP, or collecting Serial Numbers for SmartNet True-up.
Cisco Phone Log Pull - Useful to collect all Cisco Phone Logs on a phone when working with Cisco TAC or reviewing logs for various phone issues.
UCM Device Defaults - Useful to pull pre UCM Software or Device Pack upgrade in the event reverting phone firmwares is required (due to bug or other issue/requirement).


Input Method(s):
File input for device info check should be a .txt file in same-directory as the script.
Device IP addresses should be listed one per line

File input for cucm registration check should be a .csv file in same-directory as the script.
Device Names (SEPAABBCCDDEEFF) should be a comma separated string.
Example: SEPAABBCCDDEEFF,CIPCJDOE,BOULDER_CO_XCODE

Required Module(s):
subprocess, time, xml.etree.ElementTree, io > BytesIO, pycurl, requests, urllib3, xml.dom.minidom

Device Coverage for Reg Check/log pull:
Cisco IP Communicator
Cisco 6901, 7832, 7936, 7937, 7940, 7841, 7945, 7961, 7962, 7965, 7970, 8811, 8821, 8831, 8841, 8851, 8861, 8865, 9951, 9971
Cisco DX650
Cisco ATA187

Caveats (Cisco 7937):
Devices such as the Cisco 7937 do not contain a serialNumber tag/attribute on the /DeviceInformationX page.
It is thus reported as "n/a".
For these instances it is recommended to verify the data manually.
If there is a pressing need for a workaround/secondary method it may be added...
Cisco 7937 was end of life/end of sale Mar 31, 2019. Get new phones.

Querying HTTPs URLs or devices requiring login is not currently supported. This may be added in the future.
