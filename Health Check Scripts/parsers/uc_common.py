#!/usr/bin/env python3

"""
Cisco UC common parser and report helpers.

This parser is intentionally conservative. It extracts common facts and applies
only the first-pass health rules that have been discussed so far.
"""

import os
import re
from datetime import datetime

SECTION_PATTERN = re.compile(r'^#{5}(.+?)#{5}\s*$', re.MULTILINE)
IPV4_PATTERN = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')

MONTHS = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
    'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
    'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12,
}

CRITICAL_SERVICES = {
    # These are intentionally conservative starter lists and can be tuned.
    'CUCM': [
        'A Cisco DB',
        'A Cisco DB Replicator',
        'Cisco CallManager',
        'Cisco CTIManager',
        'Cisco Tomcat',
        'Cisco Tftp',
        'Cisco DRF Local',
        'Cisco RIS Data Collector',
    ],
    'CUC': [
        'A Cisco DB',
        'A Cisco DB Replicator',
        'Cisco Tomcat',
        'Connection Administration',
        'Connection Conversation Manager',
        'Connection Mixer',
        'Connection Notifier',
    ],
    'CER': [
        'A Cisco DB Replicator',
        'CER Provider',
        'Cisco Emergency Responder',
        'Cisco Tomcat',
    ],
}


def is_valid_ipv4(value):
    if not IPV4_PATTERN.match(value):
        return False
    return all(0 <= int(octet) <= 255 for octet in value.split('.'))


def infer_technology_from_folder(run_folder):
    folder_name = os.path.basename(os.path.normpath(run_folder))
    if '_' in folder_name:
        return folder_name.split('_', 1)[0]
    return 'UNKNOWN'


def infer_timestamp_from_folder(run_folder):
    folder_name = os.path.basename(os.path.normpath(run_folder))
    if '_' in folder_name:
        return folder_name.split('_', 1)[1]
    return 'UNKNOWN'


def parse_timestamp(timestamp):
    try:
        return datetime.strptime(timestamp, '%Y%m%d-%H%M%S')
    except Exception:
        return None


def split_sections(file_contents):
    matches = list(SECTION_PATTERN.finditer(file_contents))
    sections = []

    for index, match in enumerate(matches):
        section_name = match.group(1).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(file_contents)
        section_text = file_contents[start:end].strip('\n')
        sections.append((section_name, section_text))

    return sections


def section_map(sections):
    return {name: text for name, text in sections}


def clean_section_output(command, text):
    """Remove echoed command line if present."""
    lines = text.splitlines()
    while lines and lines[0].strip() == '':
        lines.pop(0)
    if lines and lines[0].strip().lower() == command.strip().lower():
        lines.pop(0)
    return '\n'.join(lines).strip('\n')


def get_section(sections, command):
    raw = sections.get(command, '')
    return clean_section_output(command, raw)


def extract_node_ip_from_filename(filename):
    matches = re.findall(r'(\d{1,3}(?:\.\d{1,3}){3})', filename)
    for match in matches:
        if is_valid_ipv4(match):
            return match
    return 'UNKNOWN'


def parse_key_value_lines(text):
    data = {}
    for line in text.splitlines():
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            if key:
                data[key] = value
    return data


def parse_uptime_days(text):
    match = re.search(r'up\s+(?:(\d+)\s+days?,\s*)?(\d+):(\d+)', text)
    if not match:
        return None
    days = int(match.group(1) or 0)
    hours = int(match.group(2))
    minutes = int(match.group(3))
    return days + (hours / 24) + (minutes / 1440)


