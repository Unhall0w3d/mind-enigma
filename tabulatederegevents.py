#!/usr/var/python
# -*- code:UTF-8 -*-

# NOTE #
# Input 'ungeg.txt' can be created by running the below command in the same folder as syslog data from UCM. #
# 'grep -r 'Unregistered' * > unreg.txt' #
import re
import numpy as np
from tabulate import tabulate


class PhoneEvent(object):
    def __init__(self, data):
        for d in data:
            attrs = d.split('=')
            setattr(self, attrs[0].lower(), attrs[1])


def process_event(event):
    data = re.search(r'\[.*\]', event).group().split('][')
    data = [re.sub(r'[\[\]]', '', e) for e in data]
    return PhoneEvent(data)


if __name__ == '__main__':
    events = []
    with open('unreg.txt') as reader:
        lines = reader.read().splitlines()
        for line in lines:
            events.append(process_event(line))
            reasons = np.array([e.reason for e in events if getattr(e, 'reason', None)])
            count_data = np.unique(reasons, return_counts=True)
            table = tabulate(count_data, tablefmt="fancy_grid")

print(table)
