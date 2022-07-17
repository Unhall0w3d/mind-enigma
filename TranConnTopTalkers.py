####
# Test Script for Parsing Syslogs for Dereg Event Top Talkers
# Script written by Kenneth Perry @ NOC Thoughts
####

# Required Modules
from getpass import getpass
import os
import time
import requests
from requests.auth import HTTPBasicAuth
import urllib3
import re
import xml.etree.ElementTree as ET

# Define disablement of HTTPS Insecure Request error message.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Define Variables for File Creation
# Time
timestr = time.strftime("%Y%m%d-%H%M%S")
# Directory and File Vars
syslogstore = 'CiscoSyslogs'
toptalkersstore = 'TopTalkersReports'
dir_path = os.getcwd()
syslogpath = os.path.join(dir_path, syslogstore)
toptalkerspath = os.path.join(dir_path, toptalkersstore)


# Function to check if required directories exist. If not, create them.
def setup():
    print("Checking if required directories exist, if not, creating them.")
    syslogpathcheck = os.path.exists(syslogpath)
    toptalkerspathcheck = os.path.exists(toptalkerspath)
    if not syslogpathcheck:
        os.makedirs(syslogpath)
        print("Creating folder CiscoSyslogs in " + dir_path)
    if not toptalkerspathcheck:
        os.makedirs(toptalkerspath)
        print("Creating folder TopTalkersReports in " + dir_path)


# Function to collect IP Address, Username and Password for CCM Publisher
def infocollect():
    ipaddr = str(input("What is the CCM Pub IP? : "))
    username = str(input("What is the username? : "))
    password = str(input("What is the password? : "))
    return ipaddr, username, password


# Function to collect CCM Subscriber IP addresses.
def listucm():
    try:
        ucnodes = []
        url = "https://" + ipaddr + ":8443/ast/ASTIsapi.dll?GetPreCannedInfo&Items=getCtiManagerInfoRequest"
        response = requests.request("POST", url, auth=HTTPBasicAuth(username, password), verify=False, timeout=10)
        if response.status_code != 200:
            print("Error! Failed to collect subscriber details. Check your credentials and reachability. Ensure the "
                  "proper services are started.")
            exit()
        root = ET.fromstring(response.text)
        for node in root.iter('CtiNode'):
            ucnodes.append(node.get('Name'))
        print('Found Cluster Nodes')
        print('\n'.join(ucnodes))
        return ucnodes
    except Exception as e:
        print("We encountered an error while pulling CCM Subscriber info. Exiting.")
        print(e)
        exit()


# Function to perform SOAP request against CCM log collection service on port 8443.
def datapull():
    payload = "<soapenv:Envelope xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" " \
              "xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" " \
              "xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" " \
              "xmlns:soap=\"http://schemas.cisco.com/ast/soap/\">\n<soapenv:Header/>\n<soapenv:Body>\n<soap" \
              ":GetOneFile soapenv:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">\n<FileName>/var/log" \
              "/active/syslog/CiscoSyslog</FileName>\n</soap:GetOneFile>\n</soapenv:Body>\n</soapenv:Envelope> "
    headers = {
        'SOAPAction': 'http://schemas.cisco.com/ast/soap/action/#LogCollectionPort#GetOneFile',
        'Content-Type': 'text/plain'
    }
    for ccmip in ucnodes:
        url = "https://" + ccmip + ":8443/logcollectionservice/services/DimeGetFileService"
        response = requests.request("POST", url, headers=headers, data=payload, auth=HTTPBasicAuth(username, password), verify=False, timeout=10)
        with open(os.path.join(syslogpath, 'CiscoSyslog.txt'), 'a+') as file:
            file.write(response.text)
    file.close()


def parselogs():
    report = {}
    index = 0
    with open(os.path.join(syslogpath, 'CiscoSyslog_' + ipaddr + '_' + timestr + '.txt'), 'r') as file:
        for line in file:
            qualifier = 'DeviceTransientConnection'
            disqualifier = 'SyslogSeverityMatchFound'
            stepone = re.sub(r'[%\]]', "", line)
            steptwo = re.sub(r'\[', "^", stepone)
            stepthree = steptwo.split("^")
            if qualifier and disqualifier in line:
                index += 1
            elif qualifier in line:
                data = (stepthree[2] + ',' + stepthree[3] + ',' + stepthree[5] + ',' + stepthree[6] + ',' + stepthree[10])
                if data in report:
                    report[data] += 1
                if data not in report:
                    report[data] = 1
        with open(os.path.join(toptalkerspath, 'TranConnTopTalkers_' + timestr + '.csv'), "w+") as results:
            results.write("Count,DeviceName,IPAddress,ReasonCode,Protocol,NodeID_InfoText\n")
            for info, count in sorted(report.items(), key=lambda x: x[1], reverse=True):
                results.write('%s,%s\n' % (count, info))
        results.close()
    file.close()


try:
    setup()
    print("This script pulls cluster node details via SOAP. If CCM nodes use FQDN/Hostname please ensure they are "
          "resolvable through DNS or the connection attempt will fail.")
    ipaddr, username, password = infocollect()
    ucnodes = listucm()
    print("Downloading the CiscoSyslog file now from the cluster.")
    print(" ")
    datapull()
    print("Beginning Syslog Parse for Transient Connection events.")
    print(" ")
    print("Constructing top talkers report in .csv format.")
    print(" ")
    parselogs()
    print("Top talkers report is available in " + toptalkerspath + ".")
    print(" ")
    print("Cleaning up")
    os.remove(os.path.join(syslogpath, 'CiscoSyslog.txt'))
except Exception as e:
    print(e)
    exit()
