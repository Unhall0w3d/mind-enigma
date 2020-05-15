#!/usr/var/python
# -*- code:UTF-8 -*-

#####################################
# Script created by Ken Perry, 2020 #
#       NOC THOUGHTS BLOG           #
# https://nocthoughts.wordpress.com #
#####################################

# Modules Imported for Script Functionality
import subprocess
import time
import xml.etree.ElementTree
from io import BytesIO

import pycurl
import requests
import urllib3
import xml.dom.minidom
from getpass import getpass

# Define Variables
timestr = time.strftime("%Y%m%d-%H%M%S")


# Define Main Menu
def menu():
    print()
    choice = input("""
                      1: Pull Cisco Phone Info
                      2: Pull Cisco Phone Logs
                      3: CUCM Queries
                      4: Undefined
                      Q: Quit

                      Selection: """)

    if choice == "1":
        serialnumpull()
        menu()
    elif choice == "2":
        ips = phonecollection()
        [logcollect(ip_addr) for ip_addr in ips]
        print('############# Files have been stored in ~/ in an IP specific folder #############')
        menu()
    elif choice == "3":
        submenuchoice = input("""
                          1: Pull UCM Device Defaults
                          2: Undefined
                          Q: Quit

                          Selection: """)
        if submenuchoice == "1":
            devicedefaultsfetch()
            menu()
        elif submenuchoice == "2":
            print("Not Implemented")
            exit()
        elif submenuchoice == "q" or "Q":
            exit()
    elif choice == "4":
        print("Not Implemented")
        exit()
    elif choice == "q" or choice == "Q":
        exit()
    else:
        print("You must select an option on the menu.")
        print("Please try again.")
        menu()


# Log collection function that runs wget against consolelog url to pull recursively.
def logcollect(ip_addr):
    destfolder = str('~/')
    uris = list({
        '/CGI/Java/Serviceability?adapter=device.statistics.consolelog',
        '/localmenus.cgi?func=603',
        # '/NetworkConfiguration', Waiting on updated URL structure for phone models I don't have access to.
        '/Console_Logs.htm',
        '/Console_Logs.html',
        '/?adapter=device.statistics.consolelog',
    })
    for uri in uris:
        try:
            response = requests.get(f'http://{ip_addr}{uri}', timeout=6)
            if response.status_code == 200:
                subprocess.call(
                    'wget -T 5 --tries=2 -r --accept "*.log, messages*, *.tar.gz" http://' + ip_addr +
                    uri + ' -P ' + destfolder,
                    shell=True)
        except requests.exceptions.ConnectionError:
            print('Far end ' + ip_addr + 'has closed the connection.')
        except requests.exceptions.Timeout:
            print('Connection to ' + ip_addr + ' timed out. Trying next.')
        except Exception as e:
            print('The script failed. Contact script dev with details from your attempt and failure.')
            print(e)


# Phone Collection function that asks for a number for how many phones we'll check, then their IP addresses.
def phonecollection():
    num_phones = int(input('How many phones?: '))
    if type(num_phones) != int:
        print('Error: Expected Integer.')
        exit(1)
    ips = []
    for phonecount in range(num_phones):
        ips.append(input('What is the phone IP address?: '))
    return ips


def getxmldata(ip_addr, uri):
    buffer = BytesIO()
    curl = pycurl.Curl()
    _url = f'http://{ip_addr}{uri}'
    curl.setopt(pycurl.CONNECTTIMEOUT, 5)
    curl.setopt(curl.URL, _url)
    curl.setopt(curl.WRITEDATA, buffer)
    try:
        curl.perform()
        curl.close()
        return xml.etree.ElementTree.fromstring((buffer.getvalue()))
    except pycurl.error:
        print('Connection Timed Out. No response after 5 seconds for ' + ip_addr + '. Trying next.')
        exit(1)


def serialnumpull():
    xmluris = ['/NetworkConfigurationX', '/DeviceInformationX']
    inputfile = input('What is the name of the input text file? (e.g. iplist.txt): ')
    with open(inputfile) as txtfile:
        lines = [line.rstrip() for line in txtfile]
        for line in txtfile:
            lines.append(line)
    for ipaddy in lines:
        try:
            for uri in xmluris:
                root = getxmldata(ipaddy, uri)
                if root == -1:
                    break
                _root = uri.strip('/X')
                for xmltag in root.iter(_root):
                    if xmltag.find('HostName') is not None:
                        macaddr = xmltag.find('HostName').text
                    if xmltag.find('modelNumber') is not None:
                        modelnum = xmltag.find('modelNumber').text
                    if xmltag.find('serialNumber') is not None:
                        serialnum = xmltag.find('serialNumber').text
                    else:
                        serialnum = "n/a"

                    for i in range(2):
                        if xmltag.find('CallManager%s' % (i + 1)) is not None:
                            if xmltag.find('CallManager%s' % (i + 1)).text.find('Active') != -1:
                                cucmreg = xmltag.find('CallManager%s' % (i + 1)).text

            if root == -1:
                continue
            print()
            print("IP:", ipaddy, "DeviceName:", macaddr, "Model:",
                  modelnum, "Serial Number:", serialnum, "Reg State:", cucmreg)
        except Exception as m:
            print(m)
            exit(2)
    return


def devicedefaultsfetch():
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
              "xmlns:ns=\"http://www.cisco.com/AXL/API/" + version + "\">\n<!--Like https://[CCM-IP-ADDRESS]/ccmadmin > Device > " \
              "Device Settings > Device Defaults -->\n   <soapenv:Header/>\n   <soapenv:Body>\n      <ns:executeSQLQuery " \
              "sequence=\"\">\n         <sql>\n        SELECT count(dev.tkmodel), tp.name, defaults.tkdeviceprotocol, " \
              "defaults.loadinformation, dev.tkmodel AS tkmodel \n        FROM device AS dev \n        INNER JOIN " \
              "TypeProduct AS tp ON dev.tkmodel=tp.tkmodel \n        INNER JOIN defaults as defaults ON " \
              "tp.tkmodel=defaults.tkmodel \n        WHERE (dev.name like 'SEP%' or dev.name like 'ATA%') \n        GROUP " \
              "BY dev.tkmodel, tp.name, defaults.loadinformation, defaults.tkdeviceprotocol\n         </sql>\n      " \
              "</ns:executeSQLQuery>\n   </soapenv:Body>\n</soapenv:Envelope> "

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
    print('Data Collected. Please see file DeviceDefaults' + timestr + ccmip + '.xml.')

    with open('DeviceDefaults' + timestr + ccmip + '.xml', 'w+') as file:
        file.write(xml_pretty_str)


# Call Menu
menu()
