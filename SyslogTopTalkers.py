####
# Test Script for Parsing Syslogs for Dereg Event Top Talkers
####

import requests
import urllib3
from getpass import getpass

ipaddr = input("What is the CCM Pub IP? : ")
username = input("What is the username? : ")
password = getpass("What is the password? : ")


def datapull(ipaddr, username, password):
    # URL to hit for request against axl
    url = "https://" + ipaddr + ":8443/logcollectionservice/services/DimeGetFileService"
    payload = "<soapenv:Envelope xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:soap=\"http://schemas.cisco.com/ast/soap/\">\n<soapenv:Header/>\n<soapenv:Body>\n<soap:GetOneFile soapenv:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">\n<FileName>/var/log/active/CiscoSyslog</FileName>\n</soap:GetOneFile>\n</soapenv:Body>\n</soapenv:Envelope>"
    headers = {
    'SOAPAction': 'http://schemas.cisco.com/ast/soap/action/#LogCollectionPort#GetOneFile',
    'Content-Type': 'text/plain'
    }

    response = requests.request("POST", url, headers=headers, data=payload, auth=(username, password), verify=False)
    fileoutput = response.decode( ' utf-8 ' )
    with open( 'CiscoSyslog.txt ' ) as file:
        file.write(fileoutput)

print(" The Cisco Syslog file should be in the same Dir as the script. Good luck! ")

exit()
