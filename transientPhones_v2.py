#!/usr/var/python
#####################################
# Script created by Ken Perry, 2020 #
# Code Contributions by:            #
# Mark Barba                        #
# Juliana Xu                        #
#####################################

import re, requests
from bs4 import BeautifulSoup

def phoneCollection():
        x = input('How many phones?: ')
        x = int(x)
        global ipAddress
        ipAddress = []
        for i in range(x):
                ipAddress.append(input('What is the phone IP address?: '))

#Here we loop to access each IP address provided (equivalent of Network Configuration page) to collect Device Type + MAC + Registered state.
def webScrape():
        try:
                URL = 'http://' + n + '/CGI/Java/Serviceability?adapter=device.statistics.configuration' #URL is dynamically created based on IPs collected
                page = requests.get(URL, timeout=6)
                soup = BeautifulSoup(page.content, 'html.parser')
#looking for instance of SEP* or CIPC*, such as CIPCKPERRY or SEPAABBCCDDEEFF. Returned as variable 'results'
                results = soup.find(text=re.compile('SEP*|CIPC*'))
#looking for instance of "Active" on the webpage indicating device is registered to a given CCM. Returned as variable 'results2'
                results2 = soup.find_all(text=re.compile('Active'))
                print(results, results2)
#conditional statement that dictates if "Active" is not found, report only the device model and name. Otherwise report the device it is registered to. (e.g. cucmpub.ipt>
        except:
                print('Connection to ' + n + ' timed out. Trying next.')

#Run collection for how many phones we will connect to, as well as the IP Addresses.
phoneCollection()

#Now loop for each appended IP Address and run webScrape function
for n in ipAddress:
        webScrape()
