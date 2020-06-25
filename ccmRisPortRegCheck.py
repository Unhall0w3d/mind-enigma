#!/usr/var/python
# -*- code:UTF-8 -*-

#####################################
# Script created by Ken Perry, 2020 #
#       NOC THOUGHTS BLOG           #
#    https://www.nocthoughts.com    #
#####################################

# Define script imports
from zeep import Client
from zeep.cache import SqliteCache
from zeep.transports import Transport
from zeep.plugins import HistoryPlugin
from requests import Session
from requests.auth import HTTPBasicAuth
from lxml import etree
import urllib3

# Disable insecure warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Define Username/PW/CUCM IP
def infocollect():
    ipaddr = input("What is the CUCM IP?: ")
    username = input("What is the CUCM Username?: ")
    password = input("What is the CUCM Password?: ")
    return ipaddr, username, password


# Function that constructs csv string to check against ucm from file input.
def inputfetch():
    inputfile = input('What is the name of the input text file?: ')
    with open(inputfile) as txtfile:
        lines = [line.rstrip() for line in txtfile]
        for line in txtfile:
            lines.append(line)
    return lines


# Script
def regcheck(ccmip, ccmun, ccmpw, macs):
    devtype = input("Are we looking for Phones or SIP Trunks? Don't mix. (phone|trunk): ")
    if devtype == "phone":
        # Define WSDL location
        wsdl = 'https://' + ccmip + ':8443/realtimeservice2/services/RISService70?wsdl'
        session = Session()
        session.verify = False
        session.auth = HTTPBasicAuth(ccmun, ccmpw)
        transport = Transport(cache=SqliteCache(), session=session, timeout=20)
        history = HistoryPlugin()
        client = Client(wsdl=wsdl, transport=transport, plugins=[history])
        factory = client.type_factory('ns0')
        item = []
        for mac in macs:
            item.append(factory.SelectItem(Item=mac))
        devnames = factory.ArrayOfSelectItem(item)
        stateinfo = ''
        criteria = factory.CmSelectionCriteria(
            MaxReturnedDevices=1000, DeviceClass='Phone', Model=255, Status='Any', NodeName='', SelectBy='Name',
            SelectItems=devnames, Protocol='Any', DownloadStatus='Any')
        result = client.service.selectCmDevice(stateinfo, criteria)
        for node in result.SelectCmDeviceResult.CmNodes.item:
            for device in node.CmDevices.item:
                print("Device Name: " + device.Name, "Status: " + device.Status,
                      "Description: " + device.Description, "Dir Number: " + device.DirNumber)
    elif devtype == "trunk":
        # Define WSDL location
        wsdl = 'https://' + ccmip + ':8443/realtimeservice/services/RisPort?wsdl'
        session = Session()
        session.verify = False
        session.auth = HTTPBasicAuth(ccmun, ccmpw)
        transport = Transport(cache=SqliteCache(), session=session, timeout=20)
        history = HistoryPlugin()
        client = Client(wsdl=wsdl, transport=transport, plugins=[history])
        factory = client.type_factory('ns0')
        item = []
        for mac in macs:
            item.append(factory.SelectItem(Item=mac))
        devnames = factory.SelectItem(item)
        stateinfo = ''
        criteria = factory.CmSelectionCriteriaSIP(
            MaxReturnedDevices=1000, Class='Any', Model=255, Status='Any', SelectBy='Name',
            SelectItems=devnames, NodeName='', Protocol='Any')
        result = client.service.SelectCmDeviceSIP(stateinfo, criteria)
        for node in result.SelectCmDeviceResultSIP.CmNodesSIP.item:
            for device in node.CmDevicesSIP.item:
                print("Device Name: " + device.Name, "Status: " + device.Status,
                      "Description: " + device.Description)
    checkhistory = input("Do you want to check the SOAP Message History?(y/n): ")
    if checkhistory == "y":
        for hist in [history.last_sent, history.last_received]:
            print(etree.tostring(hist["envelope"], encoding="unicode", pretty_print=True))
    elif checkhistory == "n":
        exit()


ccmip, ccmun, ccmpw = infocollect()
macs = inputfetch()
regcheck(ccmip, ccmun, ccmpw, macs)
