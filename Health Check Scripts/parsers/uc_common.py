#!/usr/bin/env python3

"""
Cisco UC common parser.

The parser extracts structured facts from collected Cisco UC health-check files.
It keeps report wording out of the parser as much as possible. Health rules here
are limited to common UC checks that are currently agreed upon.
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

# Service policies are intentionally defined only for services considered
# critical to product operation. Non-critical services are still parsed and
# reported, but they do not affect health status.
#
# Policy meanings:
#   required_all_nodes       - service must be activated and STARTED on every node
#   required_if_activated    - service is critical only if activated/expected on that node
#   required_publisher       - service must be activated and STARTED on the Publisher
#   cuc_singleton            - service must be STARTED on exactly one node in a cluster;
#                              in a single-node deployment it must be STARTED on that node
#   cucm_tftp                - CUCM-specific TFTP deployment policy
SERVICE_POLICIES = {
    'CUCM': [
        {'name': 'A Cisco DB', 'policy': 'required_all_nodes'},
        {'name': 'A Cisco DB Replicator', 'policy': 'required_all_nodes'},
        {'name': 'Cisco Database Layer Monitor', 'policy': 'required_all_nodes'},
        {'name': 'Cisco Tomcat', 'policy': 'required_all_nodes'},
        {'name': 'Cisco CallManager', 'policy': 'required_if_activated'},
        {'name': 'Cisco CTIManager', 'policy': 'required_if_activated'},
        {'name': 'Cisco RIS Data Collector', 'policy': 'required_if_activated'},
        {'name': 'Cisco AXL Web Service', 'policy': 'required_publisher'},
        {'name': 'Cisco Tftp', 'policy': 'cucm_tftp'},
    ],
    'CUC': [
        {'name': 'A Cisco DB', 'policy': 'required_all_nodes'},
        {'name': 'A Cisco DB Replicator', 'policy': 'required_all_nodes'},
        {'name': 'Cisco Tomcat', 'policy': 'required_all_nodes'},
        {'name': 'Connection Conversation Manager', 'policy': 'required_all_nodes'},
        {'name': 'Connection Mixer', 'policy': 'required_all_nodes'},
        {'name': 'Connection Notifier', 'policy': 'cuc_singleton'},
        {'name': 'Connection Message Transfer Agent', 'policy': 'cuc_singleton'},
        {'name': 'Connection Mailbox Sync', 'policy': 'cuc_singleton'},
    ],
    'CER': [
        {'name': 'Cisco Emergency Responder', 'policy': 'required_all_nodes'},
        {'name': 'Cisco Tomcat', 'policy': 'required_all_nodes'},
    ],
    'IMP': [
        {'name': 'Cisco XCP Router', 'policy': 'required_all_nodes'},
        {'name': 'Cisco XCP Config Manager', 'policy': 'required_all_nodes'},
        {'name': 'Cisco Route and Presence Datastores', 'policy': 'required_all_nodes'},
        {'name': 'Cisco Presence Engine', 'policy': 'required_all_nodes'},
        {'name': 'Cisco SIP Proxy', 'policy': 'required_all_nodes'},
        {'name': 'Cisco Sync Agent', 'policy': 'required_all_nodes'},
        {'name': 'Cisco Client Profile Agent', 'policy': 'required_all_nodes'},
        {'name': 'Cisco Tomcat', 'policy': 'required_all_nodes'},
        {'name': 'Cisco Database Layer Monitor', 'policy': 'required_all_nodes'},
    ],
    'CUIC': [
        {'name': 'Cisco Tomcat', 'policy': 'required_all_nodes'},
        {'name': 'Cisco Database Layer Monitor', 'policy': 'required_all_nodes'},
        {'name': 'Cisco Serviceability Reporter', 'policy': 'required_if_activated'},
    ],
    'FIN': [
        {'name': 'Cisco Tomcat', 'policy': 'required_all_nodes'},
        {'name': 'Cisco Database Layer Monitor', 'policy': 'required_all_nodes'},
        {'name': 'Cisco Serviceability Reporter', 'policy': 'required_if_activated'},
    ],
    'PLM': [
        {'name': 'Cisco Tomcat', 'policy': 'required_all_nodes'},
        {'name': 'Cisco Database Layer Monitor', 'policy': 'required_all_nodes'},
        {'name': 'Cisco Serviceability Reporter', 'policy': 'required_if_activated'},
    ],
    'UCCX': [
        {'name': 'Cisco Tomcat', 'policy': 'required_all_nodes'},
        {'name': 'Cisco Database Layer Monitor', 'policy': 'required_all_nodes'},
        {'name': 'Cisco Serviceability Reporter', 'policy': 'required_if_activated'},
    ],
}



STATUS_RANK = {
    'Good': 0,
    'Informational': 1,
    'Advisory': 1,
    'Not Supported': 1,
    'No Data': 1,
    'Parsed': 1,
    'Warning': 2,
    'Critical': 3,
}


def is_valid_ipv4(value):
    if not IPV4_PATTERN.match(value):
        return False
    return all(0 <= int(octet) <= 255 for octet in value.split('.'))


def worst_status(statuses):
    if not statuses:
        return 'Informational'
    return max(statuses, key=lambda value: STATUS_RANK.get(value, 1))


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
    lines = text.splitlines()
    while lines and lines[0].strip() == '':
        lines.pop(0)
    if lines and lines[0].strip().lower() == command.strip().lower():
        lines.pop(0)
    return '\n'.join(lines).strip('\n')


def get_section(sections, command):
    return clean_section_output(command, sections.get(command, ''))


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
        status = 'Advisory'
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
    if not text:
        return {'supported': False, 'status': 'No Data', 'processors': {}}
    if 'No valid command entered' in text:
        return {'supported': False, 'status': 'Not Supported', 'processors': {}}

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
    if not text:
        return {'supported': False, 'status': 'No Data', 'counters': {}}
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
        match = re.match(r'(.+?)\[(STARTED|STOPPED|STARTING|STOPPING|UNKNOWN|NOT STARTED)\]\s*(.*)$', line.strip())
        if match:
            activation_detail = match.group(3).strip()
            services.append({
                'name': match.group(1).strip(),
                'state': match.group(2).strip(),
                'activation_detail': activation_detail,
                'is_activated': 'service not activated' not in activation_detail.lower(),
                'classification': 'Informational Only',
                'policy': None,
                'policy_expected': False,
                'policy_result': 'Not Evaluated',
                'policy_notes': [],
            })

    not_started = [svc for svc in services if svc['state'] != 'STARTED']

    return {
        'status': 'Informational',
        'notes': ['Service policy evaluation is completed at the cluster/run level.'],
        'service_count': len(services),
        'not_started_count': len(not_started),
        'informational_not_started_count': len(not_started),
        'critical_service_count': 0,
        'critical_not_started_count': 0,
        'expected_critical_count': 0,
        'expected_critical_running_count': 0,
        'expected_critical_not_running_count': 0,
        'advisory_count': 0,
        'not_started': not_started,
        'informational_not_started': not_started,
        'critical_services': [],
        'critical_not_started': [],
        'service_policy_findings': [],
        'service_advisories': [],
        'missing_defined_critical_services': [],
        'services': services,
    }


def service_lookup(node):
    services = node.get('services', {}).get('services', [])
    return {svc.get('name', '').lower(): svc for svc in services}


def service_matches(service, policy_name):
    return service is not None and service.get('name', '').lower() == policy_name.lower()


def is_service_running(service):
    return service is not None and service.get('state') == 'STARTED'


def is_service_expected(service):
    return service is not None and service.get('is_activated')


def mark_service(service, classification, policy, expected, result, note=None):
    if service is None:
        return
    service['classification'] = classification
    service['policy'] = policy
    service['policy_expected'] = expected
    service['policy_result'] = result
    if note:
        service.setdefault('policy_notes', []).append(note)


def add_service_finding(node, policy_name, policy, status, message, service=None):
    svc = service or service_lookup(node).get(policy_name.lower())
    return {
        'node_ip': node.get('node_ip'),
        'hostname': node.get('status', {}).get('hostname'),
        'node_role': node.get('node_role'),
        'service': policy_name,
        'policy': policy,
        'status': status,
        'state': svc.get('state') if svc else 'Missing',
        'activation_detail': svc.get('activation_detail') if svc else 'Service not found in output',
        'message': message,
    }


def evaluate_service_policies(nodes, technology):
    policies = SERVICE_POLICIES.get(technology, [])
    policy_findings = []
    advisory_findings = []
    node_count = len(nodes)
    has_subscribers = any(node.get('node_role') == 'Subscriber' for node in nodes)

    # Reset service policy fields in case this parser is reused.
    for node in nodes:
        services = node.get('services', {})
        for svc in services.get('services', []):
            svc['classification'] = 'Informational Only'
            svc['policy'] = None
            svc['policy_expected'] = False
            svc['policy_result'] = 'Not Evaluated'
            svc['policy_notes'] = []

    for policy in policies:
        name = policy['name']
        policy_type = policy['policy']

        if policy_type == 'required_all_nodes':
            for node in nodes:
                svc = service_lookup(node).get(name.lower())
                if svc is None:
                    policy_findings.append(add_service_finding(
                        node, name, policy_type, 'Critical',
                        f'{name} was not found in service output.'
                    ))
                    continue
                mark_service(svc, 'Critical', policy_type, True, 'Expected')
                if not svc.get('is_activated') or svc.get('state') != 'STARTED':
                    policy_findings.append(add_service_finding(
                        node, name, policy_type, 'Critical',
                        f'{name} is expected on this node but is {svc.get("state")} / {svc.get("activation_detail") or "activated"}.',
                        svc
                    ))
                else:
                    mark_service(svc, 'Critical', policy_type, True, 'Good')

        elif policy_type == 'required_if_activated':
            for node in nodes:
                svc = service_lookup(node).get(name.lower())
                if svc is None:
                    continue
                if svc.get('is_activated'):
                    mark_service(svc, 'Critical', policy_type, True, 'Expected')
                    if svc.get('state') != 'STARTED':
                        policy_findings.append(add_service_finding(
                            node, name, policy_type, 'Critical',
                            f'{name} is activated but is not STARTED.',
                            svc
                        ))
                    else:
                        mark_service(svc, 'Critical', policy_type, True, 'Good')
                else:
                    mark_service(svc, 'Informational Only', policy_type, False, 'Not Activated')

        elif policy_type == 'required_publisher':
            for node in nodes:
                svc = service_lookup(node).get(name.lower())
                if node.get('node_role') == 'Publisher':
                    if svc is None:
                        policy_findings.append(add_service_finding(
                            node, name, policy_type, 'Critical',
                            f'{name} was not found in Publisher service output.'
                        ))
                        continue
                    mark_service(svc, 'Critical', policy_type, True, 'Expected')
                    if not svc.get('is_activated') or svc.get('state') != 'STARTED':
                        policy_findings.append(add_service_finding(
                            node, name, policy_type, 'Critical',
                            f'{name} is expected on the Publisher but is {svc.get("state")} / {svc.get("activation_detail") or "activated"}.',
                            svc
                        ))
                    else:
                        mark_service(svc, 'Critical', policy_type, True, 'Good')
                elif svc is not None:
                    mark_service(svc, 'Informational Only', policy_type, False, 'Not Expected On This Role')

        elif policy_type == 'cuc_singleton':
            running_nodes = []
            present_nodes = []
            for node in nodes:
                svc = service_lookup(node).get(name.lower())
                if svc is None:
                    continue
                present_nodes.append(node)
                mark_service(svc, 'Critical', policy_type, True, 'Singleton Expected')
                if svc.get('state') == 'STARTED':
                    running_nodes.append(node)

            if node_count == 1:
                node = nodes[0]
                svc = service_lookup(node).get(name.lower())
                if svc is None or not svc.get('is_activated') or svc.get('state') != 'STARTED':
                    policy_findings.append(add_service_finding(
                        node, name, policy_type, 'Critical',
                        f'{name} is a singleton service and must be running in a single-node deployment.',
                        svc
                    ))
                elif svc:
                    mark_service(svc, 'Critical', policy_type, True, 'Good')
            else:
                if len(running_nodes) == 1:
                    for node in nodes:
                        svc = service_lookup(node).get(name.lower())
                        if svc:
                            if node in running_nodes:
                                mark_service(svc, 'Critical', policy_type, True, 'Good')
                            else:
                                mark_service(svc, 'Informational Only', policy_type, False, 'Singleton Not Active On This Node')
                elif len(running_nodes) == 0:
                    policy_findings.append({
                        'node_ip': 'Cluster',
                        'hostname': 'Cluster',
                        'node_role': 'Cluster',
                        'service': name,
                        'policy': policy_type,
                        'status': 'Critical',
                        'state': 'Not STARTED on any node',
                        'activation_detail': '',
                        'message': f'{name} is a singleton service but is not STARTED on any node.',
                    })
                else:
                    policy_findings.append({
                        'node_ip': 'Cluster',
                        'hostname': 'Cluster',
                        'node_role': 'Cluster',
                        'service': name,
                        'policy': policy_type,
                        'status': 'Critical',
                        'state': 'STARTED on multiple nodes',
                        'activation_detail': '',
                        'message': f'{name} is a singleton service but is STARTED on multiple nodes: ' + ', '.join(n.get('node_ip') for n in running_nodes),
                    })

        elif policy_type == 'cucm_tftp':
            publisher_nodes = [node for node in nodes if node.get('node_role') == 'Publisher']
            subscriber_nodes = [node for node in nodes if node.get('node_role') == 'Subscriber']

            if node_count == 1:
                node = nodes[0]
                svc = service_lookup(node).get(name.lower())
                if svc is None or not svc.get('is_activated') or svc.get('state') != 'STARTED':
                    policy_findings.append(add_service_finding(
                        node, name, policy_type, 'Critical',
                        'Cisco TFTP must be running in a single-node CUCM deployment.',
                        svc
                    ))
                elif svc:
                    mark_service(svc, 'Critical', policy_type, True, 'Good')
                continue

            subscriber_running = []
            for node in subscriber_nodes:
                svc = service_lookup(node).get(name.lower())
                if svc and svc.get('state') == 'STARTED':
                    subscriber_running.append(node)
                    mark_service(svc, 'Critical', policy_type, True, 'Good')
                elif svc:
                    mark_service(svc, 'Informational Only', policy_type, False, 'Not Running On This Subscriber')

            if not subscriber_running and has_subscribers:
                policy_findings.append({
                    'node_ip': 'Cluster',
                    'hostname': 'Cluster',
                    'node_role': 'Cluster',
                    'service': name,
                    'policy': policy_type,
                    'status': 'Critical',
                    'state': 'No Subscriber running TFTP',
                    'activation_detail': '',
                    'message': 'Cisco TFTP is not STARTED on any Subscriber node.',
                })

            for node in publisher_nodes:
                svc = service_lookup(node).get(name.lower())
                if svc and svc.get('state') == 'STARTED':
                    mark_service(svc, 'Informational Only', policy_type, False, 'Publisher TFTP Advisory')
                    advisory_findings.append(add_service_finding(
                        node, name, policy_type, 'Advisory',
                        'Cisco TFTP is STARTED on the Publisher. This is informational/advisory; Subscriber or dedicated TFTP placement is generally preferred where practical.',
                        svc
                    ))
                elif svc:
                    mark_service(svc, 'Informational Only', policy_type, False, 'Not Running On Publisher')

    # Final per-node rollup.
    for node in nodes:
        services = node.get('services', {})
        svc_list = services.get('services', [])
        node_findings = [f for f in policy_findings if f.get('node_ip') == node.get('node_ip')]
        cluster_findings = [f for f in policy_findings if f.get('node_ip') == 'Cluster']
        node_advisories = [f for f in advisory_findings if f.get('node_ip') == node.get('node_ip')]
        expected_critical = [svc for svc in svc_list if svc.get('classification') == 'Critical' and svc.get('policy_expected')]
        expected_not_running = [svc for svc in expected_critical if svc.get('state') != 'STARTED']
        informational_not_started = [svc for svc in svc_list if svc.get('state') != 'STARTED' and svc.get('classification') != 'Critical']

        status = 'Good'
        notes = []
        if node_findings or cluster_findings:
            status = 'Critical'
            notes.append('One or more critical service policies are not satisfied.')
        elif node_advisories:
            status = 'Advisory'
            notes.append('One or more service advisories were detected.')
        else:
            notes.append('All expected critical service policies are satisfied.')

        if informational_not_started:
            notes.append('Stopped/deactivated non-critical services are listed as informational detail.')

        services.update({
            'status': status,
            'notes': notes,
            'informational_not_started': informational_not_started,
            'informational_not_started_count': len(informational_not_started),
            'critical_services': expected_critical,
            'critical_service_count': len(expected_critical),
            'critical_not_started': expected_not_running,
            'critical_not_started_count': len(expected_not_running),
            'expected_critical_count': len(expected_critical),
            'expected_critical_running_count': len([svc for svc in expected_critical if svc.get('state') == 'STARTED']),
            'expected_critical_not_running_count': len(expected_not_running),
            'service_policy_findings': node_findings + cluster_findings,
            'service_advisories': node_advisories,
            'advisory_count': len(node_advisories),
        })

    overall_status = 'Good'
    if policy_findings:
        overall_status = 'Critical'
    elif advisory_findings:
        overall_status = 'Advisory'

    return {
        'status': overall_status,
        'critical_findings': policy_findings,
        'advisory_findings': advisory_findings,
        'critical_count': len(policy_findings),
        'advisory_count': len(advisory_findings),
    }

def parse_ntp(text, node_role):
    lower_text = text.lower()

    running = (('chronyd' in lower_text) or ('ntpd' in lower_text)) and 'is running' in lower_text

    server_lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith('^'):
            server_lines.append(stripped)

    # Cisco VOS output has been observed with both spellings:
    #   "synchronised" and "synchronized"
    stratum_match = re.search(
        r'synchroni[sz]ed to NTP server \(([^)]+)\) at stratum (\d+)',
        text,
        re.IGNORECASE
    )

    server = stratum_match.group(1) if stratum_match else None
    stratum = int(stratum_match.group(2)) if stratum_match else None
    synchronized = stratum_match is not None

    down_or_bad = []
    for line in server_lines:
        if line.startswith('^?') or line.startswith('^x') or line.startswith('^-'):
            down_or_bad.append(line)

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(('remote', '====', 'Current time')):
            continue
        # Include peer rows that do not use ntpq selection markers but clearly show INIT/refid or reach 0.
        if re.search(r'\.INIT\.', stripped) or re.search(r'\s16\s+\w\s+', stripped):
            if stripped not in down_or_bad:
                down_or_bad.append(stripped)

    status = 'Good'
    notes = []

    if not running or not synchronized or stratum is None:
        status = 'Critical'
        notes.append('NTP does not appear synchronized.')
    elif node_role == 'Publisher' and stratum > 4:
        status = 'Critical'
        notes.append('Publisher NTP stratum is higher than 4.')
    elif down_or_bad:
        status = 'Advisory'
        notes.append('One or more configured NTP sources appear unreachable or unsuitable, but this node is synchronized.')

    return {
        'status': status,
        'notes': notes,
        'chronyd_running': running,
        'synchronized': synchronized,
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
    combined_text = f"{history_text}\n{status_text}"
    lower_text = combined_text.lower()

    drs_unavailable_indicators = [
        'network request timed out',
        'master agent may be processing an operation or it is down',
        'master agent may be down',
        'error occurred:master agent',
        'drfclimsg: error occurred',
    ]

    drs_unavailable = any(
        indicator in lower_text
        for indicator in drs_unavailable_indicators
    )

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

    if drs_unavailable:
        status = 'Critical'
        notes.append(
            'Disaster Recovery Framework status could not be verified. '
            'DRS returned a timeout or reported that the Master Agent may be down or processing an operation.'
        )
    elif latest is None:
        status = 'Critical'
        notes.append('No successful backup was found in parsed Disaster Recovery output.')
    elif age_days is not None and age_days > 7:
        status = 'Warning'
        notes.append('No successful backup was found within the last 7 days.')
    else:
        notes.append('Successful backup detected within the last 7 days.')

    return {
        'status': status,
        'notes': notes,
        'latest_successful_backup': latest,
        'latest_successful_backup_age_days': age_days,
        'successful_backup_count': len(all_successes),
        'drs_unavailable': drs_unavailable,
        'history_unavailable': 'No backup history available' in history_text or 'No history data is available' in history_text,
        'status_unavailable': 'No backup status available' in status_text or 'Master Agent' in status_text,
        'raw_error_detected': drs_unavailable,
    }


def parse_dbreplication(text):
    """Parse utils dbreplication runtimestate output.

    The health signal we currently care about is the Replication Setup table.
    Each collected node should report every cluster member as:
        (2) Setup Completed

    Anything else is treated as suspect by the aggregate DB replication summary.
    """
    if 'No valid command entered' in text:
        return {
            'status': 'Not Supported',
            'notes': ['DB replication runtime state command is not supported on this platform.'],
            'sync_status': None,
            'replication_setup_rows': [],
            'bad_replication_setup_rows': [],
            'parse_error': False,
            'command_error': False,
        }

    command_error_terms = [
        'Network request timed out',
        'Command failed',
        'Executed command unsuccessfully',
        'Error',
        'Exception',
    ]

    command_error = any(term.lower() in text.lower() for term in command_error_terms)

    sync_status = None
    match = re.search(r'Sync Status:\s*(.+)', text)
    if match:
        sync_status = match.group(1).strip()

    replication_setup_rows = []
    bad_rows = []

    # Common CUCM/VOS format observed:
    # SERVERNAME  10.x.x.x  0.017  Y/Y/Y  0  (g_2)  (2) Setup Completed
    row_pattern = re.compile(
        r'^(?P<server>\S+)\s+'
        r'(?P<ip>\d{1,3}(?:\.\d{1,3}){3})\s+'
        r'(?P<ping>\S+)\s+'
        r'(?P<dbmon>\S+)\s+'
        r'(?P<queue>\S+)\s+'
        r'(?P<group>\(g_\d+\))\s+'
        r'(?P<setup>\(\d+\)\s+.+?)\s*$'
    )

    for line in text.splitlines():
        stripped = line.strip()
        match = row_pattern.match(stripped)
        if not match:
            continue

        row = match.groupdict()
        row['raw'] = stripped
        row['setup_completed'] = row['setup'].strip() == '(2) Setup Completed'
        replication_setup_rows.append(row)

        if not row['setup_completed']:
            bad_rows.append(row)

    status = 'Good'
    notes = []
    parse_error = False

    if bad_rows:
        status = 'Critical'
        notes.append('One or more Replication Setup rows are not (2) Setup Completed.')
    elif replication_setup_rows:
        notes.append('All parsed Replication Setup rows report (2) Setup Completed.')
    elif command_error:
        status = 'Critical'
        notes.append('DB replication command output contains an error and could not be validated.')
        parse_error = True
    elif sync_status:
        if 'All Tables are in sync' in sync_status:
            # Useful, but less complete than Replication Setup table validation.
            status = 'Informational'
            notes.append('Sync Status reports all tables are in sync; Replication Setup rows were not parsed.')
        else:
            status = 'Critical'
            notes.append(sync_status)
    else:
        status = 'Informational'
        notes.append('DB replication runtime state details were not parsed from this output.')
        parse_error = True

    return {
        'status': status,
        'notes': notes,
        'sync_status': sync_status,
        'replication_setup_rows': replication_setup_rows,
        'bad_replication_setup_rows': bad_rows,
        'parse_error': parse_error,
        'command_error': command_error,
    }


def summarize_dbreplication(nodes):
    """Summarize DB replication across all collected node outputs."""
    bad_findings = []
    parse_warnings = []
    total_rows = 0
    files_with_rows = 0
    reporting_nodes = []

    for node in nodes:
        node_ip = node.get('node_ip')
        hostname = node.get('status', {}).get('hostname')
        label = hostname or node_ip or 'Unknown'
        db = node.get('dbreplication', {})
        rows = db.get('replication_setup_rows', [])

        if rows:
            files_with_rows += 1
            reporting_nodes.append({
                'node_ip': node_ip,
                'hostname': hostname,
                'row_count': len(rows),
            })

        total_rows += len(rows)

        if db.get('parse_error') or db.get('command_error') or not rows:
            parse_warnings.append({
                'source_node_ip': node_ip,
                'source_hostname': hostname,
                'notes': db.get('notes', []),
                'status': db.get('status', 'Informational'),
            })

        for row in db.get('bad_replication_setup_rows', []):
            bad_findings.append({
                'source_node_ip': node_ip,
                'source_hostname': hostname,
                'source_label': label,
                'reported_server': row.get('server'),
                'reported_ip': row.get('ip'),
                'setup': row.get('setup'),
                'raw': row.get('raw'),
            })

    expected_files = len(nodes)
    nodes_with_bad_findings = sorted({finding.get('source_node_ip') for finding in bad_findings if finding.get('source_node_ip')})
    nodes_with_parse_warnings = sorted({warning.get('source_node_ip') for warning in parse_warnings if warning.get('source_node_ip')})

    status = 'Good'
    notes = []
    executive_detail = ''

    all_not_supported = (
        expected_files > 0
        and total_rows == 0
        and all(
            node.get('dbreplication', {}).get('status') == 'Not Supported'
            for node in nodes
        )
    )

    if all_not_supported:
        status = 'Not Supported'
        executive_detail = 'Database Replication runtime state is not supported on this platform.'
        notes.append(executive_detail)
    elif bad_findings:
        status = 'Critical'
        if len(nodes_with_bad_findings) == expected_files and expected_files > 0:
            executive_detail = 'Database Replication is suspect on all nodes.'
        else:
            executive_detail = 'Database Replication is suspect on: ' + ', '.join(nodes_with_bad_findings) + '.'
        notes.append(executive_detail)
    elif files_with_rows == expected_files and total_rows > 0:
        executive_detail = 'Database Replication is synced on all servers.'
        notes.append(executive_detail)
    elif total_rows > 0:
        status = 'Warning'
        executive_detail = (
            f'Database Replication Setup rows were parsed from {files_with_rows} of {expected_files} node output file(s). '
            'Review nodes without parsed Replication Setup rows.'
        )
        notes.append(executive_detail)
    else:
        status = 'Warning'
        executive_detail = 'Database Replication Setup rows were not parsed from any node output file.'
        notes.append(executive_detail)

    if parse_warnings:
        notes.append(
            'One or more node outputs did not provide complete Replication Setup detail: '
            + ', '.join(nodes_with_parse_warnings)
            + '.'
        )

    return {
        'status': status,
        'notes': notes,
        'executive_detail': executive_detail,
        'total_rows': total_rows,
        'files_with_rows': files_with_rows,
        'expected_files': expected_files,
        'reporting_nodes': reporting_nodes,
        'bad_findings': bad_findings,
        'parse_warnings': parse_warnings,
        'nodes_with_bad_findings': nodes_with_bad_findings,
        'nodes_with_parse_warnings': nodes_with_parse_warnings,
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
    active_options = {}
    inactive_options = {}

    for node in nodes:
        active = node['active_version'].get('version')
        inactive = node['inactive_version'].get('version')
        active_versions.setdefault(active or 'UNKNOWN', []).append(node['node_ip'])
        inactive_versions.setdefault(inactive or 'UNKNOWN', []).append(node['node_ip'])
        active_options[node['node_ip']] = sorted(node['active_version'].get('installed_options') or [])
        inactive_options[node['node_ip']] = sorted(node['inactive_version'].get('installed_options') or [])

    active_status = 'Good' if len(active_versions) == 1 else 'Critical'
    inactive_status = 'Good' if len(inactive_versions) == 1 else 'Warning'

    def option_sets_by_node(options_map):
        normalized = {}
        for node_ip, options in options_map.items():
            normalized[node_ip] = tuple(options)
        return normalized

    def options_consistent(options_map):
        values = list(option_sets_by_node(options_map).values())
        if not values:
            return True
        return len(set(values)) == 1

    active_options_consistent = options_consistent(active_options)
    inactive_options_consistent = options_consistent(inactive_options)

    option_notes = []
    if not active_options_consistent:
        option_notes.append('Active installed software options differ between nodes.')
    if not inactive_options_consistent:
        option_notes.append('Inactive installed software options differ between nodes.')

    return {
        'active_status': active_status,
        'inactive_status': inactive_status,
        'active_versions': active_versions,
        'inactive_versions': inactive_versions,
        'active_options': active_options,
        'inactive_options': inactive_options,
        'active_options_consistent': active_options_consistent,
        'inactive_options_consistent': inactive_options_consistent,
        'option_notes': option_notes,
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

    cluster_topology = []
    for node in parsed_healthchecks:
        if node.get('cluster_nodes'):
            cluster_topology = node['cluster_nodes']
            break

    version_summary = summarize_versions(parsed_healthchecks)
    dbreplication_summary = summarize_dbreplication(parsed_healthchecks)
    service_summary = evaluate_service_policies(parsed_healthchecks, technology)

    return {
        'run_folder': run_folder,
        'technology': technology,
        'timestamp': timestamp_text,
        'run_timestamp': run_timestamp,
        'summary_files': summary_files,
        'discovery_files': discovery_files,
        'healthcheck_files': healthcheck_files,
        'parsed_healthchecks': parsed_healthchecks,
        'cluster_topology': cluster_topology,
        'version_summary': version_summary,
        'dbreplication_summary': dbreplication_summary,
        'service_summary': service_summary,
    }
