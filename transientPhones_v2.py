#!/usr/var/python
#####################################
# Script created by Ken Perry, 2020 #
# Help by Mark Barba                #
#####################################

import re
import requests
from bs4 import BeautifulSoup

#Define how many phones we need to hit
x = input('How many phones?: ')
x = int(x)

#Collect IP addresses in tuple
ipAddress = []

#Here we loop to grab the list of IP Addresses to access.
for i in range(x):
        ipAddress.append(input('What is the phone IP address?: '))

#Here we loop to access each IP address provided (equivalent of Network Configuration page) to collect Device Type + MAC + Registered state.
for n in ipAddress:
        URL = 'http://' + n + '/CGI/Java/Serviceability?adapter=device.statistics.configuration' #URL is dynamically created based on IPs collected
        page = requests.get(URL, timeout=6)
        soup = BeautifulSoup(page.content, 'html.parser')
#looking for instance of SEP* or CIPC*, such as CIPCKPERRY or SEPAABBCCDDEEFF. Returned as variable 'results'
        results = soup.find(text=re.compile('SEP*|CIPC*'))
#looking for instance of "Active" on the webpage indicating device is registered to a given CCM. Returned as variable 'results2'
        results2 = soup.find_all(text=re.compile('Active'))
#conditional statement that dictates if "Active" is not found, indicate the phone is not registered. Otherwise report the device it is registered to. (e.g. cucmpub.ipt.local Active)
        if results2 is None:
                print(results)
        else:
                print(results, results2)
