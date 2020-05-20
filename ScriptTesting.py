#!/usr/var/python
# -*- code:UTF-8 -*-

import time
import requests
import urllib3
import xml.dom.minidom
from getpass import getpass
import xml.etree.ElementTree as ET

# Define Variables
timestr = time.strftime("%Y%m%d-%H%M%S")

# Define disablement of HTTPS Insecure Request error message.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# URL to hit for request against axl
baseurl = 'https://'


def createdevstring():
    tree = ET.parse('regcheckdevicelist.xml')
    text = [child.text for child in tree.iter() if not child.text.strip() == '']
    devicename = ",".join(text)
    return devicename


def infocollect():
    # Define user input required for script; pub ip, username, pw
    ccmip = str(input('What is the CUCM Pub IP?: '))
    print('Supported UCM SQL DB Versions: 12.5 | 12.0 | 11.5 | 11.0 | 10.5 | 10.0 | 9.1 | 9.0')
    version = str(input('What version is UCM?: '))
    myusername = str(input('What is the GUI Username?: '))
    mypassword = getpass('What is the GUI Password?: ')
    devicepool = str(input('What is the Device Pool name? (e.g. Remote_EST_DP): '))
    return ccmip, version, mypassword, myusername, devicepool


def ucmdbdip(cucmipaddr, cucmversion, cucmpassword, cucmusername, cucmdevicepool):
    # Payload to send; soap envelope
    payload = '<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" ' \
              'xmlns:ns=\"http://www.cisco.com/AXL/API/10.5\">\n   <soapenv:Header/>\n   <soapenv:Body>\n      ' \
              '<ns:executeSQLQuery sequence=\"\">\n         <sql>\n            SELECT d.name \n            FROM ' \
              'device as d \n            INNER JOIN devicepool as dp ON dp.pkid=d.fkdevicepool \n            WHERE ' \
              'dp.name ' \
              'like \"' + cucmdevicepool + '\"\n         </sql>\n      </ns:executeSQLQuery>\n   ' \
                                           '</soapenv:Body>\n</soapenv:Envelope> '

    # Header content, define db version and execute an SQL Query
    headers = {
        'SOAPAction': 'CUCM:DB ver=' + cucmversion + ' executeSQLQuery',
        'Content-Type': 'text/plain'
    }

    # Here's where we verify reachability of the AXL interface for DB dip.
    try:
        reachabilitycheck = requests.get(baseurl + cucmipaddr + '/axl', auth=(cucmusername, cucmpassword), verify=False)
        if reachabilitycheck.status_code != 200:
            print('AXL Interface at ' + baseurl + cucmipaddr + '/axl/ is not available, or some other error. '
                                                               'Please verify CCM AXL Service Status.')
            print(reachabilitycheck.status_code)
            print('Contact script dev to create exception based on response code.')
            exit()
        elif reachabilitycheck.status_code == 200:
            print('AXL Interface is working and accepting requests.')
    except Exception as m:
        print(m)
    print()
    print('Collecting Data...')
    response = requests.request("POST", baseurl + cucmipaddr + '/axl/', headers=headers, data=payload,
                                auth=(cucmusername, cucmpassword), verify=False)

    uglyxml = response.text.encode('utf8')
    xmldata = xml.dom.minidom.parseString(uglyxml)
    xml_pretty_str = xmldata.toprettyxml()

    with open('regcheckdevicelist.xml', 'w+') as file:
        file.write(xml_pretty_str)


def checkregstate(cucmipaddr, cucmpassword, cucmusername, cucmdevicepool, devname):
    # Call Function to create proper devname string to append to AST request
    createdevstring()

    # Inform the user what device pool this report is for.
    print()
    print('Registration Report Below For Device Pool ' + cucmdevicepool + '.')
    print()
    try:
        response = requests.get(baseurl + cucmipaddr + '/ast/ASTIsapi.dll?OpenDeviceSearch?Type=&NodeName'
                                                       '=&SubSystemType=&Status=1&DownloadStatus=&MaxDevices=200'
                                                       '&Model=&SearchType=Name&Protocol=Any&SearchPattern=' + devname,
                                verify=False,
                                auth=(cucmusername, cucmpassword))
        devicelist = devname.split(",")
        tree = ET.fromstring(response.content)
        for item in tree.iter('DeviceReply'):
            if item.attrib['TotalDevices'] != '0':
                for devicename in devicelist:
                    notregcheck = response.content.decode('utf-8')
                    if notregcheck.find(devicename) == -1:
                        print('Device ' + devicename + ' is not registered.')
                for xmltag in tree.iter('Device'):
                    print('IP Address: ' + xmltag.attrib['IpAddress'], 'Device Name: ' + xmltag.attrib['Name'],
                          'Description: ' + xmltag.attrib['Description'],
                          'Registered: ' + xmltag.attrib['Status'])
            elif item.attrib['TotalDevices'] == '0':
                print('No queried devices were registered per UCM AST API.')
                print('Devices checked are listed below')
                print(devname)
                continue
    except Exception as p:
        print(p)


# User input collection
cucmipaddr, cucmversion, cucmpassword, cucmusername, cucmdevicepool = infocollect()

# Call DB Dip Function for Device List
ucmdbdip(cucmipaddr, cucmversion, cucmpassword, cucmusername, cucmdevicepool)

# Collect list of devices to hit AST interface with
devname = createdevstring()

# Hit AST interface
checkregstate(cucmipaddr, cucmpassword, cucmusername, cucmdevicepool, devname)
