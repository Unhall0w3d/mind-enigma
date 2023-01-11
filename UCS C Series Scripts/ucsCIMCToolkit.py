import requests
import urllib3
from requests.auth import HTTPBasicAuth

# HTTPs
# Disable HTTPS Insecure Request error message
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set the UCS-C IP address and credentials
ucs_ip = "x.x.x.x"
ucs_username = "username"
ucs_password = "password"

# Set the API endpoint URL
url = f"https://{ucs_ip}/nuova"

# Create the API request header
headers = {"Content-Type": "application/xml"}

# Set the API request body
body = """
<configConfMos cookie="```cookie```" inHierarchical="false">
    <inConfigs>
        <pair key="org-root/sys">
            <sys dn="org-root/sys" name="" id="" descr="">
                <hostname></hostname>
                <ip></ip>
                <storageLocalDiskControllers></storageLocalDiskControllers>
            </sys>
        </pair>
    </inConfigs>
</configConfMos>
"""

# Send the API request
response = requests.post(url, auth=HTTPBasicAuth(ucs_username, ucs_password), headers=headers, data=body)

# Parse the API response
response_xml = response.content

# Extract the system details from the response
hostname = response_xml.find(".//hostname").text
ip = response_xml.find(".//ip").text
storage_controllers = response_xml.find(".//storageLocalDiskControllers").text

# Print the system details
print(f"Hostname: {hostname}")
print(f"IP Address: {ip}")
print(f"Storage Controllers: {storage_controllers}")
