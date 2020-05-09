import re
import requests
from bs4 import BeautifulSoup
from collections import OrderedDict


def phonecollection():
    with open('iplist.txt') as txtfile:
        lines = [line.rstrip() for line in txtfile]
        for line in txtfile:
            lines.append(line)
    return lines


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
                break
        except requests.exceptions.ConnectionError:
            print('Far end ' + ip_addr + 'has closed the connection.')
        except requests.exceptions.Timeout:
            print('Connection to ' + ip_addr + ' timed out. Trying next.')
        except Exception as e:
            print('The script failed. Contact script dev with details from your attempt and failure.')
            print(e)


phone_ips = phonecollection()

print('Script is running. Please wait, output will follow.')

[phoneregcheck(ip_addr) for ip_addr in phone_ips]
