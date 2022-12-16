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
now = time.strftime("%Y%m%d-%H%M%S")

# Prompt the user for their CUCM username and password
ipaddr = input("Enter your CUCM Publisher IP Address: ")
print('Supported Versions: 12.5 | 12.0 | 11.5 | 11.0 | 10.5 | 10.0 | 9.1 | 9.0')
ver = input("Enter your CUCM Version: ")
username = input("Enter your CUCM GUI Username: ")
password = getpass("Enter your CUCM GUI Password: ")

# Set up the AXL API client
wsdl = 'https://' + ipaddr + '/axl/service/v12.0/AXLAPI.wsdl'
client = Client(wsdl=wsdl, wsse=UsernameToken(username, password))

while True:
    # Make the listTraceFile request
    response = client.service.listTraceFile(name='trace-file-name', fileFormat='zip')

    # Print a list of trace file names and their corresponding trace file IDs
    for trace_file in response['return']['traceFile']:
        print(f"{trace_file['name']} ({trace_file['id']})")

    # Prompt the user to select a trace file
    selected_trace_id = input("Enter the ID of the trace file you want to download (or 'q' to quit): ")

    if selected_trace_id.lower() == 'q':
        # Exit the loop if the user enters 'q'
        break

    # Make the getTraceFile request using the selected trace file ID
    response = client.service.getTraceFile(id=selected_trace_id, fileFormat='zip')

    # Save the trace file data to a local file
    with open(now + '_' + ipaddr + '_' + selected_trace_id + '.zip', 'wb') as f:
        f.write(base64.b64decode(response['return']['traceFile']))

    # Prompt the user to download another trace file
    download_more = input("Do you want to download another trace file? (y/n) ")
    if download_more.lower() != 'y':
        # Exit the loop if the user does not want to download another trace file
        break
