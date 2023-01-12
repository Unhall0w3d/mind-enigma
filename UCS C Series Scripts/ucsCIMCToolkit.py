import requests
import urllib3
from requests.auth import HTTPBasicAuth
import xml.dom.minidom
import re
import xml.etree.ElementTree as ET
import os
import time

# Define current time
timestr = time.strftime("%d-%m-%Y_%H-%M-%S")

# HTTPs
# Disable HTTPS Insecure Request error message
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class CiscoUCS:
    def __init__(self):
        # Set the UCS-C IP address and credentials
        self.ucs_ip = "localhost"
        self.ucs_username = "admin"
        self.ucs_password = "Mgr4C0-0P"

        # Set the API endpoint URL and headers
        self.url = f"https://{self.ucs_ip}/nuova"
        self.headers = {"Content-Type": "application/xml"}

        # Initial Login XML request
        self.logindata = "<aaaLogin inName='" + self.ucs_username + "' inPassword='" + self.ucs_password + "'></aaaLogin>"

    def apicall(self):
        print(f"Sending Login Request to UCS {self.ucs_ip}.")
        try:
            # Send the API request
            response = requests.post(self.url, auth=HTTPBasicAuth(self.ucs_username, self.ucs_password),
                                     headers=self.headers, data=self.logindata, verify=False, timeout=30)
        except requests.exceptions.HTTPError as err:
            print(err)
            exit()
        except requests.exceptions.ConnectionError as err:
            print(err)
            exit()
        except requests.exceptions.Timeout as err:
            print(err)
            exit()
        except requests.exceptions.RequestException as err:
            print(err)
            exit()

        # Parse the API response
        uglyxml = response.text.encode('utf-8')
        xmldata = xml.dom.minidom.parseString(uglyxml)
        xmlpretty = xmldata.toprettyxml()

        # Grab the cookie for the session
        match = re.search(r'outCookie="(.*?)"', xmlpretty)
        cookie = match.group(1)
        with open(os.path.join(os.path.expanduser('~'),
                               'Downloads/' + self.ucs_ip + '_' + timestr + '_' + 'UCSDetails.txt'),
                  'a+') as f:
            f.write(f"### Generating Report for Cisco UCS-C {self.ucs_ip} ###\n\n")
            f.close()
        # Data Request XMLs
        requestxmls = [f'<configResolveParent cookie="{cookie}" inHierarchical="false" dn="sys/rack-unit-1"/>',
                       f'<configResolveClass cookie="{cookie}" inHierarchical="false" classId="computeRackUnit"/>',
                       f'<configResolveClass cookie="{cookie}" inHierarchical="false" classId="firmwareRunning"/>',
                       f'<configResolveClass cookie="{cookie}" inHierarchical="true" classId="lsbootDef"']
        # Send API Requests for data
        for xmlmsg in requestxmls:
            response = requests.post(self.url, headers=self.headers, data=xmlmsg, verify=False, timeout=30)
            # Perform Parsing
            root = CiscoUCS.xmlparse(self, response)
            tagsearch = root.find(".//outConfigs")
            if tagsearch is not None:
                    for child in tagsearch:
                        # Report creation
                        if child.tag == "topSystem":
                            with open(os.path.join(os.path.expanduser('~'),
                                                   'Downloads/' + self.ucs_ip + '_' + timestr + '_' + 'UCSDetails.txt'),
                                      'a+') as f:
                                f.write("-------Top System Details-------\n")
                                f.write(f"Current Time: {child.attrib['currentTime']}\n")
                                f.write(f"Name: {child.attrib['name']}\n")
                                f.write(f"IP Address: {child.attrib['address']}\n")
                                f.write(f"Management Mode: {child.attrib['mode']}\n\n")
                        elif child.tag == "computeRackUnit":
                            with open(os.path.join(os.path.expanduser('~'),
                                                   'Downloads/' + self.ucs_ip + '_' + timestr + '_' + 'UCSDetails.txt'),
                                      'a+') as f:
                                f.write("-------General Details-------\n")
                                f.write(f"Hostname: {child.attrib['usrLbl']}\n")
                                f.write(f"Server ID: {child.attrib['serverId']}\n")
                                f.write(f"Serial Number: {child.attrib['serial']}\n")
                                f.write(f"Power State: {child.attrib['operPower']}\n")
                                f.write(f"Server Name: {child.attrib['name']}\n")
                                f.write(f"Server Model: {child.attrib['model']}\n")
                                f.write(f"Vendor: {child.attrib['vendor']}\n")
                                f.write(f"-------Hardware Details-------\n")
                                f.write(f"Total Memory: {child.attrib['totalMemory']}\n")
                                f.write(f"Available Memory: {child.attrib['availableMemory']}\n")
                                f.write(f"Memory Speed: {child.attrib['memorySpeed']}\n")
                                f.write(f"CPUs: {child.attrib['numOfCpus']}\n")
                                f.write(f"Cores: {child.attrib['numOfCores']}\n")
                                f.write(f"Cores Enabled: {child.attrib['numOfCoresEnabled']}\n")
                                f.write(f"Threads: {child.attrib['numOfThreads']}\n")
                                f.write(f"-------Reset/Power Event Reason-------\n")
                                f.write(f"Last Reset Reason: {child.attrib['cimcResetReason']}\n\n")
                        elif child.tag == "firmwareRunning":
                            with open(os.path.join(os.path.expanduser('~'),
                                                   'Downloads/' + self.ucs_ip + '_' + timestr + '_' + 'UCSDetails.txt'),
                                      'a+') as f:
                                f.write("-------Running Firmware Report-------\n")
                                f.write(f"Domain: {child.attrib['dn']}\n")
                                f.write(f"Deployment: {child.attrib['deployment']}\n")
                                f.write(f"Firmware Type: {child.attrib['type']}\n")
                                f.write(f"Version: {child.attrib['version']}\n\n")
                        # elif child.tag == "lsbootDef":
                            # print("checking lsbootdef")
                            # tagsearch = root.find(".//outConfigs/lsbootDef")
                            # if tagsearch is not None:
                                # print(tagsearch)
                                # for child in tagsearch:
                                    # print(child.tag)
                                    # with open(os.path.join(os.path.expanduser('~'),
                                                          # 'Downloads/' + self.ucs_ip + '_' + timestr + '_' +
                                                          # 'UCSDetails.txt'), 'a+') as f:
                                        # f.write("-------Boot Order-------\n")
                                        # f.write(f"{child.attrib['order']}, {child.tag}, {child.attrib['type']},"
                                                # f" {child.attrib['rn']}\n")
            response.close()

    def xmlparse(self, response):
        uglyxml = response.text.encode('utf-8')
        xmldata = xml.dom.minidom.parseString(uglyxml)
        prettyxml = xmldata.toprettyxml()
        root = ET.fromstring(prettyxml)
        return root


if __name__ == "__main__":
    try:
        CiscoUCS().apicall()
        exit()
    except Exception as e:
        print(e)
        exit()
