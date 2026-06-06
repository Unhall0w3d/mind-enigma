#!/usr/bin/env python3

#
# Cisco Collaboration Health Check Tool
#
# Combined / Refactored Version
# Created by Ken Perry
#

import paramiko
from paramiko_expect import SSHClientInteraction
from colorama import Fore, Style, init
import time
import os
import sys
import socket
import subprocess
import re

# ==========================================================
# INITIALIZATION
# ==========================================================

init(autoreset=True)

SSH_TIMEOUT = 60
BASE_OUTPUT_FOLDER = 'temp'
BASE_MAPPING_FOLDER = 'mappings'

cached_username = None
cached_password = None


# ==========================================================
# COMMON COMMANDS
# ==========================================================

COMMON_COMMANDS = [
    'set cli pagination off',
    'show status',
    'show version active',
    'show version inactive',
    'show hardware',
    'show network cluster',
    'show perf query class Processor',
    'show perf query class Memory',
    'utils service list',
    'utils ntp status',
    'utils disaster_recovery history backup',
    'utils disaster_recovery status backup',
    'utils dbreplication runtimestate',
    'utils core active list'
]


# ==========================================================
# TECHNOLOGY PROFILES
# ==========================================================

TECHNOLOGIES = {

    "1": {
        "name": "Cisco CallManager (CUCM)",
        "short_name": "CUCM",
        "file_prefix": "CCMHealthCheck",
        "commands": COMMON_COMMANDS + [
            'show risdb query misc phone phonefailed cmnode cmgroup cti ctiextn uone huntlist ctimlist gateway sip mediaresource h323',
            'exit'
        ]
    },

    "2": {
        "name": "Cisco Emergency Responder (CER)",
        "short_name": "CER",
        "file_prefix": "CERHealthCheck",
        "commands": COMMON_COMMANDS + [
            'exit'
        ]
    },

    "3": {
        "name": "Cisco Unity Connection (CUC)",
        "short_name": "CUC",
        "file_prefix": "CUCHealthCheck",
        "commands": COMMON_COMMANDS + [
            'show cuc cluster status',
            'exit'
        ]
    },

    "4": {
        "name": "Cisco Unified Intelligence Center (CUIC)",
        "short_name": "CUIC",
        "file_prefix": "CUICHealthCheck",
        "commands": COMMON_COMMANDS + [
            'show live-data failover',
            'show socketio status',
            'exit'
        ]
    },

    "5": {
        "name": "Cisco Finesse",
        "short_name": "FIN",
        "file_prefix": "FINHealthCheck",
        "commands": COMMON_COMMANDS + [
            'exit'
        ]
    },

    "6": {
        "name": "Cisco IM & Presence (IMP)",
        "short_name": "IMP",
        "file_prefix": "IMPHealthCheck",
        "commands": COMMON_COMMANDS + [
            'utils ha status',
            'utils imdb_replication status',
            'show perf query counter "Cisco XCP CM" "CmConnectedSockets"',
            'show perf list instances "Cisco XCP JSM Session Counters"',
            'run pe sql ttlogin select * from clientsessions',
            'run sql select * from enterprisesubcluster',
            'run sql select * from enterprisenode',
            'exit'
        ]
    },

    "7": {
        "name": "Cisco MediaSense",
        "short_name": "MS",
        "file_prefix": "MSHealthCheck",
        "commands": COMMON_COMMANDS + [
            'show tech call_control_service',
            'show db_synchronization status db_ora_config',
            'show db_synchronization status db_ora_meta',
            'exit'
        ]
    },

    "8": {
        "name": "Cisco Prime License Manager (PLM)",
        "short_name": "PLM",
        "file_prefix": "PLMHealthCheck",
        "commands": COMMON_COMMANDS + [
            'license management list users',
            'license management show system',
            'exit'
        ]
    },

    "9": {
        "name": "Cisco UCCX",
        "short_name": "UCCX",
        "file_prefix": "UCCXHealthCheck",
        "commands": COMMON_COMMANDS + [
            'show uccx jtapi_client version',
            'show uccx license',
            'show uccx livedata connections',
            'show uccx provider ip axl',
            'show uccx provider ip rmcm',
            'show uccx provider ip jtapi',
            'show uccx version',
            'exit'
        ]
    }
}


