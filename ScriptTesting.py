#!/usr/var/python
# -*- code:UTF-8 -*-

import time
import requests
import urllib3
import xml.dom.minidom
from getpass import getpass

# Define Variables
timestr = time.strftime("%Y%m%d-%H%M%S")


def jabberlastloginreport():
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
              "<ns:executeSQLQuery sequence=\"\">\n         <sql>\n            SELECT e.userid, cd.timelastaccessed\n " \
              "           FROM enduser as e, credentialdynamic as cd, credential as cr\n            WHERE " \
              "e.pkid=cr.fkenduser and e.tkuserprofile=1 and e.primarynodeid is not null and cr.tkcredential=3 and " \
              "cr.pkid=cd.fkcredential\n            ORDER by cd.timelastaccessed\n         </sql>\n      " \
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
    print('Data Collected. Please see file JabberLastLogin' + timestr + ccmip + '.xml.')

    with open('JabberLastLogin' + timestr + ccmip + '.xml', 'w+') as file:
        file.write(xml_pretty_str)


jabberlastloginreport()
