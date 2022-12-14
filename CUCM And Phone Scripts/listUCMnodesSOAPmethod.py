# Function to collect CCM Subscriber IP addresses.
import requests
from requests.auth import HTTPBasicAuth
from getpass import getpass


def infocollect():
    ipaddr = str(input("Collect: CCM Pub IP? : "))
    username = str(input("Collect: GUI Username? : "))
    password = getpass("Collect: GUI Password? : ")
    return ipaddr, username, password


def listucm(ipaddr, username, password):
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
        response.close()
        print('Found Cluster Nodes')
        print('\n'.join(ucnodes))
        return ucnodes
    except Exception as e:
        print("We encountered an error while pulling CCM Subscriber info. Exiting.")
        print(e)
        exit()


ipaddr, username, password = infocollect()
listucm(ipaddr, username, password)
exit()