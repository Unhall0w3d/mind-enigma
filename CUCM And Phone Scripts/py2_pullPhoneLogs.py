# Define Imports
import requests
import subprocess

# Collect IPs from user input based on how many phones we want to check


def phonecollection():
    num_phones = int(raw_input('How many phones?: '))
    if type(num_phones) != int:
        print('Error: Expected Integer.')
        exit(1)
    ips = []
    for phonecount in range(num_phones):
        ips.append(raw_input('What is the phone IP address?: '))
    return ips


# Log collection function that runs wget against consolelog url to pull recursively.
def logcollect(ip_addr):
    destfolder = str('~/')
    uris = list({
        '/CGI/Java/Serviceability?adapter=device.statistics.consolelog',
        '/localmenus.cgi?func=603',
        '/ConsoleLogs',
        '/Console_Logs.htm',
        '/Console_Logs.html',
        '/?adapter=device.statistics.consolelog',
    })
    for uri in uris:
        try:
            response = requests.get('http://{ip_addr}{uri}', timeout=6)
            if response.status_code == 200:
                subprocess.call(
                    'wget -T 5 --tries=2 -r --accept "*.log, messages*, *.tar.gz" http://' + ip_addr + uri + ' -P '
                    + destfolder,
                    shell=True)
        except requests.exceptions.ConnectionError:
            print('Far end ' + ip_addr + ' has closed the connection.')
        except requests.exceptions.Timeout:
            print('Connection to ' + ip_addr + ' timed out. Trying next.')
        except Exception as e:
            print('The script failed. Contact script dev with details from your attempt and failure.')
            print(e)

# Run script by collecting the output of function phonecollection()
# Then, perform the loccollect() function against each ip address in the array returned by phonecollection()
# Print where the files are and quit


ips = phonecollection()
[logcollect(ip_addr) for ip_addr in ips]
print('############# Files have been stored in ~/ in an IP specific folder #############')
exit()
