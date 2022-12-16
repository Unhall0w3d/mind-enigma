#!/usr/var/python
# -*- code:UTF-8 -*-

#####################################
# Script created in part by ChatGPT #
# and Ken Perry as a test of AI     #
# ability to create purpose built   #
# scripts.                          #
# ChatGPT: https://chat.openai.com  #
#       NOC THOUGHTS BLOG           #
#    https://www.nocthoughts.com    #
#####################################

import base64
from zeep import Client, Settings
from getpass import getpass
import time

# Define current time.
timestr = time.strftime("%Y%m%d-%H%M%S")

def infocollect():
    # Define user input required for script; pub ip, username, pw.
    cucmipaddr = str(input('What is the target UC Server Pub IP?: '))
    cucmusername = str(input('What is the GUI Username?: '))
    cucmpassword = getpass('What is the GUI Password?: ')
    try:
        print('Checking AXL Interface Availability.')
        r = requests.get('https://' + cucmipaddr + '/axl', auth=HTTPBasicAuth(cucmusername, cucmpassword), verify=False)
        if r.status_code == 401:
            print('AXL Interface is unreachable. HTTP 401 Unauthorized Received.')
            print('Please ensure the AXL URL is reachable at https://<ucm-ip>/axl.')
            print('Ensure the credentials and version info is correct.')
            print('Script Exiting.')
            exit()
        elif r.status_code == 200:
            print('AXL Interface is available. HTTP 200 received.')
            return cucmipaddr, cucmversion, cucmpassword, cucmusername
    except Exception as e:
        print(e)
        exit()


def tracednld():
    # Set up the AXL API client
    wsdl = 'https://' + cucmipaddr + '/axl/service/v12.0/AXLAPI.wsdl'
    client = Client(wsdl=wsdl, wsse=UsernameToken(cucmusername, cucmpassword))

    # Make the listTraceFile request
    response = client.service.listTraceFile(name='trace-file-name', fileFormat='zip')

    # Print a list of trace file names and their corresponding trace file IDs
    for trace_file in response['return']['traceFile']:
        print(f"{trace_file['name']} ({trace_file['id']})")

    # Prompt the user to select a trace file
    selected_trace_id = input("Enter the ID of the trace file you want to download: ")

    # Make the getTraceFile request using the selected trace file ID
    response = client.service.getTraceFile(id=selected_trace_id, fileFormat='zip')

    # Save the trace file data to a local file
    with open(cucmipaddr + '_' + selected_trace_id + '_' + timestr + '.zip', 'wb') as f:
        f.write(base64.b64decode(response['return']['traceFile']))


if __name__ == "__main__":
    try:
        infocollect()
        tracednld()
        exit()
    except Exception as x:
        print(x)
        exit()
