#!/usr/var/python
# -*- code:UTF-8 -*-

# Define Imports
import time
import requests
import urllib3
import xml.dom.minidom
from getpass import getpass
import xml.etree.ElementTree as ET
import os

# Define tmp directory
dirname = 'tmp'

# Define current working directory
dir_path = os.getcwd()

# Define complete path
completepath = os.path.join(dir_path,dirname)

# Define Variables
timestr = time.strftime("%Y%m%d-%H%M%S")

# Define disablement of HTTPS Insecure Request error message.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Define URL to hit for request against axl
axlurl = 'https://'


# Chunker function that breaks up list 'text' into chunks of 200
def chunker(text, chunk_size):
    iterlist = iter(text)
    while True:
        chunk = []
        try:
            for i in range(chunk_size):
                chunk.append(next(iterlist))
            yield chunk
        except StopIteration:
            if chunk:
                yield chunk
            return


# Function that parses xml file and strips xml specific data and joins each device name in in the xml doc.
def get_devicenames(chunk_size=200):
    tree = ET.parse('regcheckdevicelist.xml')
    for text in chunker(
            (child.text for child in tree.iter() if not child.text.strip() == ''), chunk_size):
        yield ",".join(text)


# Function that constructs csv string to check against ucm from file input.
def inputfetch():
    inputfile = input('What is the name of the input text file?: ')
    with open(inputfile) as txtfile:
        lines = [line.rstrip() for line in txtfile]
        for line in txtfile:
            lines.append(line)
        x = ",".join(lines)
    return x


# Function that gathers input from user for required parameters.
def infocollect():
    # Define user input required for script; pub ip, username, pw.
    ccmip = str(input('What is the target UC Server Pub IP?: '))
    print('Supported SQL DB Versions: 12.5 | 12.0 | 11.5 | 11.0 | 10.5 | 10.0 | 9.1 | 9.0')
    version = str(input('What version is the UC Server?: '))
    myusername = str(input('What is the GUI Username?: '))
    mypassword = getpass('What is the GUI Password?: ')
    try:
        r = requests.get(axlurl + ccmip + '/axl', auth=(myusername, mypassword), verify=False)
        if r.status_code != 200:
            print('AXL Interface check failed. Please check connectivity at https://<ucm-ip>/axl.')
            print('Ensure the credentials and version info is correct.')
            print('Script Exiting.')
            exit()
        elif r.status_code == 200:
            return ccmip, version, mypassword, myusername
    except Exception as e:
        print(e)


