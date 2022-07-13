####
# Test Script for Parsing Syslogs for Dereg Event Top Talkers
####

import requests
import urllib3
from getpass import getpass

# Define disablement of HTTPS Insecure Request error message.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def infocollect():
    ipaddr = str(raw_input("What is the CCM Pub IP? : "))
    username = str(raw_input("What is the username? : "))
    password = str(getpass("What is the password? : "))
    return ipaddr, username, password


def datapull(ipaddr, username, password):
    # URL to hit for request against axl
    url = "https://" + ipaddr + ":8443/logcollectionservice/services/DimeGetFileService"
    payload = "<soapenv:Envelope xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:soap=\"http://schemas.cisco.com/ast/soap/\">\n<soapenv:Header/>\n<soapenv:Body>\n<soap:GetOneFile soapenv:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">\n<FileName>/var/log/active/CiscoSyslog</FileName>\n</soap:GetOneFile>\n</soapenv:Body>\n</soapenv:Envelope>"
    headers = {
    'SOAPAction': 'http://schemas.cisco.com/ast/soap/action/#LogCollectionPort#GetOneFile',
    'Content-Type': 'text/plain'
    }

    response = requests.request("POST", url, headers=headers, data=payload, auth=(username, password), verify=False)
    fileoutput = response.text.encode( ' utf-8 ' )
    with open( 'CiscoSyslog.txt ', "w" ) as file:
        file.write(fileoutput)


ipaddr, username, password = infocollect()
datapull(ipaddr, username, password)

print(" The Cisco Syslog file should be in the same Dir as the script. Good luck! ")

exit()