def parse_show_status(text):
    data = parse_key_value_lines(text)

    cpu = {}
    cpu_line = re.search(
        r'CPU Idle:\s*([\d.]+)%\s+System:\s*([\d.]+)%\s+User:\s*([\d.]+)%',
        text
    )
    if cpu_line:
        cpu['idle_percent'] = float(cpu_line.group(1))
        cpu['system_percent'] = float(cpu_line.group(2))
        cpu['user_percent'] = float(cpu_line.group(3))
        cpu['used_percent'] = round(100 - cpu['idle_percent'], 2)

    io_line = re.search(
        r'IOWAIT:\s*([\d.]+)%\s+IRQ:\s*([\d.]+)%\s+Soft:\s*([\d.]+)%',
        text
    )
    if io_line:
        cpu['iowait_percent'] = float(io_line.group(1))
        cpu['irq_percent'] = float(io_line.group(2))
        cpu['soft_percent'] = float(io_line.group(3))

    memory = {}
    for key in ['Memory Total', 'Free', 'Used', 'Cached', 'Shared', 'Buffers']:
        match = re.search(rf'{re.escape(key)}:\s+(\d+)K', text)
        if match:
            memory[key.lower().replace(' ', '_') + '_kb'] = int(match.group(1))

    if memory.get('memory_total_kb') and memory.get('used_kb'):
        memory['used_percent'] = round(
            (memory['used_kb'] / memory['memory_total_kb']) * 100,
            2
        )

    disks = []
    for line in text.splitlines():
        match = re.match(r'(Disk/\S+)\s+(\d+)K\s+(\d+)K\s+(\d+)K\s+\((\d+)%\)', line.strip())
        if match:
            disks.append({
                'name': match.group(1),
                'total_kb': int(match.group(2)),
                'free_kb': int(match.group(3)),
                'used_kb': int(match.group(4)),
                'used_percent': int(match.group(5)),
            })

    uptime_days = parse_uptime_days(text)

    status = 'Good'
    notes = []
    if uptime_days is not None and uptime_days >= 365:
        status = 'Warning'
        notes.append('Uptime is at or above 365 days. Reboot planning is recommended.')

    for disk in disks:
        if disk['used_percent'] >= 95:
            status = 'Critical'
            notes.append(f"{disk['name']} usage is {disk['used_percent']}%.")
        elif disk['used_percent'] >= 90 and status != 'Critical':
            status = 'Warning'
            notes.append(f"{disk['name']} usage is {disk['used_percent']}%.")

    return {
        'status': status,
        'notes': notes,
        'hostname': data.get('Host Name'),
        'date': data.get('Date'),
        'time_zone': data.get('Time Zone'),
        'locale': data.get('Locale'),
        'product_version': data.get('Product Ver'),
        'unified_os_version': data.get('Unified OS Version'),
        'uptime_days': round(uptime_days, 2) if uptime_days is not None else None,
        'cpu': cpu,
        'memory': memory,
        'disks': disks,
    }


def parse_version(text, active=True):
    label = 'Active' if active else 'Inactive'
    version_match = re.search(rf'{label} Master Version:\s*(\S+)', text)
    version = version_match.group(1) if version_match else None

    installed_options = []
    capture = False
    for line in text.splitlines():
        stripped = line.strip()
        if 'Installed Software Options' in stripped:
            capture = True
            continue
        if capture:
            if not stripped:
                continue
            if stripped.lower().startswith('no installed software options found'):
                continue
            installed_options.append(stripped)

    return {
        'version': version,
        'installed_options': installed_options,
    }


def parse_hardware(text):
    data = parse_key_value_lines(text)
    disk_sizes = []
    for match in re.finditer(r'Size \(in GB\)\s*:\s*(\d+)', text):
        disk_sizes.append(int(match.group(1)))
    return {
        'hw_platform': data.get('HW Platform'),
        'processors': data.get('Processors'),
        'cpu_type': data.get('Type'),
        'cpu_speed': data.get('CPU Speed'),
        'memory_mb': data.get('Memory'),
        'os_version': data.get('OS Version'),
        'serial_number': data.get('Serial Number'),
        'disk_sizes_gb': disk_sizes,
    }


def parse_cluster(text):
    nodes = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 7 and is_valid_ipv4(parts[0]):
            nodes.append({
                'ip': parts[0],
                'fqdn': parts[1],
                'hostname': parts[2],
                'role': parts[3],
                'application': parts[4],
                'db_role': parts[5],
                'auth_status': parts[6],
                'transport': parts[8] if len(parts) > 8 and parts[7].lower() == 'using' else None,
                'raw': line.strip(),
            })
    return nodes


