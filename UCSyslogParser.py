import re
from pyparsing import Word, alphas, Suppress, Combine, nums, string, alphanums, OneOrMore, White, Optional
import itertools
import os
import shutil
import time
import pandas as pd
import xlsxwriter
import sys
import glob

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
tempstore = 'temp'
datetime = (timestr + '\\')
dir_path = os.getcwd()
syslogpath = os.path.join(dir_path, syslogstore)
downloaddir = os.path.join(syslogpath, datetime)
toptalkerspath = os.path.join(dir_path, toptalkersstore)
temppath = os.path.join(dir_path, tempstore)


# Check if required directories exist and create if needed
def setup():
    print("Info: Checking if required directories exist, if not, creating them.")
    syslogpathcheck = os.path.exists(syslogpath)
    toptalkerspathcheck = os.path.exists(toptalkerspath)
    downloaddirpathcheck = os.path.exists(downloaddir)
    temppathcheck = os.path.exists(temppath)
    if not syslogpathcheck:
        os.makedirs(syslogpath)
        print("Info: Creating folder CiscoSyslogs in " + dir_path)
    if not downloaddirpathcheck:
        os.makedirs(downloaddir)
        print("Info: Creating folder " + datetime + " in " + syslogpath)
    if not toptalkerspathcheck:
        os.makedirs(toptalkerspath)
        print("Info: Creating folder TopTalkersReports in " + dir_path)
    if not temppathcheck:
        os.makedirs(temppath)
        print("Info: Creating folder temp in " + dir_path)


# Collect IP Address, Username and Password for CCM Publisher
def infocollect():
    ipaddr = str(input("Collect: CCM Pub IP? : "))
    username = str(input("Collect: GUI Username? : "))
    password = getpass("Collect: GUI Password? : ")
    usernameos = str(input("Collect: OS Username? : "))
    passwordos = getpass("Collect: OS Password? : ")
    return ipaddr, username, password, usernameos, passwordos


# Processing command input, needed in netrequests()
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
# Connect to each ip and download identified logs
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
                    file.write(response.text[869:])
                    file.close()
        print('Info: Syslogs downloaded to ' + downloaddir)
    except Exception as z:
        print('Error: Failed to establish connection to UCM Server: ', z)
        _sshconn.close()


