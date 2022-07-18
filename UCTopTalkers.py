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
import re
import urllib3
import paramiko


# Disablement of HTTPS Insecure Request error message.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# DateTime String
timestr = time.strftime("%Y%m%d-%H%M%S")
# Directory and File Vars
syslogstore = 'CiscoSyslogs'
toptalkersstore = 'TopTalkersReports'
dir_path = os.getcwd()
syslogpath = os.path.join(dir_path, syslogstore)
toptalkerspath = os.path.join(dir_path, toptalkersstore)


# Check if required directories exist and create if needed
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


# Collect IP Address, Username and Password for CCM Publisher
def infocollect():
    ipaddr = str(input("What is the CCM Pub IP? : "))
    username = str(input("What is the GUI username? : "))
    password = getpass("What is the GUI password? : ")
    usernameos = str(input("What is the OS username? : "))
    passwordos = getpass("What is the OS password? : ")
    return ipaddr, username, password, usernameos, passwordos


# Processing command input, needed in listucm()
def receivestr(sshconn, cmd):
    buffer = ''
    prompt = 'admin:'
    if cmd != '':
        sshconn.send(cmd)
    while not sshconn.recv_ready():
        time.sleep(.5)
        buffer += str(sshconn.recv(65535), 'utf-8')
        if buffer.endswith(prompt):
            break
    return buffer


# Connect to UCM Pub on port 22|Collect output from show network cluster to construct ip list for log download
def listucm():
    _sshconn = paramiko.SSHClient()
    _sshconn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ucnodes = []
    try:
        _sshconn.connect(hostname=ipaddr, port=22, username=usernameos, password=passwordos, timeout=300,
                         banner_timeout=300)
        __sshConn = _sshconn.invoke_shell()
        receivestr(__sshConn, '')
        print('Info: Connected to Platform ... ')
        buffer = receivestr(__sshConn, 'show network cluster\n')
        networkinfo = buffer.split('\r\n')
        regexip = re.compile('((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|['
                             '1-9]?[0-9])')
        for node in networkinfo:
            if 'callmanager' in node and re.search(regexip, node):
                iplist = re.search(regexip, node)
                if iplist not in ucnodes:
                    ucnodes.append(iplist.group(0))
        _sshconn.close()
        return ucnodes
    except Exception as z:
        print('Error: Failed to establish connection to UCM Publisher via SSH', z)
        _sshconn.close()


# Perform SOAP request against CCM log collection service on port 8443 for each IP in list
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
            response.close()
    file.close()


# Parse downloaded CiscoSyslog file for strings and generate report.
def parselogs():
    unregreport = {}
    tranconnreport = {}
    siptrunkreport = {}
    endpointreport = {}
    index = 0
    with open(os.path.join(syslogpath, 'CiscoSyslog.txt'), 'r') as file:
        for line in file:
            searchlist = ['-DeviceUnregistered', '-EndPointUnregistered', '-DeviceTransientConnection', '-SIPTrunkOOS']
            disqualifier = 'SyslogSeverityMatchFound'
            stepone = re.sub(r'[%\]]', "", line)
            steptwo = re.sub(r'\[', "^", stepone)
            stepthree = steptwo.split("^")
            for qualifier in searchlist:
                if qualifier and disqualifier in line:
                    index += 1
                elif qualifier in line:
                    if qualifier is searchlist[0]:
                        unregdata = (stepthree[1] + ',' + stepthree[2] + ',' + stepthree[5] + ',' + stepthree[6] + ',' + stepthree[12])
                        if unregdata in unregreport:
                            unregreport[unregdata] += 1
                        elif unregdata not in unregreport:
                            unregreport[unregdata] = 1
                    elif qualifier is searchlist[1]:
                        endpointdata = (stepthree[1] + ',' + stepthree[2] + ',' + stepthree[3] + ',' + stepthree[6] + ',' + stepthree[7] + ',' + stepthree[15])
                        if endpointdata in endpointreport:
                            endpointreport[endpointdata] += 1
                        elif endpointdata not in endpointreport:
                            endpointreport[endpointdata] = 1
                    elif qualifier is searchlist[2]:
                        tranconndata = (stepthree[1] + ',' + stepthree[2] + ',' + stepthree[3] + ',' + stepthree[5] + ',' + stepthree[6] + ',' + stepthree[10])
                        if tranconndata in tranconnreport:
                            tranconnreport[tranconndata] += 1
                        elif tranconndata not in tranconnreport:
                            tranconnreport[tranconndata] = 1
                    elif qualifier is searchlist[3]:
                        siptrunkdata = (stepthree[1] + ',' + stepthree[2] + ',' + stepthree[5])
                        if siptrunkdata in siptrunkreport:
                            siptrunkreport[siptrunkdata] += 1
                        elif siptrunkdata not in siptrunkreport:
                            siptrunkreport[siptrunkdata] = 1
        file.close()
    return unregreport, tranconnreport, siptrunkreport, endpointreport


def createreport():
    with open(os.path.join(toptalkerspath, 'DeregTopTalkers_' + timestr + '.csv'), "w+") as results:
        results.write("Device Unregistered\n")
        results.write("-------------------------------------------------------\n")
        results.write("Count,DeviceName,IPAddress,Description,ReasonCode,NodeID_InfoText\n")
        for info1, count1 in sorted(unregreport.items(), key=lambda x: x[1], reverse=True):
            results.write('%s,%s' % (count1, info1))
        results.write("------")
        results.write('\n\n\n')
        results.write("Endpoint Unregistered\n")
        results.write("-------------------------------------------------------\n")
        results.write("Count,DeviceName,IPAddress,Description,ReasonCode,NodeID_InfoText\n")
        for info2, count2 in sorted(endpointreport.items(), key=lambda x: x[1], reverse=True):
            results.write('%s,%s' % (count2, info2))
        results.write("------")
        results.write('\n\n\n')
        results.write("Transient Connections\n")
        results.write("-------------------------------------------------------\n")
        results.write("Count,SourcePort,DeviceName,IPAddress,ReasonCode,Protocol,NodeID_InfoText\n")
        for info3, count3 in sorted(tranconnreport.items(), key=lambda x: x[1], reverse=True):
            results.write('%s,%s' % (count3, info3))
        results.write("------")
        results.write('\n\n\n')
        results.write("SIP Trunk Out of Service\n")
        results.write("-------------------------------------------------------\n")
        results.write("Count,DeviceName,PeerIP_ReasonCode,NodeID_InfoText\n")
        for info4, count4 in sorted(siptrunkreport.items(), key=lambda x: x[1], reverse=True):
            results.write('%s,%s' % (count4, info4))
        results.close()


try:
    setup()
    ipaddr, username, password, usernameos, passwordos = infocollect()
    print("Finding cluster Subscriber IP addresses.")
    ucnodes = listucm()
    print("Downloading the CiscoSyslog file now from the cluster.")
    datapull()
    print("Beginning Syslog Parse for Device Deregistration events.")
    time.sleep(1)
    unregreport, tranconnreport, siptrunkreport, endpointreport = parselogs()
    print("Constructing top talkers report in .csv format.")
    time.sleep(1)
    createreport()
    print("-------------------------------------------------------")
    print("Top talkers report is available in " + toptalkerspath + ".")
    print("-------------------------------------------------------")
    print("Cleaning up")
    os.remove(os.path.join(syslogpath, 'CiscoSyslog.txt'))
except Exception as e:
    print(e)
    exit()
