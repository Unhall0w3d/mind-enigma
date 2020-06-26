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


# Function that takes device names from a text file, strips carriage return and adds device names to array
def inputfetch():
    inputfile = input('What is the name of the input text file?: ')
    with open(inputfile) as txtfile:
        lines = [line.rstrip() for line in txtfile]
        for line in txtfile:
            lines.append(line)
    return lines


# Script to check against risport the status of specified phones. We check using different return parameters for
# Phone and SIP Trunk as we cannot pull Dir Number.
def regcheck(ccmip, ccmun, ccmpw):
    devtype = input("Are we looking for Phones or SIP Trunks? If both, select trunk. (phone|trunk): ")
    if devtype == "phone":
        # Define WSDL location at http url, we do not store it locally
        macs = inputfetch()
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
        # Define WSDL location at http url, we do not store it locally
        macs = inputfetch()
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
            MaxReturnedDevices=1000, DeviceClass='Any', Model=255, Status='Any', NodeName='', SelectBy='Name',
            SelectItems=devnames, Protocol='Any', DownloadStatus='Any')
        result = client.service.selectCmDevice(stateinfo, criteria)
        for node in result.SelectCmDeviceResult.CmNodes.item:
            for device in node.CmDevices.item:
                print("SIP Trunks that appear multiple times due to assignment to multiple RG/RL will appear multiple"
                      "times in the below output.")
                print("Device Name: " + device.Name, "Status: " + device.Status,
                      "Description: " + device.Description)
    checkhistory = input("Do you want to check the SOAP Message History?(y/n): ")
    if checkhistory == "y":
        for hist in [history.last_sent, history.last_received]:
            print(etree.tostring(hist["envelope"], encoding="unicode", pretty_print=True))
    elif checkhistory == "n":
        exit()


ccmip, ccmun, ccmpw = infocollect()
regcheck(ccmip, ccmun, ccmpw)
