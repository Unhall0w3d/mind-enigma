# UC/UCC Health Check Scripts

Scripts with a focus on performing CLI based Health Checks on UC, and some UC VOS based UCC components.

# Introduction

These scripts provide a more efficient way to collect CLI output from applicable UC/UCC devices during pre-change and post-change activities.
As there is verification output to collect from the CLI and GUI of most components in the UC and UCC world, these scripts enable us to collect
the CLI output "in the background" while taking the necessary screenshots, backups or otherwise.

At present, you will require the Username and Password to enter in when prompted by the script. Additionally, you will need to edit the 'hostname'
list variable to include the IP addresses within the cluster that you are checking. Output is stored in the /temp/ directory created within the 
current working directory.

# Vars to Change

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

# Running the Script

To run the script, you simply need to type 'python <scriptname>.py'.
