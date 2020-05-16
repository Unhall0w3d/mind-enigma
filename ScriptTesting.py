#!/usr/var/python
# -*- code:UTF-8 -*-

import time
import requests
import urllib3
import xml.dom.minidom
from getpass import getpass

# Define Variables
timestr = time.strftime("%Y%m%d-%H%M%S")


def devicestaticfirmwareassignment():
    # Define disablement of HTTPS Insecure Request error message.
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Define user input required for script; pub ip, username, pw
    ccmip = str(input('What is the CUCM Pub IP?: '))
    print('Supported UCM SQL DB Versions: 12.5 | 12.0 | 11.5 | 11.0 | 10.5 | 10.0 | 9.1 | 9.0')
    version = str(input('What version is UCM?: '))
    myusername = str(input('What is the GUI Username?: '))
    mypassword = getpass('What is the GUI Password?: ')

    # URL to hit for request against axl
    url = ('https://' + ccmip + '/axl/')

    # Payload to send; soap envelope
    payload = "<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" " \
              "xmlns:ns=\"http://www.cisco.com/AXL/API/10.5\">\n<!-- Like https://[CCM-IP-ADDRESS]/ccmadmin > Device " \
              "> Device Settings > Device Firmware Load Information -->\n   <soapenv:Header/>\n   <soapenv:Body>\n    " \
              "  <ns:executeSQLQuery sequence=\"\">\n         <sql>\n            SELECT d.name, " \
              "d.specialloadinformation, d.description, tp.name AS model\n            FROM device AS d\n            " \
              "INNER JOIN TypeProduct AS tp ON d.tkmodel=tp.tkmodel\n            WHERE d.name like 'SEP%' AND " \
              "d.specialloadinformation != ''\n         </sql>\n      </ns:executeSQLQuery>\n   " \
              "</soapenv:Body>\n</soapenv:Envelope>\n "

    # Header content, define db version and execute an SQL Query
    headers = {
        'SOAPAction': 'CUCM:DB ver=' + version + ' executeSQLQuery',
        'Content-Type': 'text/plain'
    }

    print('Collecting Data...')
    # Here's where we send a POST message out to CUCM, we don't verify certificates.
    response = requests.request("POST", url, headers=headers, data=payload, auth=(myusername, mypassword), verify=False)

    uglyxml = response.text.encode('utf8')
    xmldata = xml.dom.minidom.parseString(uglyxml)
    xml_pretty_str = xmldata.toprettyxml()
    print('Data Collected. Please see file DevicesStaticFirmwareAssignment' + timestr + ccmip + '.xml.')

    with open('DevicesStaticFirmwareAssignment' + timestr + ccmip + '.xml', 'w+') as file:
        file.write(xml_pretty_str)