# ==========================================================
# HELPER FUNCTIONS
# ==========================================================

def sanitize_filename(hostname):

    return re.sub(r'[^A-Za-z0-9_.-]', '_', hostname)


def ping_host(host):

    try:

        count_flag = "-n" if os.name == "nt" else "-c"

        result = subprocess.run(
            ["ping", count_flag, "1", host],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        return result.returncode == 0

    except Exception:
        return False


def create_output_directory(short_name):

    timestr = time.strftime("%Y%m%d-%H%M%S")

    dirname = f"{short_name}_{timestr}"

    path = os.path.join(
        BASE_OUTPUT_FOLDER,
        dirname
    )

    if os.path.exists(path) is False:
        os.makedirs(path)

    return path, timestr


def get_credentials():

    global cached_username
    global cached_password

    if cached_username is not None:

        print()

        reuse = input(
            "Reuse cached credentials? (Y/N): "
        ).strip().lower()

        if reuse == 'y':

            return (
                cached_username,
                cached_password
            )

    username = input("Username: ")
    password = input("Password: ")

    cached_username = username
    cached_password = password

    return username, password


def get_publisher():

    print()
    print("=" * 70)
    print("Publisher Input")
    print("=" * 70)
    print()

    publisher = input(
        "Publisher IP/FQDN: "
    ).strip()

    return publisher


def write_command_output(
    output_file,
    command,
    output
):

    with open(
        output_file,
        'a',
        encoding='utf-8'
    ) as filewrite:

        filewrite.write(
            '#' * 5 +
            command +
            '#' * 5
        )

        filewrite.write('\n')
        filewrite.write(output)
        filewrite.write('\n\n')


def is_valid_ipv4(ip):

    ipv4_pattern = re.compile(
        r'^(\d{1,3}\.){3}\d{1,3}$'
    )

    if not ipv4_pattern.match(ip):
        return False

    octets = ip.split('.')

    return all(
        0 <= int(octet) <= 255
        for octet in octets
    )


def resolve_publisher(
    publisher
):

    if is_valid_ipv4(
        publisher
    ):

        return publisher

    try:

        resolved_ip = (
            socket.gethostbyname(
                publisher
            )
        )

        print(
            f"[INFO] "
            f"Resolved "
            f"{publisher} "
            f"-> "
            f"{resolved_ip}"
        )

        return resolved_ip

    except Exception:

        print()
        print(
            Fore.RED +
            "[ERROR] "
            "Unable to resolve "
            "publisher FQDN."
        )

        return None


def parse_cluster_ips(cluster_output, publisher_ip):

    hosts = []
    collecting = False

    for line in cluster_output.splitlines():

        line = line.strip()

        if line.startswith('Server Table'):
            if collecting:
                break
            continue

        if not line:
            continue

        parts = line.split()

        if len(parts) == 0:
            continue

        first_token = parts[0]

        if is_valid_ipv4(first_token):

            collecting = True

            if first_token not in hosts:
                hosts.append(first_token)

    if publisher_ip in hosts:
        hosts.remove(publisher_ip)

    hosts.insert(0, publisher_ip)

    return hosts


# ==========================================================
# PROFILE / MAPPING FUNCTIONS
# ==========================================================

def get_mapping_directory(
    technology
):

    mapping_dir = os.path.join(
        BASE_MAPPING_FOLDER,
        technology[
            "short_name"
        ]
    )

    if os.path.exists(mapping_dir) is False:
        os.makedirs(mapping_dir)

    return mapping_dir


def list_profiles(
    technology
):

    mapping_dir = get_mapping_directory(
        technology
    )

    profiles = []

    for filename in os.listdir(
        mapping_dir
    ):

        if filename.lower().endswith(
            '.txt'
        ):

            profiles.append(
                filename[:-4]
            )

    profiles.sort()

    return profiles


def profile_file_path(
    technology,
    client_id
):

    mapping_dir = get_mapping_directory(
        technology
    )

    safe_client_id = sanitize_filename(
        client_id
    )

    return os.path.join(
        mapping_dir,
        f"{safe_client_id}.txt"
    )


def read_profile(
    technology,
    client_id
):

    path = profile_file_path(
        technology,
        client_id
    )

    publisher = None
    hosts = []

    if os.path.exists(path) is False:

        return (
            publisher,
            hosts
        )

    with open(
        path,
        'r',
        encoding='utf-8'
    ) as file_read:

        lines = [
            line.strip()
            for line in file_read.readlines()
            if line.strip()
        ]

    for line in lines:

        if line.lower().startswith(
            'publisher='
        ):

            publisher = line.split(
                '=',
                1
            )[1].strip()

        elif is_valid_ipv4(
            line
        ):

            if line not in hosts:
                hosts.append(line)

    if publisher is None and len(hosts) > 0:

        publisher = hosts[0]

    return (
        publisher,
        hosts
    )


def save_profile(
    technology,
    client_id,
    publisher,
    hosts
):

    path = profile_file_path(
        technology,
        client_id
    )

    clean_hosts = []

    if publisher not in clean_hosts:
        clean_hosts.append(
            publisher
        )

    for host in hosts:

        if host not in clean_hosts:
            clean_hosts.append(
                host
            )

    with open(
        path,
        'w',
        encoding='utf-8'
    ) as file_write:

        file_write.write(
            f"publisher={publisher}\n"
        )

        for host in clean_hosts:

            file_write.write(
                f"{host}\n"
            )

    print()
    print(
        f"[INFO] "
        f"Profile saved: "
        f"{path}"
    )


def select_client_profile(
    technology
):

    profiles = list_profiles(
        technology
    )

    print()
    print("=" * 70)
    print("Client Profile")
    print("=" * 70)
    print()

    if len(profiles) > 0:

        print("Saved Profiles")
        print()

        for index, profile in enumerate(
            profiles,
            start=1
        ):

            print(
                f"{index}. "
                f"{profile}"
            )

        print()
        print("N. New ClientID")
        print()

        while True:

            selection = input(
                "Selection: "
            ).strip()

            if selection.lower() == 'n':

                break

            if selection.isdigit():

                index = int(selection)

                if (
                    index >= 1 and
                    index <= len(profiles)
                ):

                    client_id = profiles[
                        index - 1
                    ]

                    publisher, hosts = read_profile(
                        technology,
                        client_id
                    )

                    print()
                    print(
                        f"[INFO] "
                        f"Selected profile: "
                        f"{client_id}"
                    )

                    print(
                        f"[INFO] "
                        f"Publisher: "
                        f"{publisher}"
                    )

                    print(
                        f"[INFO] "
                        f"Stored node count: "
                        f"{len(hosts)}"
                    )

                    return {
                        "client_id": client_id,
                        "publisher": publisher,
                        "hosts": hosts,
                        "is_new": False
                    }

            print(
                "Invalid selection."
            )

    print()
    client_id = input(
        "Enter ClientID: "
    ).strip()

    while client_id == "":

        client_id = input(
            "Enter ClientID: "
        ).strip()

    publisher = get_publisher()

    publisher = resolve_publisher(
        publisher
    )

    if publisher is None:

        return None

    return {
        "client_id": sanitize_filename(
            client_id
        ),
        "publisher": publisher,
        "hosts": [],
        "is_new": True
    }


# ==========================================================
# DISCOVERY FUNCTION
# ==========================================================

def discover_cluster_nodes(
    publisher,
    username,
    password,
    output_path,
    timestr
):

    print()
    print(
        "[DISCOVERY] "
        "Connecting to Publisher..."
    )

    sshconnect = paramiko.SSHClient()

    sshconnect.set_missing_host_key_policy(
        paramiko.AutoAddPolicy()
    )

    discovery_file = os.path.join(
        output_path,
        (
            "ClusterDiscovery_"
            f"{sanitize_filename(publisher)}"
            f"_{timestr}.txt"
        )
    )

    discovery_commands = [
        'set cli pagination off',
        'show network cluster',
        'exit'
    ]

    try:

        sshconnect.connect(
            hostname=publisher,
            username=username,
            password=password
        )

        print(
            "[DISCOVERY] "
            "Collecting cluster topology..."
        )

        interact = SSHClientInteraction(
            sshconnect,
            timeout=60,
            display=True
        )

        previous_command = "Connected"

        for command in discovery_commands:

            interact.expect(
                'admin:'
            )

            devoutput = (
                interact.current_output_clean
            )

            write_command_output(
                discovery_file,
                previous_command,
                devoutput
            )

            interact.send(
                command
            )

            previous_command = command

        sshconnect.close()

        with open(discovery_file, 'r', encoding='utf-8') as file_read:
            discovery_file_contents = file_read.read()

        hosts = parse_cluster_ips(
            discovery_file_contents,
            publisher
        )

        print(
            f"[DISCOVERY] "
            f"Found "
            f"{len(hosts)} "
            f"cluster node(s)"
        )

        print()
        print("=" * 70)
        print(
            "Discovered "
            "Cluster Nodes"
        )
        print("=" * 70)
        print()

        for index, host in enumerate(
            hosts,
            start=1
        ):

            print(
                f"{index}. "
                f"{host}"
            )

        print()

        proceed = input(
            "Proceed with "
            "health check? "
            "(Y/N): "
        ).strip().lower()

        if proceed != 'y':

            print()
            print(
                "Cancelled by user."
            )

            return None

        return hosts

    except paramiko.ssh_exception.AuthenticationException:

        print()
        print(
            Fore.YELLOW +
            "[DISCOVERY FAILED] "
            "Authentication Failed"
        )

        return None

    except Exception as error:

        print()
        print(
            Fore.RED +
            "[DISCOVERY FAILED] "
            "SSH Connection Failed"
        )

        print(
            Fore.RED +
            str(error)
        )

        return None

    finally:

        try:
            sshconnect.close()

        except Exception:
            pass


# ==========================================================
# HEALTH CHECK ENGINE
# ==========================================================

def run_health_checks(
    technology,
    hosts,
    username,
    password,
    output_path,
    timestr
):

    results = []

    print()
    print("=" * 70)
    print(
        f"Starting "
        f"{technology['name']} "
        f"Health Check"
    )
    print("=" * 70)

    for host in hosts:

        print()
        print(
            f"[INFO] "
            f"Processing: "
            f"{host}"
        )

        output_filename = (
            f"{technology['file_prefix']}"
            f"_"
            f"{sanitize_filename(host)}"
            f"_{timestr}.txt"
        )

        output_file = (
            os.path.join(
                output_path,
                output_filename
            )
        )

        sshconnect = None

        try:

            if ping_host(host):

                print(
                    Fore.GREEN +
                    f"[PING SUCCESS] "
                    f"{host}"
                )

            else:

                print(
                    Fore.YELLOW +
                    f"[PING FAILED] "
                    f"{host} "
                    f"(Attempting SSH anyway)"
                )

            sshconnect = (
                paramiko.SSHClient()
            )

            sshconnect.set_missing_host_key_policy(
                paramiko.AutoAddPolicy()
            )

            sshconnect.connect(
                hostname=host,
                username=username,
                password=password
            )

            interact = (
                SSHClientInteraction(
                    sshconnect,
                    timeout=60,
                    display=True
                )
            )

            previous_command = "Connected"

            for command in (
                technology[
                    "commands"
                ]
            ):

                interact.expect(
                    'admin:'
                )

                devoutput = (
                    interact.current_output_clean
                )

                write_command_output(
                    output_file,
                    previous_command,
                    devoutput
                )

                interact.send(
                    command
                )

                previous_command = command

            sshconnect.close()

            print(
                '\n' +
                Fore.GREEN +
                f"[SUCCESS] "
                f"{host}"
            )

            results.append({
                "host": host,
                "result":
                    "Connected Successfully",
                "status":
                    "green",
                "file":
                    output_filename,
                "failure_type":
                    None
            })

        except paramiko.ssh_exception.AuthenticationException:

            print(
                Fore.YELLOW +
                f"[FAILED] "
                f"{host} "
                f"(Authentication)"
            )

            results.append({
                "host": host,
                "result":
                    "Authentication Failed",
                "status":
                    "yellow",
                "file":
                    output_filename,
                "failure_type":
                    "auth"
            })

        except Exception as error:

            print(
                Fore.RED +
                f"[FAILED] "
                f"{host} "
                f"(SSH)"
            )

            print(
                Fore.RED +
                str(error)
            )

            results.append({
                "host": host,
                "result":
                    "SSH Connection Failed",
                "status":
                    "red",
                "file":
                    output_filename,
                "failure_type":
                    "connection"
            })

        finally:

            try:

                if sshconnect is not None:
                    sshconnect.close()

            except Exception:
                pass

    return results


# ==========================================================
# SESSION FUNCTION
# ==========================================================

def session(
    technology
):

    profile = select_client_profile(
        technology
    )

    if profile is None:
        return

    username, password = (
        get_credentials()
    )

    client_id = profile[
        "client_id"
    ]

    publisher = profile[
        "publisher"
    ]

    stored_hosts = profile[
        "hosts"
    ]

    short_name = (
        technology[
            "short_name"
        ]
    )

    output_path, timestr = (
        create_output_directory(
            short_name
        )
    )

    if len(stored_hosts) == 0:

        hosts = discover_cluster_nodes(
            publisher,
            username,
            password,
            output_path,
            timestr
        )

        if hosts is None:
            return

        save_profile(
            technology,
            client_id,
            publisher,
            hosts
        )

    else:

        hosts = stored_hosts

        print()
        print("=" * 70)
        print(
            "Using Stored "
            "Client Profile"
        )
        print("=" * 70)
        print()

        print(
            f"ClientID: "
            f"{client_id}"
        )

        print(
            f"Publisher: "
            f"{publisher}"
        )

        print()

        for index, host in enumerate(
            hosts,
            start=1
        ):

            print(
                f"{index}. "
                f"{host}"
            )

    results = run_health_checks(
        technology,
        hosts,
        username,
        password,
        output_path,
        timestr
    )

    connection_failures = [
        result
        for result in results
        if result[
            "failure_type"
        ] == "connection"
    ]

    publisher_failed = any(
        result["host"] == publisher
        and result[
            "failure_type"
        ] == "connection"
        for result in results
    )

    auth_failed = any(
        result[
            "failure_type"
        ] == "auth"
        for result in results
    )

    if (
        len(connection_failures) > 0
        and not publisher_failed
        and not auth_failed
    ):

        print()
        print(
            Fore.YELLOW +
            "[INFO] "
            "One or more stored profile nodes failed. "
            "Attempting cluster rediscovery from Publisher..."
        )

        discovered_hosts = discover_cluster_nodes(
            publisher,
            username,
            password,
            output_path,
            timestr
        )

        if discovered_hosts is not None:

            save_profile(
                technology,
                client_id,
                publisher,
                discovered_hosts
            )

            print()
            print(
                Fore.YELLOW +
                "[INFO] "
                "Retrying health check using refreshed profile..."
            )

            retry_timestr = time.strftime(
                "%Y%m%d-%H%M%S"
            )

            results = run_health_checks(
                technology,
                discovered_hosts,
                username,
                password,
                output_path,
                retry_timestr
            )

    elif publisher_failed:

        print()
        print(
            Fore.RED +
            "[INFO] "
            "Publisher failed. "
            "Skipping rediscovery because Publisher is required "
            "for topology discovery."
        )

    write_summary(
        results,
        output_path,
        timestr
    )


# ==========================================================
# HEALTH REPORT LAUNCHER
# ==========================================================

def launch_health_report(
    output_path
):

    report_script = os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)
        ),
        'health_report.py'
    )

    if os.path.exists(report_script) is False:

        print()
        print(
            Fore.RED +
            '[ERROR] '
            'health_report.py was not found.'
        )

        return

    print()
    print(
        '[INFO] '
        'Launching parser/report runner...'
    )

    subprocess.run(
        [
            sys.executable,
            report_script,
            output_path
        ]
    )


