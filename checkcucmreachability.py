import requests
import urllib3
from getpass import getpass

# Define disablement of HTTPS Insecure Request error message.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# URL to hit for request against axl
baseurl = 'https://'

# Define user input required for script; pub ip, username, pw.
ccmip = str(input('What is the CUCM Pub IP?: '))
print('Supported UCM SQL DB Versions: 12.5 | 12.0 | 11.5 | 11.0 | 10.5 | 10.0 | 9.1 | 9.0')
version = str(input('What version is UCM?: '))
myusername = str(input('What is the GUI Username?: '))
mypassword = getpass('What is the GUI Password?: ')

# Here's where we verify reachability of the AXL interface for DB dip.
try:
    reachabilitycheck = requests.get(baseurl + ccmip + '/axl', auth=(myusername, mypassword), verify=False)
    if reachabilitycheck.status_code != 200:
        print('AXL Interface at ' + baseurl + ccmip + '/axl/ is not available, or some other error. '
                                                      'Please verify CCM AXL Service Status.')
        print(reachabilitycheck.status_code)
        print('Contact script dev to create exception or handle response code.')
        exit()
    elif reachabilitycheck.status_code == 200:
        print()
        print('AXL Interface is working and accepting requests.')
except requests.exceptions.ConnectionError:
    print('Connection error occurred. Unable to get HTTP Response from CUCM AXL Interface. Check connectivity.')
except requests.exceptions.Timeout:
    print('Connection timed out to UCM AXL Interface.')
except Exception as m:
    print(m)
