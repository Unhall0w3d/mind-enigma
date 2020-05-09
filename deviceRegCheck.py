#!/usr/var/python
# -*- code:UTF-8 -*-

#####################################
# Script created by Ken Perry, 2020 #
#####################################

# Modules Imported for Script Functionality
import re
import requests
from bs4 import BeautifulSoup
from collections import OrderedDict


# Phone Collection function that asks for a number for how many phones we'll check, then their IP addresses.
# TO DO: Modify phonecollection function to utilize input from file.
def phonecollection():
    num_phones = int(input('How many phones?: '))
    if type(num_phones) != int:
        print('Error: Expected Integer.')
        exit(1)
    ip_list = []
    for i in range(num_phones):
        ip_list.append(input('What is the phone IP address?: '))
    return ip_list


# Web Scrape function that uses requests to get webpage content.
# Content is then parsed by lxml (or html.parser) and BeautifulSoup is used to extract data based on regular expression.
def phoneregcheck(ip_addr):
    uris = OrderedDict({
        '/CGI/Java/Serviceability?adapter=device.statistics.configuration': ['SEP*|CIPC*', 'Active'],
        '/localmenus.cgi?func=219': ['SEP*', 'Active'],
        '/NetworkConfiguration': ['SEP*', 'Active'],
        '/Network_Setup.htm': ['ATA*|SEP*', 'Active'],
        '/Network_Setup.html': ['SEP*', 'Active'],
        '/?adapter=device.statistics.configuration': ['DX*', 'Active'],
    })
    for uri, regex_list in uris.items():
        try:
            response = requests.get(f'http://{ip_addr}{uri}', timeout=6)
            if response.status_code == 200:
                parser = BeautifulSoup(response.content, 'lxml')
                for regex in regex_list:
                    data = parser.find(text=re.compile(regex))
                    if data:
                        print(data)
                break
        except requests.exceptions.ConnectionError:
            print('Far end ' + ip_addr + 'has closed the connection.')
        except requests.exceptions.Timeout:
            print('Connection to ' + ip_addr + ' timed out. Trying next.')
        except Exception as e:
            print('The script failed. Contact script dev with details from your attempt and failure.')
            print(e)


# Run collection for how many phones we will connect to, as well as the IP Addresses.
# TO DO: Create prompt with options, based on option selected (e.g. 1), run function tied to (1)
phone_ips = phonecollection()

# Now loop for each appended IP Address and run webScrape function
[phoneregcheck(ip_addr) for ip_addr in phone_ips]
