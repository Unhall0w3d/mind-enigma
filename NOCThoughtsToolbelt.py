#!/usr/var/python
# -*- code:UTF-8 -*-

#####################################
# Script created by Ken Perry, 2020 #
#       NOC THOUGHTS BLOG           #
# https://nocthoughts.wordpress.com #
#####################################

# Modules Imported for Script Functionality
import re
import requests
import sys
import subprocess
import time
from bs4 import BeautifulSoup
from collections import OrderedDict

# Define Variables
timestr = time.strftime("%Y%m%d-%H%M%S")


# Define Main Menu
def menu():
    print("************MAIN MENU**************")
    print()
    choice = input("""
                      1: deviceRegCheck File Input
                      2: deviceRegCheck Menu Input
                      3: pull phoneConsoleLogs
                      Q. Quit

                      Please enter your choice: """)

    if choice == "1":
        # Phone Collection function that utilizes input file 'iplist.txt' in same directory.
        def phonefilefetch():
            with open('iplist.txt') as txtfile:
                lines = [line.rstrip() for line in txtfile]
                for line in txtfile:
                    lines.append(line)
            return lines
        phone_ips = phonefilefetch()
        [phoneregcheck(ip_addr) for ip_addr in phone_ips]
        menu()
    elif choice == "2":
        # Phone Collection function that asks for a number for how many phones we'll check, then their IP addresses.
        def phonecollection():
            num_phones = int(input('How many phones?: '))
            if type(num_phones) != int:
                print('Error: Expected Integer.')
                exit(1)
            ip_list = []
            for phonecount in range(num_phones):
                ip_list.append(input('What is the phone IP address?: '))
            return ip_list
        phone_ips = phonecollection()
        [phoneregcheck(ip_addr) for ip_addr in phone_ips]
        menu()
    elif choice == "3":
        phones = int(input('How many phones do we need logs for?: '))
        ipaddress = []
        destfolder = str('~/')
        for ipcollect in range(phones):
            ipaddress.append(input('What is the phone IP address?: '))
        for n in ipaddress:
            try:
                subprocess.call(
                    'wget -T 5 --tries=2 -r --accept "*.log, messages*, *.tar.gz" http://' + n +
                    '/CGI/Java/Serviceability?adapter=device.statistics.consolelog' + ' -P ' + destfolder,
                    shell=True)
            except requests.exceptions.ConnectionError:
                print('Far end ' + n + 'has closed the connection.')
            except requests.exceptions.Timeout:
                print('Connection to ' + n + ' timed out. Trying next.')
            except Exception as e:
                print('The script failed. Contact script dev with details from your attempt and failure.')
                print(e)
        print('#################################################################################')
        print('#################################################################################')
        print('Files have been stored in ' + destfolder + ' in an IP specific folder.')
        print('#################################################################################')
        print('#################################################################################')
        menu()
    elif choice == "q" or choice == "Q":
        sys.exit()
    else:
        print("You must select an option on the menu.")
        print("Please try again")
        menu()


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
                        z = open('DeviceRegStatus' + timestr + '.txt', 'a+')
                        z.write(data + "\n")
                        z.close()
                break
        except requests.exceptions.ConnectionError:
            print('URL Attempted for ' + ip_addr + ' received HTTP 200 but closed connection. Attempting next URL.')
        except requests.exceptions.Timeout:
            print('Connection to ' + ip_addr + ' timed out. Trying next.')
        except Exception as e:
            print('The script failed. Contact script dev with details from your attempt and failure.')
            print(e)


# Call Menu
menu()