def parse_perf_processor(text):
    if 'No valid command entered' in text:
        return {'supported': False, 'status': 'Not Supported', 'processors': []}

    processors = {}
    for line in text.splitlines():
        match = re.match(r'\s*(\S+)\s+->\s+(.+?)\s+=\s+(-?\d+(?:\.\d+)?)', line)
        if match:
            instance = match.group(1)
            counter = match.group(2).strip()
            value = float(match.group(3))
            processors.setdefault(instance, {})[counter] = value

    return {
        'supported': True,
        'status': 'Parsed' if processors else 'No Data',
        'processors': processors,
    }


def parse_perf_memory(text):
    if 'No valid command entered' in text:
        return {'supported': False, 'status': 'Not Supported', 'counters': {}}

    counters = {}
    for line in text.splitlines():
        match = re.match(r'\s*->\s+(.+?)\s+=\s+(-?\d+(?:\.\d+)?)', line)
        if match:
            counters[match.group(1).strip()] = float(match.group(2))

    return {
        'supported': True,
        'status': 'Parsed' if counters else 'No Data',
        'counters': counters,
    }


def parse_services(text, technology):
    services = []
    for line in text.splitlines():
        match = re.match(r'(.+?)\[(STARTED|STOPPED|STARTING|STOPPING|UNKNOWN|NOT STARTED)\]', line.strip())
        if match:
            services.append({
                'name': match.group(1).strip(),
                'state': match.group(2).strip(),
            })

    not_started = [svc for svc in services if svc['state'] != 'STARTED']
    critical_names = CRITICAL_SERVICES.get(technology, [])
    critical = [svc for svc in services if svc['name'] in critical_names]
    critical_not_started = [svc for svc in critical if svc['state'] != 'STARTED']

    status = 'Good'
    notes = []
    if critical_not_started:
        status = 'Critical'
        notes.append('One or more defined critical services are not STARTED.')
    elif not_started:
        status = 'Warning'
        notes.append('One or more services are not STARTED.')

    missing_critical = [name for name in critical_names if name not in [svc['name'] for svc in services]]
    if missing_critical:
        notes.append('Some defined critical services were not present in service output; review technology-specific service list.')

    return {
        'status': status,
        'notes': notes,
        'service_count': len(services),
        'not_started_count': len(not_started),
        'critical_service_count': len(critical),
        'critical_not_started_count': len(critical_not_started),
        'not_started': not_started,
        'critical_services': critical,
        'critical_not_started': critical_not_started,
        'missing_defined_critical_services': missing_critical,
        'services': services,
    }


def parse_ntp(text, node_role):
    running = 'chronyd' in text and 'is running' in text
    server_lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith('^'):
            server_lines.append(stripped)

    stratum_match = re.search(r'synchronised to NTP server \(([^)]+)\) at stratum (\d+)', text)
    server = stratum_match.group(1) if stratum_match else None
    stratum = int(stratum_match.group(2)) if stratum_match else None

    status = 'Good'
    notes = []
    if not running or stratum is None:
        status = 'Critical'
        notes.append('NTP does not appear synchronized.')
    elif node_role == 'Publisher' and stratum > 4:
        status = 'Critical'
        notes.append('Publisher NTP stratum is higher than 4.')
    elif node_role == 'Subscriber' and stratum > 6:
        status = 'Critical'
        notes.append('Subscriber NTP stratum is higher than expected.')

    down_or_bad = []
    for line in server_lines:
        if line.startswith('^?') or line.startswith('^x') or line.startswith('^-'):
            down_or_bad.append(line)
    if down_or_bad and status != 'Critical':
        status = 'Warning'
        notes.append('One or more NTP sources may be unavailable or unsuitable.')

    return {
        'status': status,
        'notes': notes,
        'chronyd_running': running,
        'synchronized_server': server,
        'stratum': stratum,
        'source_lines': server_lines,
        'down_or_bad_sources': down_or_bad,
    }


