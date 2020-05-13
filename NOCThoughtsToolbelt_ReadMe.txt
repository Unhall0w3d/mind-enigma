READ_ME
Script written by Ken Perry, NOC Thoughts Blog
https://nocthoughts.wordpress.com
Code guidance, testing and other contributions by Mark Barba, Juliana Xu, Cole Aten, Robert Phillips.

Required Modules:
subprocess
time
xml.etree.ElementTree
from io import BytesIO

pycurl
requests

Device Coverage for Reg Check:
Cisco IP Communicator
Cisco 6901, 7832, 7936, 7937, 7940, 7841, 7945, 7961, 7962, 7965, 7970, 8811, 8821, 8831, 8841, 8851, 8861, 8865, 9951, 9971
Cisco DX650
Cisco ATA187

Device Coverage for Log Pull:
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