# ==========================================================
# SUMMARY REPORT
# ==========================================================

def write_summary(
    results,
    output_path,
    timestr
):

    summary_filename = (
        f"Summary_"
        f"{timestr}.txt"
    )

    summary_file = (
        os.path.join(
            output_path,
            summary_filename
        )
    )

    print()
    print("=" * 100)
    print(
        "Health Check Summary"
    )
    print("=" * 100)

    header = (
        f"{'Server IP/FQDN':<35}"
        f"{'Result':<30}"
        f"{'Output File'}"
    )

    print(header)
    print('-' * 100)

    with open(
        summary_file,
        'w',
        encoding='utf-8'
    ) as filewrite:

        filewrite.write(
            "=" * 100 +
            "\n"
        )

        filewrite.write(
            "Health Check Summary\n"
        )

        filewrite.write(
            "=" * 100 +
            "\n"
        )

        filewrite.write(
            header +
            "\n"
        )

        filewrite.write(
            '-' * 100 +
            "\n"
        )

        for result in results:

            status = (
                result[
                    "status"
                ]
            )

            color = (
                Fore.GREEN
                if status ==
                "green"
                else
                Fore.YELLOW
                if status ==
                "yellow"
                else
                Fore.RED
            )

            line = (
                f"{result['host']:<35}"
                f"{result['result']:<30}"
                f"{result['file']}"
            )

            print(
                color +
                line
            )

            filewrite.write(
                line + '\n'
            )

    print()
    print(
        f"Summary written to: "
        f"{summary_file}"
    )

    print()
    print("=" * 70)
    print(
        "Return to Main Menu, Parse Output, or Quit?"
    )
    print("=" * 70)

    while True:

        selection = input(
            "[Y] Main Menu | [P] Parse Output | [N/Q] Quit: "
        ).strip().lower()

        if selection == 'y':
            return

        elif selection == 'p':

            launch_health_report(
                output_path
            )

            print()
            print("=" * 70)
            print(
                "Return to Main Menu or Quit?"
            )
            print("=" * 70)

        elif selection in [
            'n',
            'q'
        ]:
            sys.exit()

        else:
            print(
                "Invalid choice."
            )


# ==========================================================
# MENU
# ==========================================================

def show_menu():

    print()
    print("=" * 70)
    print(
        "Cisco Collaboration "
        "Health Check Tool"
    )
    print("=" * 70)
    print()

    for key, value in (
        TECHNOLOGIES.items()
    ):

        print(
            f"{key}. "
            f"{value['name']}"
        )

    print()
    print("Q. Quit")
    print()


# ==========================================================
# MAIN LOOP
# ==========================================================

def main():

    while True:

        show_menu()

        selection = input(
            "Selection: "
        ).strip().lower()

        if selection == 'q':

            print(
                "\nExiting..."
            )

            break

        if (
            selection
            not in
            TECHNOLOGIES
        ):

            print(
                "\nInvalid "
                "selection.\n"
            )

            continue

        technology = (
            TECHNOLOGIES[
                selection
            ]
        )

        session(
            technology
        )


# ==========================================================
# START SCRIPT
# ==========================================================

if __name__ == "__main__":

    try:
        main()

    except KeyboardInterrupt:

        print()
        print("Interrupted by user.")
        sys.exit(0)
