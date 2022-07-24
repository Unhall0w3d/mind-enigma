####
# Test Script for Parsing Syslogs for Dereg Event Top Talkers
# Script written by Kenneth Perry @ NOC Thoughts
####
# Required Modules
import itertools
import os
import re
import shutil
import time

from getpass import getpass
from logging import exception

import paramiko
import requests
import urllib3
from requests.auth import HTTPBasicAuth

# Disablement of HTTPS Insecure Request error message.
# noinspection PyUnresolvedReferences
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# DateTime String
timestr = time.strftime("%Y%m%d-%H%M%S")
# Exit text
infoexit = "Info: Exiting ... "
# Directory and File Vars
syslogstore = 'CiscoSyslogs'
toptalkersstore = 'TopTalkersReports'
datetime = (timestr + '\\')
dir_path = os.getcwd()
syslogpath = os.path.join(dir_path, syslogstore)
downloaddir = os.path.join(syslogpath, datetime)
toptalkerspath = os.path.join(dir_path, toptalkersstore)


# Check if required directories exist and create if needed
def setup():
    print("Info: Checking if required directories exist, if not, creating them.")
    syslogpathcheck = os.path.exists(syslogpath)
    toptalkerspathcheck = os.path.exists(toptalkerspath)
    downloaddirpathcheck = os.path.exists(downloaddir)
    if not syslogpathcheck:
        os.makedirs(syslogpath)
        print("Info: Creating folder CiscoSyslogs in " + dir_path)
    if not downloaddirpathcheck:
        os.makedirs(downloaddir)
        print("Info: Creating folder " + datetime + " in " + syslogpath)
    if not toptalkerspathcheck:
        os.makedirs(toptalkerspath)
        print("Info: Creating folder TopTalkersReports in " + dir_path)


# Collect IP Address, Username and Password for CCM Publisher
def infocollect():
    ipaddr = str(input("Collect: CCM Pub IP? : "))
    username = str(input("Collect: GUI Username? : "))
    password = getpass("Collect: GUI Password? : ")
    usernameos = str(input("Collect: OS Username? : "))
    passwordos = getpass("Collect: OS Password? : ")
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
def netrequests():
    _sshconn = paramiko.SSHClient()
    _sshconn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ucnodes = []
    headers = {
        'SOAPAction': 'http://schemas.cisco.com/ast/soap/action/#LogCollectionPort#GetOneFile',
        'Content-Type': 'text/plain'
    }
    try:
        _sshconn.connect(hostname=ipaddr, port=22, username=usernameos, password=passwordos, timeout=300,
                         banner_timeout=300)
        invokeshell = _sshconn.invoke_shell()
        receivestr(invokeshell, '')
        print('Info: Connected to Publisher ... ')
        buffer = receivestr(invokeshell, 'show network cluster\n')
        networkinfo = buffer.split('\r\n')
        regexip = re.compile('((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|['
                             '1-9]?[0-9])')
        for node in networkinfo:
            if 'callmanager' in node and re.search(regexip, node):
                iplist = re.search(regexip, node)
                if iplist.group(0) not in ucnodes:
                    ucnodes.append(iplist.group(0))
        _sshconn.close()
        print('Info: CUCM Servers Found')
        print('Servers: ' + ', '.join(ucnodes))
        for ip in ucnodes:
            files = []
            url = "https://" + ip + ":8443/logcollectionservice/services/DimeGetFileService"
            _sshconn.connect(hostname=ip, port=22, username=usernameos, password=passwordos,
                             timeout=300, banner_timeout=300)
            invokeshell = _sshconn.invoke_shell()
            receivestr(invokeshell, '')
            print('Info: Connected to ' + ip + ' ... ')
            buffer2 = receivestr(invokeshell, 'file list activelog /syslog/ detail \n')
            output = buffer2.split('\r\n')
            searchterm = re.compile('.*Syslo.*')
            for line in output:
                check = re.search(searchterm, line)
                if check is not None:
                    files.append(check.group(0))
            flist = [filename[35:] for filename in files]
            print('Info: Found files for download on ' + ip)
            print('Files: ' + ', '.join(flist))
            _sshconn.close()
            for fname in flist:
                payload = "<soapenv:Envelope xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" " \
                          "xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" " \
                          "xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" " \
                          "xmlns:soap=\"http://schemas.cisco.com/ast/soap/\">\n<soapenv:Header/>\n<soapenv:Body>\n<soap" \
                          ":GetOneFile soapenv:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">\n<FileName>/var" \
                          "/log" \
                          "/active/syslog/" + fname + "</FileName>\n</soap:GetOneFile>\n</soapenv:Body>\n</soapenv:Envelope> "
                response = requests.request("POST", url, headers=headers, data=payload,
                                            auth=HTTPBasicAuth(username, password), verify=False, timeout=10)
                print('Info: Downloading ' + fname + ' from ' + ip + ' ... ')
                dnldfile = (ip + '_' + fname)
                with open(os.path.join(downloaddir, dnldfile), 'w+', encoding='utf-8') as file:
                    file.write(response.text[872:])
                    file.close()
        print('Info: Syslogs downloaded to ' + downloaddir)
    except Exception as z:
        print('Error: Failed to establish connection to UCM Publisher via SSH', z)
        _sshconn.close()


