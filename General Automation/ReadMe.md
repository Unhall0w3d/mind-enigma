#####################################
#       NOC THOUGHTS BLOG
#    https://www.nocthoughts.com
#####################################

# Input File
-Input File ./mRemoteNG_docs/devicelist.csv is a tempalate that can be followed to create the input csv file. The valid device types are
listed, as well as an example line.
-The script will feed in every line and, based on the device type, hostname, ip address, component and sitename construct
both the registry keys to add the PuTTY session and the .csv file that can be imported into mRemoteNG based on the
port forwards built in the reg key.
-The devicelist.csv file should be in the same directory as the script when run. It will search for all .csv files within
the current working directory and present the files found as selectable options.

# Running The Script
python mRemoteNG_puttySessionCreator.py
>> Input your Session Name (e.g. JumpSvr1, CustomerName, etc.)
>> Input the Hostname/IP (e.g. IP address of port forward proxy)
>> Input the Username (e.g. Username of account that will be used to connect via PuTTY to establish tunnels)
Script should complete and create two files in ./mRemoteNG\ Sessions/ - a .csv and a .reg

# Setting Up PuTTY and mRemoteNG Sessions
Run the .reg file by double clicking to add the PuTTY session and tunnels into Saved Putty Sessions
In mRemoteNG, click on Connections, then --> File > Import > importfile.csv
Configure your PuTTY session for the newly created entry, point it to your public key file, etc. and connect.
Load one of your saved tunnel sessions and confirm it connects. This validates the tunnel functionality.