def parse_backup_dates(text):
    dates = []
    pattern = re.compile(r'([A-Z][a-z]{2})\s+([A-Z][a-z]{2})\s+(\d{1,2})\s+(\d{2}:\d{2}:\d{2})\s+\S+\s+(\d{4})\s+SUCCESS')
    for match in pattern.finditer(text):
        dow, mon, day, time_part, year = match.groups()
        try:
            month = MONTHS[mon]
            hour, minute, second = [int(part) for part in time_part.split(':')]
            dates.append(datetime(int(year), month, int(day), hour, minute, second))
        except Exception:
            pass
    return dates


def parse_backups(history_text, status_text, reference_date):
    history_successes = parse_backup_dates(history_text)
    status_successes = parse_backup_dates(status_text)
    all_successes = history_successes + status_successes
    latest = max(all_successes) if all_successes else None

    if latest and reference_date:
        age_days = (reference_date - latest).days
    else:
        age_days = None

    status = 'Good'
    notes = []
    if latest is None:
        status = 'Warning'
        notes.append('No successful backup was found in parsed backup output.')
    elif age_days is not None and age_days > 7:
        status = 'Warning'
        notes.append('No successful backup was found within the last 7 days.')

    return {
        'status': status,
        'notes': notes,
        'latest_successful_backup': latest,
        'latest_successful_backup_age_days': age_days,
        'successful_backup_count': len(all_successes),
        'history_unavailable': 'No backup history available' in history_text,
        'status_unavailable': 'No backup status available' in status_text,
    }


def parse_dbreplication(text):
    if 'No valid command entered' in text:
        return {
            'status': 'Not Supported',
            'notes': ['DB replication runtime state command is not supported on this platform.'],
            'sync_status': None,
            'node_rows': [],
        }

    sync_status = None
    match = re.search(r'Sync Status:\s*(.+)', text)
    if match:
        sync_status = match.group(1).strip()

    node_rows = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 7 and is_valid_ipv4(parts[1]):
            node_rows.append(line.strip())

    status = 'Good'
    notes = []
    if sync_status and 'All Tables are in sync' not in sync_status:
        status = 'Warning'
        notes.append(sync_status)
    elif not sync_status:
        status = 'Informational'
        notes.append('DB replication summary was not parsed from this output.')

    return {
        'status': status,
        'notes': notes,
        'sync_status': sync_status,
        'node_rows': node_rows,
    }


def parse_core_files(text):
    if 'No core files found' in text:
        return {
            'status': 'Good',
            'notes': ['No core files found.'],
            'core_files': [],
        }

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    lines = [line for line in lines if not line.lower().startswith('utils core active list')]
    if lines:
        return {
            'status': 'Critical',
            'notes': ['Core files were found. Cisco TAC engagement/review is recommended.'],
            'core_files': lines,
        }

    return {
        'status': 'Informational',
        'notes': ['Core file output was empty or not recognized.'],
        'core_files': [],
    }


