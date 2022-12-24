import requests
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as ET
import os
from getpass import getpass

# Disablement of HTTPS Insecure Request error message.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Prompt the user to enter the hostname and port of the CUCM AXL interface
hostname = input('Enter the hostname of the CUCM AXL interface: ')
port = input('Enter the port of the CUCM AXL interface: ')

# Prompt the user to enter the username and password to use for authentication
username = input('Enter the username for CUCM AXL: ')
password = getpass('Enter the password for CUCM AXL: ')

# Set the AXL API endpoint URL
url = f'https://{hostname}:{port}/logcollectionservice2/services/LogCollectionPortTypeService'

# Set the SOAP action and body for the AXL API call to list the active logs
soap_action = 'http://www.cisco.com/AXL/API/10.5/FileTrans'
soap_body = """
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns="http://www.cisco.com/AXL/API/10.5">
  <soapenv:Header/>
  <soapenv:Body>
    <ns:listActiveLog>
    </ns:listActiveLog>
  </soapenv:Body>
</soapenv:Envelope>
"""

# Set the HTTP headers for the AXL API call
headers = {
    'Content-Type': 'text/xml',
    'SOAPAction': soap_action
}

# Make the AXL API call to list the active logs and store the response
response = requests.post(url, auth=HTTPBasicAuth(username, password), headers=headers, data=soap_body, verify=False)

# Parse the response XML
root = ET.fromstring(response.text)

# Extract the list of active logs from the response
active_logs = root.findall('.//return/activeLogs/')

# Print the list of active logs and prompt the user to select the logs they want to download
print('Available log files:')
for i, log in enumerate(active_logs):
    print(f'{i+1}. {log.text}')
selected_logs = input('Enter the numbers of the log files you want to download, separated by commas (e.g. 1,2,3): ')

# Split the user's input into a list of log file numbers
selected_logs = [int(x) for x in selected_logs.split(',')]

# Download the selected log files
default_download_dir = os.path.join(os.environ['USERPROFILE'], 'Downloads')
for i, log in enumerate(active_logs):
    if i+1 in selected_logs:
        # Set the SOAP action and body for the AXL API call to download the log file
        soap_action = 'http://www.cisco.com/AXL/API/10.5/FileTrans'
        soap_body = f"""
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns="http://www.cisco.com/AXL/API/10.5">
          <soapenv:Header/>
          <soapenv:Body>
            <ns:download>
              <fileName>{log.text}</fileName>
            </ns:download>
          </soapenv:Body>
        </soapenv:Envelope>
        """

        # Set the HTTP headers for the AXL API call
        headers = {
            'Content-Type': 'text/xml',
            'SOAPAction': soap_action
        }

        # Make the AXL API call to download the log file and store the response
        response = requests.post(url, auth=HTTPBasicAuth(username, password), headers=headers, data=soap_body, verify=False)

        # Extract the log file data from the response
        log_data = response.content

        # Save the log file to the default download directory
        with open(os.path.join(default_download_dir, log.text), 'wb') as f:
            f.write(log_data)

print('Selected log files have been downloaded to the default download directory.')
