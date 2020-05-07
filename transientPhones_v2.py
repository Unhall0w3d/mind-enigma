#!/usr/var/python
# -*- code:UTF-8 -*-

#####################################
# Script created by Ken Perry, 2020 #
#####################################

# Modules Imported for Script Functionality
import re
import requests
from bs4 import BeautifulSoup


# Phone Collection function that asks for a number for how many phones we'll check, then their IP addresses.
# TO DO: Add exception/method to allow script to proceed if < x IP Addresses are provided.
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
# Content is then parsed by lxml and BeautifulSoup is used to extract data based on regular expression.
# TO DO: Come up with method to have multiple URLs in dictionary (OrderedDict?) to try URL, if http 200 returned, proceed.
# TO DO: Fail the script more to form proper exceptions
def phoneregcheck(ip_addr):
    url = 'http://' + ip_addr + '/CGI/Java/Serviceability?adapter=device.statistics.configuration'
    url2 = 'http://' + ip_addr + '/localmenus.cgi?func=219'
    # url3 = 'http://' + n + '/localmenus.cgi?func=604' -- URL used to pull Serial Number from older Cisco Conf phones.
    # To be reused for SN Audit method once created.
    try:
        response = requests.get(url, timeout=6)
        if response.status_code == 200:
            page = requests.get(url, timeout=6)
            soup = BeautifulSoup(page.content, 'lxml')
            results = soup.find(text=re.compile('SEP*|CIPC*'))
            results2 = soup.find_all(text=re.compile('Active'))
            print(results, results2)
        elif response.status_code != 200:
            page = requests.get(url2, timeout=6)
            soup = BeautifulSoup(page.content, 'lxml')
            results = soup.find(text=re.compile('SEP*'))
            results2 = soup.find_all(text=re.compile('Active'))
            print(results, results2)
        else:
            print('This is not a phone I am configured to handle. Exiting')
    except requests.exceptions.Timeout:
        print('Connection to ' + ip_addr + ' timed out. Trying next.')
    except Exception as e:
        print('Something failed beyond a simple timeout. Contact the script dev with details from your attempt.')
        print(e)


# Run collection for how many phones we will connect to, as well as the IP Addresses.
# TO DO: Create prompt with options, based on option selected (e.g. 1), run function tied to (1)
phone_ips = phonecollection()


# Now loop for each appended IP Address and run webScrape function
[phoneregcheck(ip_addr) for ip_addr in phone_ips]