def parse_healthcheck_file(path, technology, run_timestamp):
    with open(path, 'r', encoding='utf-8', errors='replace') as file_read:
        contents = file_read.read()

    sections_list = split_sections(contents)
    sections = section_map(sections_list)
    node_ip = extract_node_ip_from_filename(os.path.basename(path))

    status = parse_show_status(get_section(sections, 'show status'))
    active_version = parse_version(get_section(sections, 'show version active'), active=True)
    inactive_version = parse_version(get_section(sections, 'show version inactive'), active=False)
    hardware = parse_hardware(get_section(sections, 'show hardware'))
    cluster_nodes = parse_cluster(get_section(sections, 'show network cluster'))
    node_role = None
    for node in cluster_nodes:
        if node['ip'] == node_ip:
            node_role = node['role']
            break

    processor = parse_perf_processor(get_section(sections, 'show perf query class Processor'))
    memory_perf = parse_perf_memory(get_section(sections, 'show perf query class Memory'))
    services = parse_services(get_section(sections, 'utils service list'), technology)
    ntp = parse_ntp(get_section(sections, 'utils ntp status'), node_role)
    backups = parse_backups(
        get_section(sections, 'utils disaster_recovery history backup'),
        get_section(sections, 'utils disaster_recovery status backup'),
        run_timestamp,
    )
    dbreplication = parse_dbreplication(get_section(sections, 'utils dbreplication runtimestate'))
    core_files = parse_core_files(get_section(sections, 'utils core active list'))

    return {
        'path': path,
        'filename': os.path.basename(path),
        'node_ip': node_ip,
        'section_names': [section[0] for section in sections_list],
        'section_count': len(sections_list),
        'sections': sections_list,
        'status': status,
        'active_version': active_version,
        'inactive_version': inactive_version,
        'hardware': hardware,
        'cluster_nodes': cluster_nodes,
        'node_role': node_role,
        'processor': processor,
        'memory_perf': memory_perf,
        'services': services,
        'ntp': ntp,
        'backups': backups,
        'dbreplication': dbreplication,
        'core_files': core_files,
    }


def find_files(run_folder):
    files = os.listdir(run_folder)

    summary_files = sorted(
        os.path.join(run_folder, item)
        for item in files
        if item.startswith('Summary_') and item.endswith('.txt')
    )

    discovery_files = sorted(
        os.path.join(run_folder, item)
        for item in files
        if item.startswith('ClusterDiscovery_') and item.endswith('.txt')
    )

    healthcheck_files = sorted(
        os.path.join(run_folder, item)
        for item in files
        if 'HealthCheck_' in item and item.endswith('.txt')
    )

    return summary_files, discovery_files, healthcheck_files


def summarize_versions(nodes):
    active_versions = {}
    inactive_versions = {}
    for node in nodes:
        active = node['active_version'].get('version')
        inactive = node['inactive_version'].get('version')
        active_versions.setdefault(active or 'UNKNOWN', []).append(node['node_ip'])
        inactive_versions.setdefault(inactive or 'UNKNOWN', []).append(node['node_ip'])

    active_status = 'Good' if len(active_versions) == 1 else 'Critical'
    inactive_status = 'Good' if len(inactive_versions) == 1 else 'Warning'

    return {
        'active_status': active_status,
        'inactive_status': inactive_status,
        'active_versions': active_versions,
        'inactive_versions': inactive_versions,
    }


def parse_run_folder(run_folder):
    technology = infer_technology_from_folder(run_folder)
    timestamp_text = infer_timestamp_from_folder(run_folder)
    run_timestamp = parse_timestamp(timestamp_text)

    summary_files, discovery_files, healthcheck_files = find_files(run_folder)

    parsed_healthchecks = [
        parse_healthcheck_file(path, technology, run_timestamp)
        for path in healthcheck_files
    ]

    return {
        'run_folder': run_folder,
        'technology': technology,
        'timestamp': timestamp_text,
        'run_timestamp': run_timestamp,
        'summary_files': summary_files,
        'discovery_files': discovery_files,
        'healthcheck_files': healthcheck_files,
        'parsed_healthchecks': parsed_healthchecks,
        'version_summary': summarize_versions(parsed_healthchecks),
    }


def status_icon(status):
    return {
        'Good': '[GOOD]',
        'Warning': '[WARN]',
        'Critical': '[CRIT]',
        'Informational': '[INFO]',
        'Not Supported': '[N/A]',
        'Parsed': '[INFO]',
        'No Data': '[INFO]',
    }.get(status, '[INFO]')


def render_datetime(value):
    if value is None:
        return 'Not found'
    return value.strftime('%Y-%m-%d %H:%M:%S')