# Parse downloaded CiscoSyslog file for strings and generate report.
def parselogs():
    unregreport = {}
    endpointreport = {}
    tranconnreport = {}
    siptrunkreport = {}
    searchlist = ['-DeviceUnregistered', '-EndPointUnregistered', 'TransientConnection', '-SIPTrunk']
    disqualifier = 'SyslogSeverityMatchFound'
    regexlist1 = ['DeviceName=', 'Description=', 'IPAddress=', 'Reason=', 'Protocol=', 'NodeID=']
    regexlist2 = ['DeviceName=', 'IPAddress=', 'MACAddress=', 'Reason=', 'Protocol=', 'NodeID=']
    regexlist3 = ['DeviceName=', 'UnavailableRemotePeersWithReasonCode=', 'NodeID=']
    found = '.*?\]'
    print('Info: Loading files for parsing ... ')
    for syslg in os.listdir(downloaddir):
        with open(os.path.join(downloaddir, syslg), 'r', encoding='utf-8') as logfile:
            for line in logfile:
                devicelist = []
                endpointlist = []
                tranconnlist = []
                siptrunklist = []
                if disqualifier in line:
                    continue
                for search in searchlist:
                    searchpattern = re.compile(r'{}'.format(search))
                    searchresult = searchpattern.search(line)
                    if searchresult is None:
                        continue
                    elif searchresult is not None:
                        if searchresult.group(0) == searchlist[0]:
                            for prefix in regexlist1:
                                regex = prefix + found
                                pattern = re.compile(r'{}'.format(regex))
                                result = pattern.search(line)
                                if result is not None:
                                    devicelist.append(result.group(0).strip(']'))
                                elif result is None:
                                    devicelist.append(prefix + "None")
                            devicedata = (','.join(devicelist))
                            if devicedata in unregreport:
                                unregreport[devicedata] += 1
                            elif devicedata not in unregreport:
                                unregreport[devicedata] = 1
                        if searchresult.group(0) == searchlist[1]:
                            for prefix in regexlist1:
                                regex = prefix + found
                                pattern = re.compile(r'{}'.format(regex))
                                result = pattern.search(line)
                                if result is not None:
                                    endpointlist.append(result.group(0).strip(']'))
                                elif result is None:
                                    endpointlist.append(prefix + "None")
                            endpointdata = (','.join(endpointlist))
                            if endpointdata in endpointreport:
                                endpointreport[endpointdata] += 1
                            elif endpointdata not in endpointreport:
                                endpointreport[endpointdata] = 1
                        if searchresult.group(0) == searchlist[2]:
                            for prefix in regexlist2:
                                regex = prefix + found
                                pattern = re.compile(r'{}'.format(regex))
                                result = pattern.search(line)
                                if result is None:
                                    tranconnlist.append(prefix + "None")
                                elif result is not None:
                                    tranconnlist.append(result.group(0).strip(']'))
                            tranconndata = (','.join(tranconnlist))
                            if tranconndata in tranconnreport:
                                tranconnreport[tranconndata] += 1
                            elif tranconndata not in tranconnreport:
                                tranconnreport[tranconndata] = 1
                        if searchresult.group(0) == searchlist[3]:
                            for prefix in regexlist3:
                                regex = prefix + found
                                pattern = re.compile(r'{}'.format(regex))
                                result = pattern.search(line)
                                if result is None:
                                    siptrunklist.append(prefix + "None")
                                elif result is not None:
                                    commas = result.group(0).replace(',' , '')
                                    siptrunklist.append(commas.strip('\]'))
                            siptrunkdata = (','.join(siptrunklist))
                            if siptrunkdata in siptrunkreport:
                                siptrunkreport[siptrunkdata] += 1
                            elif siptrunkdata not in siptrunkreport:
                                siptrunkreport[siptrunkdata] = 1
            logfile.close()
    return unregreport, tranconnreport, siptrunkreport, endpointreport