class Parser(object):
    def __init__(self):
        ints = Word(nums)
        punc = "-_.;"

        # Timestamp
        month = Word(string.ascii_uppercase, string.ascii_lowercase, exact=3)
        day = ints
        hour = Combine(ints + ":" + ints + ":" + ints)
        exhour = Combine(ints + ":" + ints + ":" + ints + "." + ints)
        year = ints

        timestamp = month + day + hour
        extimestamp = month + day + year + exhour
        tzdata = Word(string.ascii_uppercase, exact=3)

        # Hostname
        hostname = Word(alphanums + "-_.")

        # Local Syslog
        local = Word(alphanums)

        # Priority
        priority = ints

        # Server Type
        srvtype = Combine(Word(string.ascii_lowercase, exact=3) + Suppress(":"))

        # Message Number
        msgnum = Combine(ints + Suppress(":"))

        # Separator
        separator = ":   "

        # Message Type
        msgtype = Word("%:-_" + alphanums)

        # Device Name
        devname = Suppress("%[") + Combine("DeviceName=" + Optional(Word(alphanums + punc))) + Suppress("]")

        # Device IP
        devip = Suppress("[") + Combine("IPAddress=" + Word(nums + ".")) + Suppress("]")

        # Protocol
        protocol = Suppress("[") + Combine("Protocol=" + Word(alphas)) + Suppress("]")

        # Device Type
        devtype = Suppress("[") + Combine("DeviceType=" + ints) + Suppress("]")

        # Description
        descval = Combine(OneOrMore(Word(alphanums + punc) | White(' ', max=1) + ~White()))
        desc = Suppress("[") + Combine("Description=" + OneOrMore(descval)) + Suppress("]")

        # Reason Code
        reason = Suppress("[") + Combine("Reason=" + ints) + Suppress("]")
        reasoncode = Suppress("[") + Combine("ReasonCode=" + ints) + Suppress("]")

        # IP Attributes
        ipattrib = Suppress("[") + Combine("IPAddrAttributes=" + Word(nums + ".", asKeyword=True)) + Suppress("]")

        # Last Signal Received
        lastsig = Suppress("[") + Combine("LastSignalReceived=" + Word(alphanums, asKeyword=True)) + Suppress("]")

        # App ID
        # appid = Suppress("[") + "AppID=" + Word(printables + " ") + Suppress("]")
        appidval = Combine(OneOrMore(Word(alphas) | White(' ', max=1) + ~White()))
        appid = Suppress("[") + Combine("AppID=" + OneOrMore(appidval)) + Suppress("]")

        # Call State
        callstate = Suppress("[") + Combine("CallState=" + Word(alphanums + punc)) + Suppress("]")

        # Cluster ID
        cluster = Suppress("[") + Combine("ClusterID=" + Word(alphanums)) + Suppress("]")

        # Node ID
        node = Suppress("[") + Combine("NodeID=" + Word(alphanums)) + Suppress("]:")

        # Info Text
        infoval = Combine(OneOrMore(Word(alphas) | White(' ', max=1) + ~White()))
        info = OneOrMore(infoval)

        # Search Patterns - EndpointUnregistered
        self.__endpointall = timestamp + hostname + local + priority + srvtype + msgnum + hostname + extimestamp +\
            tzdata + separator + msgtype + devname + devip + protocol + devtype + desc + reason \
            + ipattrib + lastsig + appid + cluster + node + info
        self.__endpointnodesc = timestamp + hostname + local + priority + srvtype + msgnum + hostname + extimestamp + \
            tzdata + separator + msgtype + devname + devip + protocol + devtype + reason \
            + ipattrib + lastsig + appid + cluster + node + info
        self.__endpointnosigcall = timestamp + hostname + local + priority + srvtype + msgnum + hostname + extimestamp + \
            tzdata + separator + msgtype + devname + devip + protocol + devtype + desc + reason \
            + ipattrib + appid + cluster + node + info
        self.__endpointnosigdesc = timestamp + hostname + local + priority + srvtype + msgnum + hostname + extimestamp + \
            tzdata + separator + msgtype + devname + devip + protocol + devtype + reason \
            + ipattrib + appid + cluster + node + info
        self.__endpointnosig = timestamp + hostname + local + priority + srvtype + msgnum + hostname + extimestamp + \
            tzdata + separator + msgtype + devname + devip + protocol + devtype + desc + reason \
            + ipattrib + callstate + appid + cluster + node + info

        # Search Patterns - StationConnectionError
        self.__stationall = timestamp + hostname + local + priority + srvtype + msgnum + hostname + extimestamp +\
            tzdata + separator + msgtype + devname + reasoncode + appid + cluster + node + info

    def endpointparse(self, line):
        sigkywd = "LastSignalReceived"
        searching = re.compile(r'{}'.format(sigkywd))
        dosearch = searching.search(line)
        if dosearch is None:
            descsigkywd = "Description"
            descsearching = re.compile(r'{}'.format(descsigkywd))
            descsearch = descsearching.search(line)
            if descsearch is None:
                parsed = self.__endpointnosigdesc.parseString(line)
                # print("nosig-nodesc")
                # print(parsed)
                payload = {"device": parsed[16], "ip": parsed[17], "description": "Description=", "reason": parsed[21],
                        "node": parsed[26], "lastsignal": "LastSignalReceived=", "callstate": "CallState="}
                return payload
            elif descsearch is not None:
                callkywd = "CallState"
                callsearching = re.compile(r'{}'.format(callkywd))
                callsearch = callsearching.search(line)
                if callsearch is None:
                    parsed = self.__endpointnosigcall.parseString(line)
                    # print("nosig-yesdesc-nocallstate")
                    # print(parsed)
                    payload = {"device": parsed[16], "ip": parsed[17], "description": parsed[20], "reason": parsed[21],
                        "node": parsed[25], "lastsignal": "LastSignalReceived=", "callstate": "CallState="}
                    return payload
                if callsearch is not None:
                    parsed = self.__endpointnosig.parseString(line)
                    # print("nosig-yesdesc-yescallstate")
                    # print(parsed)
                    payload = {"device": parsed[16], "ip": parsed[17], "description": parsed[20], "reason": parsed[21],
                        "node": parsed[25], "lastsignal": "LastSignalReceived=", "callstate": parsed[23]}
                    return payload
        elif dosearch is not None:
            descsigkywd = "Description"
            descsearching = re.compile(r'{}'.format(descsigkywd))
            descsearch = descsearching.search(line)
            if descsearch is None:
                parsed = self.__endpointnodesc.parseString(line)
                # print("yessig-nodesc")
                # print(parsed)
                payload = {"device": parsed[16], "ip": parsed[17], "description": "Description=", "reason": parsed[20],
                "node": parsed[25], "lastsignal": parsed[22], "callstate": "CallState="}
                return payload
            elif descsearch is not None:
                parsed = self.__endpointall.parseString(line)
                # print("all")
                # print(parsed)
                payload = {"device": parsed[16], "ip": parsed[17], "description": parsed[20], "reason": parsed[21],
                    "node": parsed[26], "lastsignal": parsed[22], "callstate": "CallState="}
                return payload

    def stationparse(self, line):
        parsed = self.__stationall.parseString(line)
        payload = {"device": parsed[16], "reason": parsed[17], "node": parsed[20]}
        return payload


