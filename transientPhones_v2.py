#!/usr/var/python
#####################################
# Script created by Ken Perry, 2020 #
# Code Contributions by:            #
# Mark Barba                        #
# Juliana Xu                        #
#####################################

import re, requests, lxml
from bs4 import BeautifulSoup

def phonecollection():
	x = input('How many phones?: ')
	x = int(x)
	global ipaddr
	ipaddr = []
	for i in range(x):
		ipaddr.append(input('What is the phone IP address?: '))


def webscrape():
	url = 'http://' + n + '/CGI/Java/Serviceability?adapter=device.statistics.configuration'
	url2 = 'http://' + n + '/localmenus.cgi?func=219'
	url3 = 'http://' + n + '/localmenus.cgi?func=604'
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
			page2 = requests.get(url3, timeout=6)
			soup = BeautifulSoup(page.content, 'lxml')
			soup2 = BeautifulSoup(page2.content, 'lxml')
			results = soup2.find(text=re.compile('Cisco'))
			results2 = soup.find(text=re.compile('SEP*'))
			results3 = soup.find_all(text=re.compile('Active'))
			print(results, results2, results3)
		else:
			print('This is not a phone I am configured to handle. Exiting')
	except requests.exceptions.Timeout:
		print('Connection to ' + n + ' timed out. Trying next.')
	except requests.exceptions.RequestException as e:
		raise SystemExit(e)

# Run collection for how many phones we will connect to, as well as the IP Addresses.
phonecollection()

# Now loop for each appended IP Address and run webScrape function
for n in ipaddr:
	webscrape()