# Function to query UCM for device pool list and present to the user, in case they don't know. Returns selected DP.
def collectdevicepool(cucmipaddr, cucmusername, cucmpassword, cucmversion):
    payload = "<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" " \
              "xmlns:ns=\"http://www.cisco.com/AXL/API/10.5\">\n   <soapenv:Header/>\n   <soapenv:Body>\n      " \
              "<ns:executeSQLQuery sequence=\"\">\n         <sql>\n            SELECT name\n            FROM " \
              "devicepool\n         </sql>\n      </ns:executeSQLQuery>\n   </soapenv:Body>\n</soapenv:Envelope> "
    headers = {
        'SOAPAction': 'CUCM:DB ver=' + cucmversion + ' executeSQLQuery',
        'Content-Type': 'text/plain'
    }
    response = requests.request("POST", axlurl + cucmipaddr + '/axl/', headers=headers, data=payload,
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
def ucmdbdip_dp(cucmipaddr, cucmversion, cucmpassword, cucmusername, cucmdevicepool):
    # Define payload specific to ucmdbdip for specified device pool.
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
    print()
    print('Collecting Data...')
    response = requests.request("POST", axlurl + cucmipaddr + '/axl/', headers=headers, data=payload,
                                auth=(cucmusername, cucmpassword), verify=False)
    # We encode the text response from POST request as utf8 and pretty print it to a file
    uglyxml = response.text.encode('utf8')
    xmldata = xml.dom.minidom.parseString(uglyxml)
    xml_pretty_str = xmldata.toprettyxml()
    with open('regcheckdevicelist.xml', 'w+') as file:
        file.write(xml_pretty_str)


# Function that dips into ccm db and executes SQL Query via SOAP. Returns devices in specified device pool.
def ucmdbdip_all(cucmipaddr, cucmversion, cucmpassword, cucmusername):
    # Define payload specific to ucmdbdip for all devices.
    payload = "<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" " \
              "xmlns:ns=\"http://www.cisco.com/AXL/API/10.5\">\n   <soapenv:Header/>\n   <soapenv:Body>\n      " \
              "<ns:executeSQLQuery sequence=\"\">\n         <sql>\n            SELECT d.name\n            FROM " \
              "device\n            AS d order by d.name\n         </sql>\n      </ns:executeSQLQuery>\n   " \
              "</soapenv:Body>\n</soapenv:Envelope> "
    # Header content, define db version and execute an SQL Query
    headers = {
        'SOAPAction': 'CUCM:DB ver=' + cucmversion + ' executeSQLQuery',
        'Content-Type': 'text/plain'
    }
    print()
    print('Collecting Data...')
    response = requests.request("POST", axlurl + cucmipaddr + '/axl/', headers=headers, data=payload,
                                auth=(cucmusername, cucmpassword), verify=False)
    # We encode the text response from POST request as utf8 and pretty print it to a file
    uglyxml = response.text.encode('utf8')
    xmldata = xml.dom.minidom.parseString(uglyxml)
    xml_pretty_str = xmldata.toprettyxml()
    with open('regcheckdevicelist.xml', 'w+') as file:
        file.write(xml_pretty_str)


# Function to hit AST interface using device name list generated by createdevstring function.
def checkregstate(cucmipaddr, cucmpassword, cucmusername, devname):
    try:
        response = requests.get(axlurl + cucmipaddr + '/ast/ASTIsapi.dll?OpenDeviceSearch?Type=&NodeName'
                                                       '=&SubSystemType=&Status=1&DownloadStatus=&MaxDevices=200'
                                                       '&Model=&SearchType=Name&Protocol=Any&SearchPattern=' + devname,
                                verify=False,
                                auth=(cucmusername, cucmpassword))
        devicelist = devname.split(",")
        xmlresponse = ET.fromstring(response.content)
        for item in xmlresponse.iter('DeviceReply'):
            # If the amount of devices found is not zero, proceed to look for the device name. If it's not found,
            # say so
            if item.attrib['TotalDevices'] == '0':
                print('No queried devices were registered per UCM AST API.')
                exit()
            else:
                continue
        xmltag = xmlresponse.findall('.//ReplyNode/Device')
        for response in xmltag:
            if response.attrib['Name'] in devicelist:
                ipaddr = response.attrib['IpAddress']
                device = response.attrib['Name']
                if response.attrib.get('Description') is not None:
                    descr = response.attrib['Description']
                else:
                    descr = "No Description"
                status = "Registered"
                with open(os.path.join(completepath, 'RegisteredDevicesReport' + timestr + '.txt'), 'a+') as rdr:
                    rdr.write(ipaddr + ' ' + device + ' ' + descr + ' ' + status + '\n')
                devicelist.remove(response.attrib['Name'])
                continue
        for devicename in devicelist:
            if response.attrib['Name'] != devicename:
                with open(os.path.join(completepath, 'UnregisteredDevicesReport' + timestr + '.txt'), 'a+') as udr:
                    udr.write('Device ' + devicename + ' is not registered.' + '\n')
                devicelist.remove(devicename)
    except requests.exceptions.ConnectionError:
        print('Connection error occurred. Unable to get HTTP Response from CUCM AST Interface. Check connectivity.')
    except requests.exceptions.Timeout:
        print('Connection timed out to UCM AST Interface.')


def querytype():
    print()
    choice = input("""
                      1: Search by Device Pool
                      2: Search by Text File
                      3: Search by All Devices
                      
                      Selection: """)
    if choice == "1":
        # User input collection provided by infocollect function
        cucmipaddr, cucmversion, cucmpassword, cucmusername = infocollect()
        # Collect device pool
        cucmdevicepool = collectdevicepool(cucmipaddr, cucmusername, cucmpassword, cucmversion)
        # Call DB Dip Function to execute sql query and prettyprint xml response to file, contains devices to parse
        ucmdbdip_dp(cucmipaddr, cucmversion, cucmpassword, cucmusername, cucmdevicepool)
        # Inform the user what device pool this report is for.
        print()
        print('Registration Report Below For Device Pool: ' + cucmdevicepool + '.')
        print()
        # Pull in device names to check for AST
        for devname in get_devicenames():
            # Hit AST interface to check reg status using csv string generated by createdevstring function
            checkregstate(cucmipaddr, cucmpassword, cucmusername, devname)
        print('Report for Unregistered Devices can be found in UnregisteredDevicesReport' + timestr + '.txt')
        print('Report for Registered Devices can be found in RegisteredDevicesReport' + timestr + '.txt')
        # Perform cleanup of files generated.
        os.remove("regcheckdevicelist.xml")
        os.remove("devicepoollist.xml")
    if choice == "2":
        try:
            # Devname is equal to the returned value from inputfetch(), which is a Comma Separated String drawn from
            # file.
            devname = inputfetch()
            # User input collection provided by infocollect function
            cucmipaddr, cucmversion, cucmpassword, cucmusername = infocollect()
            # Inform the user what device pool this report is for.
            print()
            print('Registration Report Below For Custom List.')
            print()
            checkregstate(cucmipaddr, cucmpassword, cucmusername, devname)
            print('Report for Unregistered Devices can be found in UnregisteredDevicesReport' + timestr + '.txt')
            print('Report for Registered Devies can be found in RegisteredDevicesReport' + timestr + '.txt')
        except FileNotFoundError as x:
            print(x)
    if choice == "3":
        # User input collection provided by infocollect function
        cucmipaddr, cucmversion, cucmpassword, cucmusername = infocollect()
        # Call DB Dip Function to execute sql query and prettyprint xml response to file, contains devices to parse
        ucmdbdip_all(cucmipaddr, cucmversion, cucmpassword, cucmusername)
        # Inform the user what device pool this report is for.
        print()
        print('Registration Report Below For All Devices.')
        print()
        # Pull in device names to check for AST
        for devname in get_devicenames():
            # Hit AST interface to check reg status using csv string generated by createdevstring function
            checkregstate(cucmipaddr, cucmpassword, cucmusername, devname)
        print('Report for Unregistered Devices can be found in UnregisteredDevicesReport' + timestr + '.txt')
        print('Report for Registered Devices can be found in RegisteredDevicesReport' + timestr + '.txt')
        # Perform cleanup of files generated.
        os.remove("regcheckdevicelist.xml")


# Check if tmp directory exists.
if os.path.exists(dirname) is False:
    os.mkdir(dirname)
    print('####################################################################################################')
    print('Folder ' + dirname + ' has been created in current directory. Generated reports will be found there.')
    print('####################################################################################################')
# Call Menu
querytype()