def main():
    parser = Parser()
    searchlist = ['-EndPointUnregistered', '-StationConnectionError']
    endpointreport = {}
    stationsreport = {}
    with open("test.txt") as syslogfile:
        for line in syslogfile:
            for search in searchlist:
                searchpattern = re.compile(r'{}'.format(search))
                searchresult = searchpattern.search(line)
                if searchresult is None:
                    continue
                elif searchresult is not None:
                    if searchresult.group(0) == searchlist[0]:
                        endpoints = parser.endpointparse(line)
                        endpointdata = ','.join(str(x) for x in endpoints.values())
                        if endpointdata in endpointreport:
                            endpointreport[endpointdata] += 1
                        elif endpointdata not in endpointreport:
                            endpointreport[endpointdata] = 1
                    if searchresult.group(0) == searchlist[1]:
                        stations = parser.stationparse(line)
                        stationsdata = ','.join(str(x) for x in stations.values())
                        if stationsdata in stationsreport:
                            stationsreport[stationsdata] += 1
                        elif stationsdata not in stationsreport:
                            stationsreport[stationsdata] = 1
    return endpointreport, stationsreport


# Create TopTalkers report by default with top 10 chatty syslogs
# Prompt user to create full report not filtered by top 10.
def createreport():
    placer = '%s,%s\n'
    deregheader = "count,device,ip,description,reason,node,lastsignal,callstate\n"
    endpointout = list(itertools.islice(sorted(endpointreport.items(), key=lambda x: x[1], reverse=True), 30))
    stationsout = list(itertools.islice(sorted(stationsreport.items(), key=lambda x: x[1], reverse=True), 30))
    print("Info: Constructing TopTalkers report ... ")
    with open(os.path.join(temppath, 'EndpointUnregistered.csv'), 'w+', encoding='utf-8') as eptemp:
        eptemp.write(deregheader)
        for info, count in endpointout:
            eptemp.write(placer % (count, info))
    with open(os.path.join(temppath, 'StationConnectionError.csv'), 'w+', encoding='utf-8') as sttemp:
        sttemp.write("count,device,reason,nodeid\n")
        for info, count in stationsout:
            sttemp.write(placer % (count, info))
    writer = pd.ExcelWriter(os.path.join(toptalkerspath, 'TopTalkersReport_' + timestr + '.xlsx'), engine='xlsxwriter')
    for tempfile in glob.glob(temppath + "\\*.csv"):
        filecombine = pd.read_csv(tempfile)
        (_, f_name) = os.path.split(tempfile)
        (f_shortname, _) = os.path.splitext(f_name)
        filecombine.to_excel(writer, f_shortname, index=False)
    writer.save()


# Prompt user to perform cleanup by deleting the date-time named folder in CiscoSyslogs\, optional
def cleanup():
    while True:
        try:
            cleanup = input("Collect: Delete downloaded log files? (Y\\n): ").lower()
            if cleanup == "n":
                print(infoexit)
                exit()
            elif cleanup == "y":
                shutil.rmtree(downloaddir)
                shutil.rmtree(temppath)
                print("Info: Downloaded logs deleted.")
                print(infoexit)
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
        # ipaddr, username, password, usernameos, passwordos = infocollect()
        # netrequests()
        endpointreport, stationsreport = main()
        createreport()
        cleanup()
        exit()
    except Exception as e:
        print(e)
        exit()
