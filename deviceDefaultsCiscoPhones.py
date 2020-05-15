#!/usr/var/python
# -*- code:UTF-8 -*-
import time

import requests
import urllib3
import xml.dom.minidom


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


devicedefaultsfetch()
