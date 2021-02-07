```
#####################################
# Script created by Ken Perry, 2020 #
#       NOC THOUGHTS BLOG           #
#    https://www.nocthoughts.com    #
#####################################
```

# Introduction

This script is designed to log in to a list of Cisco Expressway IP addresses using user provided username/pw and pull
the output of the command 'cat /proc/meminfo | grep Committed_AS'. This is in reference to guidance provided on the
Cisco Support forums (https://community.cisco.com/t5/telepresence-and-video/expressway-memory-usage/td-p/3743732).

The script is set up to loop and log the data to a file in 'temp' folder which gets created in the Current Working
Directory. There are lines that will allow you to email the output of the file in the body of an email, as well as
reporting back via email if the script hits an exception. It sleeps for 12 hours and runs again. As mentioned in the
scripts comments, if you're using this at all you likely need to run it more than once. This helps automate it.

# Imported Modules

time
paramiko
os
getpass

# Running the Script

If you require invoking a virtual environment you likely already know how to do this, however, to run this script in a
Screen and detatch after providing required input, do the below:

```
#Run Directly
screen bash -c 'python expresswayMemoryCheck.py'

#Invoke venv and run (edit as needed)
screen bash -c 'cd /home/user/foldercontainingvenv/; source venv/bin/activate; cd /home/user/scriptlocation/; python expresswayMemorycheck.py'

#To Detatch from Screen
ctrl+A --> "d"

#To Attach to Screen
screen -list
    verify the process id. The screen name will be something like "22016.something". The number will change.
screen -r 22016
```


# Variables You May Want To Change

```
# Define list of IP Addresses to SSH to.
# Replace the ip-addr# in quotes with an IP address (e.g. 10.161.1.133), one per line.
# Follow the syntax below to add additional entries
hostname = [
    "ip-addr1",
    "ip-addr2"
]

# Define folder name where files will be stored.
# Change this to your desired folder name.
dirname = 'temp'
```

# To get Emails working

Pay attention to the below lines in the script and modify the required values. Uncomment the line if it is to be used.

Modify "email@domain.com" to your email address, or a distribution list. If preferred, create a variable and substitute
the variable in. (e.g. os.system('mail -s "Expressway Healthchecks" ' + emailVar + ' < ' + path + filename + '')

```
    # The below allows you to email the file to your email, or a distro list if you have smtp configured on your linux machine.
    # "mail" command should work before trying to use it through this script.
    # os.system('mail -s "Expressway Healthchecks" email@domain.com < ' + path + filename + '')
```

Uncomment the below print statement if you want to validate that the gathering (healthcheck()) and file handling/emailing
(filehandling()) functions executed properly on initial test. Re-comment or remove after if desired.

```
    # Uncomment the line below if you use the email function above.
    # print("Email has been sent.")
```

Comment out the print statement if you won't be monitoring the screen session. Or don't.
Uncomment the os.system line for an email to be sent indicating the script hit an exception.
Change the verbiage in quotes as desired.

```
    print("Oh no! We failed somewhere. We'll try again in 6 hours. Use Email function for better notifications.")
    # os.system('mail -s "Expressway Script Hit Exception | Verify Script Status" email@domain.com')
```