def render_health_report_text(parsed_run):
    lines = []
    nodes = parsed_run['parsed_healthchecks']
    version_summary = parsed_run['version_summary']

    lines.append('=' * 100)
    lines.append('Cisco UC Health Report')
    lines.append('=' * 100)
    lines.append(f"Run Folder: {parsed_run['run_folder']}")
    lines.append(f"Technology: {parsed_run['technology']}")
    lines.append(f"Timestamp: {parsed_run['timestamp']}")
    lines.append(f"Nodes Parsed: {len(nodes)}")
    lines.append('')

    lines.append('Executive Summary')
    lines.append('-' * 100)
    lines.append(f"{status_icon(version_summary['active_status'])} Active Version Consistency: {version_summary['active_status']}")
    lines.append(f"{status_icon(version_summary['inactive_status'])} Inactive Version Consistency: {version_summary['inactive_status']}")
    for node in nodes:
        label = f"{node['node_ip']} ({node['status'].get('hostname') or 'UNKNOWN'})"
        lines.append(f"{status_icon(node['ntp']['status'])} NTP: {node['ntp']['status']} - {label}")
        lines.append(f"{status_icon(node['backups']['status'])} Backup: {node['backups']['status']} - {label}")
        lines.append(f"{status_icon(node['core_files']['status'])} Core Files: {node['core_files']['status']} - {label}")
        lines.append(f"{status_icon(node['services']['status'])} Services: {node['services']['status']} - {label}")
        lines.append(f"{status_icon(node['status']['status'])} System Status: {node['status']['status']} - {label}")
    lines.append('')

    lines.append('Version / Installed Software')
    lines.append('-' * 100)
    for version, node_ips in version_summary['active_versions'].items():
        lines.append(f"Active Version {version}: {', '.join(node_ips)}")
    for version, node_ips in version_summary['inactive_versions'].items():
        lines.append(f"Inactive Version {version}: {', '.join(node_ips)}")
    lines.append('')
    for node in nodes:
        lines.append(f"Node: {node['node_ip']} / {node['status'].get('hostname') or 'UNKNOWN'}")
        lines.append(f"  Active Version: {node['active_version'].get('version') or 'Not found'}")
        if node['active_version'].get('installed_options'):
            lines.append(f"  Active Installed Options: {', '.join(node['active_version']['installed_options'])}")
        else:
            lines.append('  Active Installed Options: None found')
        lines.append(f"  Inactive Version: {node['inactive_version'].get('version') or 'Not found'}")
        if node['inactive_version'].get('installed_options'):
            lines.append(f"  Inactive Installed Options: {', '.join(node['inactive_version']['installed_options'])}")
        else:
            lines.append('  Inactive Installed Options: None found')
    lines.append('')

    lines.append('Node Inventory / System Status')
    lines.append('-' * 100)
    for node in nodes:
        status = node['status']
        hardware = node['hardware']
        lines.append(f"Node: {node['node_ip']} / {status.get('hostname') or 'UNKNOWN'} / {node.get('node_role') or 'UNKNOWN'}")
        lines.append(f"  Product Version: {status.get('product_version') or 'Not found'}")
        lines.append(f"  Unified OS Version: {status.get('unified_os_version') or 'Not found'}")
        lines.append(f"  Uptime Days: {status.get('uptime_days') if status.get('uptime_days') is not None else 'Not found'}")
        lines.append(f"  CPU Used: {status['cpu'].get('used_percent', 'Not found')}%")
        lines.append(f"  Memory Used: {status['memory'].get('used_percent', 'Not found')}%")
        lines.append(f"  Hardware: {hardware.get('hw_platform') or 'Not found'} | CPUs: {hardware.get('processors') or 'Not found'} | Memory: {hardware.get('memory_mb') or 'Not found'}")
        for disk in status['disks']:
            lines.append(f"  {disk['name']}: {disk['used_percent']}% used")
        for note in status['notes']:
            lines.append(f"  Note: {note}")
        lines.append('')

    lines.append('Cluster Topology')
    lines.append('-' * 100)
    if nodes:
        for cluster_node in nodes[0]['cluster_nodes']:
            lines.append(
                f"{cluster_node['ip']:<15} {cluster_node['hostname']:<25} {cluster_node['role']:<12} "
                f"{cluster_node['application']:<12} {cluster_node['db_role']:<8} {cluster_node['auth_status']}"
            )
    lines.append('')

    lines.append('NTP')
    lines.append('-' * 100)
    for node in nodes:
        ntp = node['ntp']
        lines.append(f"{node['node_ip']} / {node['status'].get('hostname') or 'UNKNOWN'}: {ntp['status']}")
        lines.append(f"  Role: {node.get('node_role') or 'UNKNOWN'}")
        lines.append(f"  Synchronized Server: {ntp.get('synchronized_server') or 'Not found'}")
        lines.append(f"  Stratum: {ntp.get('stratum') if ntp.get('stratum') is not None else 'Not found'}")
        for note in ntp['notes']:
            lines.append(f"  Note: {note}")
    lines.append('')

    lines.append('Backups')
    lines.append('-' * 100)
    for node in nodes:
        backups = node['backups']
        lines.append(f"{node['node_ip']} / {node['status'].get('hostname') or 'UNKNOWN'}: {backups['status']}")
        lines.append(f"  Latest Successful Backup: {render_datetime(backups['latest_successful_backup'])}")
        lines.append(f"  Age Days: {backups['latest_successful_backup_age_days'] if backups['latest_successful_backup_age_days'] is not None else 'Not found'}")
        for note in backups['notes']:
            lines.append(f"  Note: {note}")
    lines.append('')

    lines.append('Core Files')
    lines.append('-' * 100)
    for node in nodes:
        core = node['core_files']
        lines.append(f"{node['node_ip']} / {node['status'].get('hostname') or 'UNKNOWN'}: {core['status']}")
        for note in core['notes']:
            lines.append(f"  Note: {note}")
        for core_file in core['core_files'][:10]:
            lines.append(f"  {core_file}")
    lines.append('')

    lines.append('Services')
    lines.append('-' * 100)
    for node in nodes:
        services = node['services']
        lines.append(f"{node['node_ip']} / {node['status'].get('hostname') or 'UNKNOWN'}: {services['status']}")
        lines.append(f"  Services Parsed: {services['service_count']}")
        lines.append(f"  Non-Started Services: {services['not_started_count']}")
        lines.append(f"  Defined Critical Services Parsed: {services['critical_service_count']}")
        lines.append(f"  Defined Critical Services Not Started: {services['critical_not_started_count']}")
        for note in services['notes']:
            lines.append(f"  Note: {note}")
        for svc in services['critical_not_started']:
            lines.append(f"  Critical Not Started: {svc['name']} [{svc['state']}]")
        for svc in services['not_started'][:20]:
            lines.append(f"  Not Started: {svc['name']} [{svc['state']}]")
    lines.append('')

    lines.append('DB Replication')
    lines.append('-' * 100)
    for node in nodes:
        db = node['dbreplication']
        lines.append(f"{node['node_ip']} / {node['status'].get('hostname') or 'UNKNOWN'}: {db['status']}")
        lines.append(f"  Sync Status: {db.get('sync_status') or 'Not found'}")
        for note in db['notes']:
            lines.append(f"  Note: {note}")
    lines.append('')

    return '\n'.join(lines)


def render_health_report_markdown(parsed_run):
    text = render_health_report_text(parsed_run)
    lines = []
    for line in text.splitlines():
        if line == 'Cisco UC Health Report':
            lines.append('# Cisco UC Health Report')
        elif line in [
            'Executive Summary',
            'Version / Installed Software',
            'Node Inventory / System Status',
            'Cluster Topology',
            'NTP',
            'Backups',
            'Core Files',
            'Services',
            'DB Replication',
        ]:
            lines.append(f'## {line}')
        elif set(line) in [{'-'}, {'='}]:
            continue
        else:
            lines.append(line)
    return '\n'.join(lines)


# Backwards-compatible names used by earlier health_report.py scaffold.
def render_inventory_text(parsed_run):
    return render_health_report_text(parsed_run)


def render_inventory_markdown(parsed_run):
    return render_health_report_markdown(parsed_run)
