#!/usr/var/python
# -*- code:UTF-8 -*-
import requests
import time
import urllib3
import xml.dom.minidom

# Define disablement of HTTPS Insecure Request error message.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Define user input required for script; pub ip, username, pw
ccmip = str(input('What is the CUCM Pub IP?: '))
myusername = str(input('What is the GUI Username?: '))
mypassword = str(input('What is the GUI Password?: '))

# Define datetime variable
timestr = time.strftime("%Y%m%d-%H%M%S")

# URL to hit for request against axl
url = ('https://' + ccmip + '/axl/')

# Payload to send; soap envelope
payload = "<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" " \
          "xmlns:ns=\"http://www.cisco.com/AXL/API/10.5\">\n<!--Like https://[CCM-IP-ADDRESS]/ccmadmin > Device > " \
          "Device Settings > Device Defaults -->\n   <soapenv:Header/>\n   <soapenv:Body>\n      <ns:executeSQLQuery " \
          "sequence=\"\">\n         <sql>\n        SELECT count(dev.tkmodel), tp.name, defaults.tkdeviceprotocol, " \
          "defaults.loadinformation, dev.tkmodel AS tkmodel \n        FROM device AS dev \n        INNER JOIN " \
          "TypeProduct AS tp ON dev.tkmodel=tp.tkmodel \n        INNER JOIN defaults as defaults ON " \
          "tp.tkmodel=defaults.tkmodel \n        WHERE (dev.name like 'SEP%' or dev.name like 'ATA%') \n        GROUP " \
          "BY dev.tkmodel, tp.name, defaults.loadinformation, defaults.tkdeviceprotocol\n         </sql>\n      " \
          "</ns:executeSQLQuery>\n   </soapenv:Body>\n</soapenv:Envelope> "

# Header content, define db version and execute an SQL Query
headers = {
  'SOAPAction': 'CUCM:DB ver=10.5 executeSQLQuery',
  'Content-Type': 'text/plain'
}

# Here's where we send a POST message out to CUCM, we don't verify certificates.
response = requests.request("POST", url, headers=headers, data=payload, auth=(myusername, mypassword), verify=False)

uglyxml = response.text.encode('utf8')
xml = xml.dom.minidom.parseString(uglyxml)
xml_pretty_str = xml.toprettyxml()
print(xml_pretty_str)

with open('DeviceDefaults' + timestr + ccmip + '.xml', 'w+') as file:
    file.write(xml_pretty_str)