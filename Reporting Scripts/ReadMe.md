# UCTopTalkers
## Overview

The purpose of this script is to create a Top Talkers report for chatty devices producing syslogs often.
The report is intended to help aim UC resources to the chattiest endpoints for review and remediation.
This should drive down the amount of syslogs generated and ultimately lead to a healthier UC environment.

## General Flow

1. Prompt the user for CCM Publisher IP, GUI Username, GUI Password, OS Username, OS Password.
2. Log in to CCM Pub and identify all CCM server IPs.
   1. This is done via CLI due to AXL query returning Hostname/FQDN when servers are defined this way. To avoid potential
DNS issues, CLI is used to grab IPs.
3. Access each IP sequentially, identify *Syslog* files.
4. Download the identified files using DimeGetFile and store locally for parsing.
5. Parse Syslogs for predefined log types -- SIPTrunkOOS, Endpoint/DeviceUnregistered, TransientConnections
6. Construct a top 10 report in CSV format sorted by count for each predefined log type, if they are found.
7. Prompt for a full report (not limited to top 10).
8. Prompt for downloaded Syslog file cleanup
   1. In some instances, depending on cluster size and file count, files downloaded were in excess of 100MB.

## Required Modules

The required modules are, at a minimum, what is listed below. 
Using an older version of the module may or may not cause issues.
YMMV.

1. paramiko~=2.11.0
2. requests~=2.28.1
3. urllib3~=1.26.10
4. cryptography~=37.0.4