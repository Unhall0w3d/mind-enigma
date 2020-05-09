READ_ME
Script written by Ken Perry
Code, testing and other contributions by Mark Barba, Juliana Xu, Cole Aten, Robert Phillips

Required Modules:
re
requests
bs4 (BeautifulSoup)
collections (OrderedDict)

Device Coverage:
Cisco IP Communicator
Cisco 6901, 7832, 7936, 7937, 7940, 7841, 7945, 7961, 7962, 7965, 7970, 8811, 8821, 8831, 8841, 8851, 8861, 8865, 9951, 9971
Cisco DX650
Cisco ATA187

Notes:
Script accepts user input at shell to define phone count and IP addresses. This is ideal for small subset of devices (max 20), more than that becomes cumbersome. Script is being developed to allow input of text file with an IP Per line. Details to follow once script moves out of test phase.

Querying HTTPs URLs or devices requiring login is not currently supported.
