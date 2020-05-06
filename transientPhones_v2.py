#!/usr/var/python
# -*- code:UTF-8 -*-

#####################################
# Script created by Ken Perry, 2020 #
#####################################

# Modules Imported for Script Functionality
import re
import requests
from bs4 import BeautifulSoup

# Define Variables Required Globally
ipaddr = []

# Phone Collection function that asks for a number for how many phones we'll check, then their IP addresses.
# TO DO: Add exception for if non-number to re-prompt.
# TO DO: Add exception/method to allow script to proceed if < x IP Addresses are provided.
def phonecollection():
    x = input('How many phones?: ')
    x = int(x)
    ipaddr = []
    for i in range(x):
        ipaddr.append(input('What is the phone IP address?: '))
    return ipaddr


# Web Scrape function that uses requests to get webpage content.
# Content is then parsed by lxml and BeautifulSoup is used to extract data based on regular expression.
# TO DO: Scope in variables to appropriate if/elif
# TO DO: Fail the script more to form proper exceptions
def phoneregcheck():
    url = 'http://' + n + '/CGI/Java/Serviceability?adapter=device.statistics.configuration'
    url2 = 'http://' + n + '/localmenus.cgi?func=219'
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
        print('Connection to ' + n + ' timed out. Trying next.')
    except:
        print('Something failed beyond a simple timeout. Contact the script dev with details from your attempt.')


# Run collection for how many phones we will connect to, as well as the IP Addresses.
# TO DO: Create prompt with options, based on option selected (e.g. 1), run function tied to (1)
ipaddr = phonecollection()

# Now loop for each appended IP Address and run webScrape function
# TO DO: Find a better way to do this so that it runs subsequently.
# TO DO: Ensure does not contain phoneregcheck as nested function so phonecollection method can be used elsewhere.
for n in ipaddr:
    phoneregcheck()