#!/usr/bin/python
import subprocess

#Define Variables
ipAddress = input('IP Address: ')
destFolder = input('Folder Location to Store Files - It Must Exist (e.g. /home/sampson/): ')

#Inform user what we're doing
print('Beginning download of Phone Console logs from ' + ipAddress)

#Download files from the Serviceability page. This includes /FS/ directory storing console logs. 
subprocess.call ('wget -r --accept "messages*, *.tar.gz" http://' + ipAddress + '/CGI/Java/Serviceability?adapter=device.statistics.consolelog' + ' -P ' + destFolder, shell=True)

#Inform user download is complete, indicate where files are stored.
print('#################################################################################')
print('#################################################################################')
print('Files have been stored in ' + destFolder + 'in a folder named ' + ipAddress + '.')
print('#################################################################################')
print('#################################################################################')
