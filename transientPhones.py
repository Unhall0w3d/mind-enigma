#!/usr/bin/python

#import required modules
import subprocess

#Define Variables
x = input('How many phones?: ')
x = int(x)
ipAddress = []

#Loop to grab IP addresses
for i in range(x) : #Loop X amount of times based on input from user
        ipAddress.append(input('What is the phone IP address?: '))

#Grab XML Data and awk it for SEP*.
for n in ipAddress :
        subprocess.call ("curl --max-time 5 -s http://" + n + "/CGI/Java/Serviceability?adapter=device.statistics.device | awk '/SEP*/{for(i=1;i<=NF;++i)if($i~/SEP*/)print $i}'", shell=True)
