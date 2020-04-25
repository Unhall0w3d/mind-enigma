#!/usr/bin/python
import subprocess

#Define Variables
x = input('How many phones do we need logs for?: ')
x = int(x)
ipAddress = []
destFolder = input('Folder Location to Store Files - It Must Exist (e.g. /home/sampson/): ')


#Collect IP Addresses
for i in range(x) :
        ipAddress.append(input('What is the phone IP address?: '))

#Download files from the Serviceability page. This includes /FS/ directory storing console logs. 
for n in ipAddress :
        subprocess.call ('wget -T 5 --tries=2 -r --accept "*.log, messages*, *.tar.gz" http://' + n + '/CGI/Java/Serviceability?adapter=device.statistics.consolelog' + ' -P ' + destFolder, shell=True)

#Inform user download is complete, indicate where files are stored.
print('#################################################################################')
print('#################################################################################')
print('Files have been stored in ' + destFolder + ' in an IP specific folder.')
print('#################################################################################')
print('#################################################################################')
