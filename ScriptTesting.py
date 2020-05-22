#!/usr/var/python
# -*- code:UTF-8 -*-

import time
import requests
import urllib3
import xml.dom.minidom
from getpass import getpass
import xml.etree.ElementTree as ET
import os
import numpy

# Define Variables
timestr = time.strftime("%Y%m%d-%H%M%S")

# Define disablement of HTTPS Insecure Request error message.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# URL to hit for request against axl
baseurl = 'https://'


# Function that parses xml file and strips xml specific data and joins each device name in in the xml doc.
def createdevstring():
    tree = ET.parse('regcheckdevicelist.xml')
    text = [child.text for child in tree.iter() if not child.text.strip() == '']
    devicename = ",".join(text)
    return devicename


# Function that gathers input from user for required parameters.
def infocollect():
    # Define user input required for script; pub ip, username, pw
    ccmip = str(input('What is the CUCM Pub IP?: '))
    print('Supported UCM SQL DB Versions: 12.5 | 12.0 | 11.5 | 11.0 | 10.5 | 10.0 | 9.1 | 9.0')
    version = str(input('What version is UCM?: '))
    myusername = str(input('What is the GUI Username?: '))
    mypassword = getpass('What is the GUI Password?: ')
    return ccmip, version, mypassword, myusername


def collectdevicepool(cucmipaddr, cucmusername, cucmpassword, cucmversion):
    payload = "<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" " \
              "xmlns:ns=\"http://www.cisco.com/AXL/API/10.5\">\n   <soapenv:Header/>\n   <soapenv:Body>\n      " \
              "<ns:executeSQLQuery sequence=\"\">\n         <sql>\n            SELECT name\n            FROM " \
              "devicepool\n         </sql>\n      </ns:executeSQLQuery>\n   </soapenv:Body>\n</soapenv:Envelope> "
    headers = {
        'SOAPAction': 'CUCM:DB ver=' + cucmversion + ' executeSQLQuery',
        'Content-Type': 'text/plain'
    }
    response = requests.request("POST", baseurl + cucmipaddr + '/axl/', headers=headers, data=payload,
                                auth=(cucmusername, cucmpassword), verify=False)
    uglyxml = response.text.encode('utf8')
    xmldata = xml.dom.minidom.parseString(uglyxml)
    xml_pretty_str = xmldata.toprettyxml()
    with open('devicepoollist.xml', 'w+') as file:
        file.write(xml_pretty_str)
    parse = ET.parse('devicepoollist.xml')
    entry = [child.text for child in parse.iter() if not child.text.strip() == '']
    dplist = "\n".join(entry)
    print()
    print('Device Pools Available:')
    print()
    print(dplist)
    print()
    devicepool = str(input('What is the Device Pool name?: '))
    return devicepool


# Function that dips into ccm db and executes SQL Query via SOAP. Returns devices in specified device pool.
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
            print('Contact script dev to create exception or handle response code.')
            exit()
        elif reachabilitycheck.status_code == 200:
            print()
            print('AXL Interface is working and accepting requests.')
    except requests.exceptions.ConnectionError:
        print('Connection error occurred. Unable to get HTTP Response from CUCM AXL Interface. Check connectivity.')
    except requests.exceptions.Timeout:
        print('Connection timed out to UCM AXL Interface.')
    except Exception as m:
        print(m)
    print()
    print('Collecting Data...')
    response = requests.request("POST", baseurl + cucmipaddr + '/axl/', headers=headers, data=payload,
                                auth=(cucmusername, cucmpassword), verify=False)
    # We encode the text response from POST request as utf8 and pretty print it to a file
    uglyxml = response.text.encode('utf8')
    xmldata = xml.dom.minidom.parseString(uglyxml)
    xml_pretty_str = xmldata.toprettyxml()
    with open('regcheckdevicelist.xml', 'w+') as file:
        file.write(xml_pretty_str)


# Function to hit AST interface using device name list generated by createdevstring function.
# Prints the response for registered and unregistered devices.
def checkregstate(cucmipaddr, cucmpassword, cucmusername, cucmdevicepool, devname):
    # Call Function to create proper devname string to append to AST request
    createdevstring()

    # Inform the user what device pool this report is for.
    print()
    print('Registration Report Below For Device Pool: ' + cucmdevicepool + '.')
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
            # If the amount of devices found is not zero, proceed to look for the device name. If it's not found, say so
            if item.attrib['TotalDevices'] != '0':
                for devicename in devicelist:
                    notregcheck = response.content.decode('utf-8')
                    if notregcheck.find(devicename) == -1:
                        print('Device ' + devicename + ' is not registered.')
                # If the device name is found, print out the relevant attributes.
                for xmltag in tree.iter('Device'):
                    print('IP Address: ' + xmltag.attrib['IpAddress'], 'Device Name: ' + xmltag.attrib['Name'],
                          'Description: ' + xmltag.attrib['Description'],
                          'Registered: ' + xmltag.attrib['Status'])
            # If the total number of devices found is 0, we've probably got a problem.
            # Though it is possible to return 0 if all devices are actually unregistered.
            # We print the device name list (csv style) so the user can validate.
            elif item.attrib['TotalDevices'] == '0':
                print('No queried devices were registered per UCM AST API.')
                continue
    except requests.exceptions.ConnectionError:
        print('Connection error occurred. Unable to get HTTP Response from CUCM AST Interface. Check connectivity.')
    except requests.exceptions.Timeout:
        print('Connection timed out to UCM AST Interface.')
    except Exception as p:
        print(p)
    # Perform cleanup of files generated.
    os.remove("regcheckdevicelist.xml")
    os.remove("devicepoollist.xml")


# User input collection provided by infocollect function
cucmipaddr, cucmversion, cucmpassword, cucmusername = infocollect()

# Collect device pool
cucmdevicepool = collectdevicepool(cucmipaddr, cucmusername, cucmpassword, cucmversion)

# Call DB Dip Function to execute sql query and prettyprint xml response to file
ucmdbdip(cucmipaddr, cucmversion, cucmpassword, cucmusername, cucmdevicepool)

# Collect list of devices to hit AST interface with by parsing xml file and joining to csv string
devname = createdevstring()

# Hit AST interface to check reg status using csv string generated by createdevstring function
checkregstate(cucmipaddr, cucmpassword, cucmusername, cucmdevicepool, devname)
