####
# Test Script for Parsing Syslogs for Dereg Event Top Talkers
# Script written by Kenneth Perry @ NOC Thoughts
####

# Required Modules
import requests
import urllib3
from getpass import getpass

# Define disablement of HTTPS Insecure Request error message.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Function to collect IP Address, Username and Password for UCM Publisher
def infocollect():
    ipaddr = str(input("What is the CCM Pub IP? : "))
    username = str(input("What is the username? : "))
    password = str(getpass("What is the password? : "))
    return ipaddr, username, password


# Function to perform SOAP request against CCM log collection service on port 8443.
def datapull(ipaddr, username, password):
    url = "https://" + ipaddr + ":8443/logcollectionservice/services/DimeGetFileService"
    payload = "<soapenv:Envelope xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:soap=\"http://schemas.cisco.com/ast/soap/\">\n<soapenv:Header/>\n<soapenv:Body>\n<soap:GetOneFile soapenv:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">\n<FileName>/var/log/active/syslog/CiscoSyslog</FileName>\n</soap:GetOneFile>\n</soapenv:Body>\n</soapenv:Envelope>"
    headers = {
    'SOAPAction': 'http://schemas.cisco.com/ast/soap/action/#LogCollectionPort#GetOneFile',
    'Content-Type': 'text/plain'
    }

    response = requests.request("POST", url, headers=headers, data=payload, auth=(username, password), verify=False)
    with open('CiscoSyslog.txt', "w") as file:
        file.write(response.text)


try:
    ipaddr, username, password = infocollect()
    print("Downloading the CiscoSyslog now.")
    datapull(ipaddr, username, password)
    print("The CiscoSyslog file was placed in X Directory.")
except Exception as e:
    print("We ran into an error. Will update with more detail in final script version.")
    exit()
