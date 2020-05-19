#!/usr/var/python
# -*- code:UTF-8 -*-

import time
import os
import sys
import requests
import urllib3
import xml.dom.minidom
from getpass import getpass
import xml.etree.ElementTree as ET

# Define Variables
timestr = time.strftime("%Y%m%d-%H%M%S")


def checkregstate():
    # Define disablement of HTTPS Insecure Request error message.
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Define user input required for script; pub ip, username, pw
    ccmip = str(input('What is the CUCM Pub IP?: '))
    print('Supported UCM SQL DB Versions: 12.5 | 12.0 | 11.5 | 11.0 | 10.5 | 10.0 | 9.1 | 9.0')
    version = str(input('What version is UCM?: '))
    myusername = str(input('What is the GUI Username?: '))
    mypassword = getpass('What is the GUI Password?: ')
    devicepool = str(input('What is the Device Pool name? (e.g. Remote_EST_DP): '))

    # URL to hit for request against axl
    url = ('https://' + ccmip + '/axl/')

    # Payload to send; soap envelope
    payload = '<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" ' \
              'xmlns:ns=\"http://www.cisco.com/AXL/API/10.5\">\n   <soapenv:Header/>\n   <soapenv:Body>\n      ' \
              '<ns:executeSQLQuery sequence=\"\">\n         <sql>\n            SELECT d.name \n            FROM ' \
              'device d \n            INNER JOIN devicepool dp ON dp.pkid=d.fkdevicepool \n            WHERE dp.name ' \
              'like \"' + devicepool + '\"\n         </sql>\n      </ns:executeSQLQuery>\n   ' \
                                       '</soapenv:Body>\n</soapenv:Envelope> '

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

    with open('regcheckdevicelist.xml', 'w+') as file:
        file.write(xml_pretty_str)

    tree = ET.parse('regcheckdevicelist.xml')
    text = [child.text for child in tree.iter() if not child.text.strip() == '']
    for word in text:
        with open('devicelist_' + timestr + '.txt', 'a+') as file:
            file.write(word + '\n')
    inputfile = os.path.join(sys.path[0], "devicelist_" + timestr + ".txt")
    with open(inputfile, 'r') as inputfile:
        lines = [line.rstrip() for line in inputfile]
        for line in inputfile:
            lines.append(line)
    print('Registration Report Below.')
    for devname in lines:
        try:
            response = requests.get('https://' + ccmip + '/ast/ASTIsapi.dll?OpenDeviceSearch?Type=&NodeName'
                                                         '=&SubSystemType=&Status=1&DownloadStatus=&MaxDevices=200'
                                                         '&Model=&SearchType=Name&Protocol=Any&SearchPattern=' + devname,
                                    verify=False,
                                    auth=(myusername, mypassword))
            tree = ET.fromstring(response.content)
            for item in tree.iter('DeviceReply'):
                if item.attrib['TotalDevices'] == '1':
                    for _item in tree.iter('Device'):
                        print('IP Address: ' + _item.attrib['IpAddress'], 'Device Name: ' + _item.attrib['Name'],
                              'Description: ' + _item.attrib['Description'],
                              'Registered DNs: ' + _item.attrib['DirNumber'],
                              'Phone Load: ' + _item.attrib['ActiveLoadId'])
            continue
        except (KeyboardInterrupt, SystemExit, Exception):
            exit()


# XML Content is now received from CCM AST for each device pulled, response.content (xml string) is printed. Would
# like to parse xml string (xml.fromstring?) and look for uniquely identifyable tag text indicating device is
# registered, such as if tag text contains devname, consider it registered and print the tag text? Need to think on it.


checkregstate()
