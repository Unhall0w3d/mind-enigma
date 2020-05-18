import time
import requests
import urllib3
import xml.dom.minidom
from getpass import getpass

# Define Variables
timestr = time.strftime("%Y%m%d-%H%M%S")


def checkregstate():
    # Define disablement of HTTPS Insecure Request error message.
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Define user input required for script; pub ip, username, pw
    ccmip = str(input('What is the CUCM Pub IP?: '))
    print('Supported UCM SQL DB Versions: 12.5 | 12.0 | 11.5 | 11.0 | 10.5 | 10.0 | 9.1 | 9.0')
    version = str(input('What version is UCM?: '))
    myusername = str(input('What is the GUI Username?: '))
    mypassword = getpass('What is the GUI Password?: ')
    devname = str(input('What is the Device Name (e.g. SEPAABBCCDDEEFF): '))

    # URL to hit for request against axl
    url = ('https://' + ccmip + '/axl/')

    response = requests.get('https://' + ccmip + '/ast/ASTIsapi.dll?OpenDeviceSearch?Type=&NodeName'
                                                         '=&SubSystemType=&Status=1&DownloadStatus=&MaxDevices=200'
                                                         '&Model=&SearchType=Name&&Protocol=Any&SearchPattern=' + devname, verify=False, auth=(myusername, mypassword))

    uglyxml = response.text.encode('utf8')
    xmldata = xml.dom.minidom.parseString(uglyxml)
    xml_pretty_str = xmldata.toprettyxml()
    
    print('Writing response to file ASTResponse_' + timestr + '.txt')
    with open('ASTResponse_' + timestr + '.txt', 'w+') as file:
        file.write(xml_pretty_str)


checkregstate()
