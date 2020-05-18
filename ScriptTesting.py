#!/usr/var/python
# -*- code:UTF-8 -*-

import time
import os
import sys
import requests
import urllib3
import xml.dom.minidom
from getpass import getpass
from csv import reader
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

    # URL to hit for request against axl
    url = ('https://' + ccmip + '/axl/')

    # Payload to send; soap envelope
    payload = "<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" " \
              "xmlns:ns=\"http://www.cisco.com/AXL/API/10.5\">\n<!--Verifies the last time a Jabber user logged in, " \
              "or the last time their profile was accessed-->\n   <soapenv:Header/>\n   <soapenv:Body>\n      " \
              "<ns:executeSQLQuery sequence=\"\">\n         <sql>\n            SELECT d.name \n            FROM " \
              "device d \n            INNER JOIN devicepool dp ON dp.pkid=d.fkdevicepool \n            WHERE dp.name " \
              "like \"Remote_EST_DP\"\n         </sql>\n      </ns:executeSQLQuery>\n   " \
              "</soapenv:Body>\n</soapenv:Envelope> "

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
        with open('devicelist_' + timestr + '.csv', 'a+') as file:
            file.write(word + ',')
    inputfile = os.path.join(sys.path[0], "devicelist_" + timestr + ".csv")
    with open(inputfile, 'r') as inputfile:
        csv_reader = reader(inputfile)
        for word in csv_reader:
            response = requests.get('https://' + ccmip + '/ast/ASTIsapi.dll?OpenDeviceSearch?Type=&NodeName'
                                                         '=&SubSystemType=&Status=1&DownloadStatus=&MaxDevices=200'
                                                         '&Model=&SearchType=Name&&Protocol=Any&SearchPattern=' + word)

# Need to figure out how to parse reseponse as response.content isn't containing full xml for some reason... and
# print to file screen & file device name, reg state, node it's registered to w/ descriptor line as first line.
# seems like there could be a better way to do all of this.

checkregstate()