def createreport():
    bigseparator = "-------------------------------------------------------\n"
    smallseparator = "------\n"
    newline = "\n\n"
    placer = '%s,%s\n'
    deregheader = "Count,DeviceName,Description,IPAddress,MACAddress,ReasonCode,Protocol,NodeID\n"
    unregout = list(itertools.islice(sorted(unregreport.items(), key=lambda x: x[1], reverse=True), 10))
    endpointout = list(itertools.islice(sorted(endpointreport.items(), key=lambda x: x[1], reverse=True), 10))
    tranconnout = list(itertools.islice(sorted(tranconnreport.items(), key=lambda x: x[1], reverse=True), 10))
    siptrunkout = list(itertools.islice(sorted(siptrunkreport.items(), key=lambda x: x[1], reverse=True), 10))
    print("Info: Constructing TopTalkers report ... ")
    with open(os.path.join(toptalkerspath, 'TopTalkersReport_' + timestr + '.csv'), 'w+', encoding='utf-8') as topresults:
        topresults.write("Device Unregistered\n")
        topresults.write(bigseparator)
        topresults.write(deregheader)
        for info1, count1 in unregout:
            topresults.write(placer % (count1, info1))
        topresults.write(smallseparator)
        topresults.write(newline)
        topresults.write("Endpoint Unregistered\n")
        topresults.write(bigseparator)
        topresults.write(deregheader)
        for info2, count2 in endpointout:
            topresults.write(placer % (count2, info2))
        topresults.write(smallseparator)
        topresults.write(newline)
        topresults.write("Transient Connections\n")
        topresults.write(bigseparator)
        topresults.write("Count,DeviceName,IPAddress,MACAddress,ReasonCode,Protocol,NodeID\n")
        for info3, count3 in tranconnout:
            topresults.write(placer % (count3, info3))
        topresults.write(smallseparator)
        topresults.write(newline)
        topresults.write("SIP Trunk Out of Service\n")
        topresults.write(bigseparator)
        topresults.write("Count,DeviceName,PeerIP_Port_Reason,NodeID\n")
        for info4, count4 in siptrunkout:
            topresults.write(placer % (count4, info4))
        topresults.close()
    print("Info: Top talkers report (top 10) is available in " + toptalkerspath + ".")
    while True:
        try:
            fullreport = input("Collect: Do you want the full report? (Y\\n): ").lower()
            if fullreport == "n":
                print(infoexit)
                exit()
            elif fullreport == "y":
                break
            elif fullreport != "n" or "y":
                raise exception("Invalid Key")
        except Exception:
            print("Info: Please input Y or N. Press Enter for the default.")
            continue
    print("Info: Constructing Full report ... ")
    with open(os.path.join(toptalkerspath, 'FullReport_' + timestr + '.csv'), 'w+', encoding='utf-8') as results:
        results.write("Device Unregistered\n")
        results.write(bigseparator)
        results.write(deregheader)
        for info1, count1 in sorted(unregreport.items(), key=lambda x: x[1], reverse=True):
            results.write(placer % (count1, info1))
        results.write(smallseparator)
        results.write(newline)
        results.write("Endpoint Unregistered\n")
        results.write(bigseparator)
        results.write(deregheader)
        for info2, count2 in sorted(endpointreport.items(), key=lambda x: x[1], reverse=True):
            results.write(placer % (count2, info2))
        results.write(smallseparator)
        results.write(newline)
        results.write("Transient Connections\n")
        results.write(bigseparator)
        results.write(deregheader)
        for info3, count3 in sorted(tranconnreport.items(), key=lambda x: x[1], reverse=True):
            results.write(placer % (count3, info3))
        results.write(smallseparator)
        results.write(newline)
        results.write("SIP Trunk Out of Service\n")
        results.write(bigseparator)
        results.write("Count,DeviceName,PeerIP_Port_Reason,NodeID\n")
        for info4, count4 in sorted(siptrunkreport.items(), key=lambda x: x[1], reverse=True):
            results.write(placer % (count4, info4))
        results.close()
    print("Info: Full report is available in " + toptalkerspath + ".")


def cleanup():
    while True:
        try:
            cleanup = input("Collect: Delete downloaded log files? (Y\\n): ").lower()
            if cleanup == "n":
                print(infoexit)
                exit()
            elif cleanup == "y":
                shutil.rmtree(downloaddir)
                break
            elif cleanup != "n" or "y":
                print("Info: Please input Y or N. Press Enter for the default.")
                raise exception("Unexpected Key")
        except OSError as c:
            print("Error: %s : %s" % (downloaddir, c.strerror))
            print("Error: File cleanup requires write and execute permissions on directory " + downloaddir + ".")
            print(infoexit)
            exit()
        except Exception:
            continue


if __name__ == "__main__":
    try:
        setup()
        ipaddr, username, password, usernameos, passwordos = infocollect()
        netrequests()
        unregreport, tranconnreport, siptrunkreport, endpointreport = parselogs()
        createreport()
        cleanup()
        exit()
    except Exception as e:
        print(e)
        exit()
