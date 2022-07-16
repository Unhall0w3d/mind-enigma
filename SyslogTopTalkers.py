####
# Test Script for Parsing Syslogs for Dereg Event Top Talkers
# Script written by Kenneth Perry @ NOC Thoughts
####

# Required Modules
from getpass import getpass
import os
import time
import requests
import urllib3
import re

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


def setup():
    syslogpathcheck = os.path.exists(syslogpath)
    if not syslogpathcheck:
        os.makedirs(syslogpath)
        print("Syslog Download Folder was not found, creating folder CiscoSyslogs in CWD.")
    toptalkerspathcheck = os.path.exists(toptalkerspath)
    if not toptalkerspathcheck:
        os.makedirs(toptalkerspath)
        print("TopTalkersReports Folder was not found, creating folder TopTalkersReports in CWD.")


# Function to collect IP Address, Username and Password for CCM Publisher
def infocollect():
    ipaddr = str(input("What is the CCM Pub IP? : "))
    username = str(input("What is the username? : "))
    password = str(getpass("What is the password? : "))
    return ipaddr, username, password


# Function to perform SOAP request against CCM log collection service on port 8443.
def datapull(ipaddr, username, password):
    # URL for Log Collection Service on CCM
    url = "https://" + ipaddr + ":8443/logcollectionservice/services/DimeGetFileService"
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
    response = requests.request("POST", url, headers=headers, data=payload, auth=(username, password), verify=False)
    with open(os.path.join(syslogpath, 'CiscoSyslog_' + ipaddr + '_' + timestr + '.txt'), 'w') as file:
        file.write(response.text)
        file.close()


def parselogs():
    report = {}
    # with open(os.path.join(syslogpath, 'CiscoSyslog_' + ipaddr + '_' + timestr + '.txt'), 'r') as file:
    with open('CiscoSyslog.txt', 'r') as file:
        for line in file:
            qualifier = 'DeviceUnregistered'
            stepone = re.sub(r'[%\]]', "", line)
            steptwo = re.sub(r'\[', "^", stepone)
            stepthree = steptwo.split("^")
            if qualifier in line:
                data = (stepthree[1] + ' ' + stepthree[2] + ' ' + stepthree[5] + ' ' + stepthree[6])
                if data in report:
                    report[data] += 1
                if data not in report:
                    report[data] = 1
        with open(os.path.join(toptalkerspath, 'DeregTopTalkers' + timestr + '.txt'), "w+") as results:
            results.write("Count : Device Details\n")
            for info, count in sorted(report.items(), key=lambda x: x[1], reverse=True):
                results.write('%s : %s\n' % (count, info))


try:
    setup()
    ipaddr, username, password = infocollect()
    print("Downloading the CiscoSyslog file now from CUCM Publisher " + ipaddr + " .")
    datapull(ipaddr, username, password)
    print("Beginning Syslog Parse for Device Deregistration Events.")
    parselogs()
    print("Top talkers report is available in " + toptalkerspath + " .")
except Exception as e:
    print(e)
    print("We ran into an error. Will update with more detail in final script version.")
    exit()
