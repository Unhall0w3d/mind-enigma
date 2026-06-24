#!/usr/bin/env python3

"""
Cisco UC health report builder.

Parser modules return structured facts. This module turns those facts into
terminal/text/Markdown output and should not parse raw Cisco command output.
"""

from datetime import datetime


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

STATUS_ICON = {
    'Good': '[GOOD]',
    'Advisory': '[INFO]',
    'Warning': '[WARN]',
    'Critical': '[CRIT]',
    'Informational': '[INFO]',
    'Not Supported': '[N/A]',
    'Parsed': '[INFO]',
    'No Data': '[INFO]',
}


def status_icon(status):
    return STATUS_ICON.get(status, '[INFO]')


def worst_status(statuses):
    if not statuses:
        return 'Informational'
    return max(statuses, key=lambda value: STATUS_RANK.get(value, 1))


def render_datetime(value):
    if value is None:
        return 'Not found'
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    return str(value)


def node_hostname(node):
    return node.get('status', {}).get('hostname') or 'UNKNOWN'


def node_label(node):
    return f"{node.get('node_ip', 'UNKNOWN')} ({node_hostname(node)})"


def join_node_labels(nodes):
    return ', '.join(node_label(node) for node in nodes)


def active_version_summary(parsed_run):
    version_summary = parsed_run.get('version_summary', {})
    active_versions = version_summary.get('active_versions', {})
    status = version_summary.get('active_status', 'Informational')

    if status == 'Good' and active_versions:
        version = next(iter(active_versions.keys()))
        count = len(next(iter(active_versions.values())))
        return {
            'name': 'Active Version Consistency',
            'status': status,
            'detail': f'All {count} node(s) are running active version {version}.'
        }

    details = []
    for version, ips in active_versions.items():
        details.append(f'{version}: {", ".join(ips)}')

    return {
        'name': 'Active Version Consistency',
        'status': status,
        'detail': 'Active version mismatch detected. ' + '; '.join(details)
    }


def inactive_version_summary(parsed_run):
    version_summary = parsed_run.get('version_summary', {})
    inactive_versions = version_summary.get('inactive_versions', {})
    status = version_summary.get('inactive_status', 'Informational')

    if status == 'Good' and inactive_versions:
        version = next(iter(inactive_versions.keys()))
        count = len(next(iter(inactive_versions.values())))
        return {
            'name': 'Inactive Version Consistency',
            'status': status,
            'detail': f'All {count} node(s) report inactive version {version}.'
        }

    details = []
    for version, ips in inactive_versions.items():
        details.append(f'{version}: {", ".join(ips)}')

    return {
        'name': 'Inactive Version Consistency',
        'status': status,
        'detail': 'Inactive version differences detected. This may be relevant during upgrades or rollback planning. ' + '; '.join(details)
    }


def system_status_summary(nodes):
    status = worst_status([node.get('status', {}).get('status', 'Informational') for node in nodes])
    problem_nodes = [
        node for node in nodes
        if STATUS_RANK.get(node.get('status', {}).get('status', 'Informational'), 1) >= STATUS_RANK.get('Warning')
    ]

    if not problem_nodes:
        return {
            'name': 'System Status',
            'status': 'Good',
            'detail': f'System inventory and resource snapshot parsed successfully for {len(nodes)} node(s).'
        }

    details = []
    for node in problem_nodes:
        notes = node.get('status', {}).get('notes', [])
        if notes:
            details.append(f"{node_label(node)}: " + '; '.join(notes))
        else:
            details.append(node_label(node))

    return {
        'name': 'System Status',
        'status': status,
        'detail': 'System status advisories detected. ' + ' | '.join(details)
    }



def ntp_summary(nodes):
    status = worst_status([node.get('ntp', {}).get('status', 'Informational') for node in nodes])

    if status == 'Good':
        publisher = next((node for node in nodes if node.get('node_role') == 'Publisher'), None)
        if publisher:
            ntp = publisher.get('ntp', {})
            return {
                'name': 'NTP',
                'status': 'Good',
                'detail': f'All parsed nodes are synchronized. Publisher {node_hostname(publisher)} is synchronized to {ntp.get("synchronized_server") or "an NTP source"} at stratum {ntp.get("stratum")}.'
            }
        return {
            'name': 'NTP',
            'status': 'Good',
            'detail': 'All parsed nodes are synchronized to NTP.'
        }

    critical_nodes = [node for node in nodes if node.get('ntp', {}).get('status') == 'Critical']
    advisory_nodes = [node for node in nodes if node.get('ntp', {}).get('status') == 'Advisory']

    if critical_nodes:
        details = []
        for node in critical_nodes:
            ntp = node.get('ntp', {})
            server = ntp.get('synchronized_server') or 'Not found'
            stratum = ntp.get('stratum') if ntp.get('stratum') is not None else 'Not found'
            role = node.get('node_role') or 'Unknown role'
            if role == 'Publisher' and isinstance(stratum, int) and stratum > 4:
                details.append(
                    f'Publisher {node_hostname(node)} ({node.get("node_ip")}) is synchronized to {server} at stratum {stratum}; Publisher NTP should be stratum 4 or better'
                )
            else:
                details.append(
                    f'{role} {node_hostname(node)} ({node.get("node_ip")}) does not appear properly synchronized to NTP'
                )
        return {
            'name': 'NTP',
            'status': status,
            'detail': '; '.join(details) + '.'
        }

    if advisory_nodes:
        details = []
        for node in advisory_nodes:
            ntp = node.get('ntp', {})
            bad_count = len(ntp.get('down_or_bad_sources', []))
            server = ntp.get('synchronized_server') or 'Not found'
            stratum = ntp.get('stratum') if ntp.get('stratum') is not None else 'Not found'
            details.append(
                f'{node_hostname(node)} ({node.get("node_ip")}) is synchronized to {server} at stratum {stratum}, but {bad_count} configured NTP source(s) appear unreachable or unsuitable'
            )
        return {
            'name': 'NTP',
            'status': status,
            'detail': '; '.join(details) + '.'
        }

    return {
        'name': 'NTP',
        'status': status,
        'detail': 'NTP status could not be fully evaluated.'
    }



def disaster_recovery_summary(nodes):
    status = worst_status([node.get('backups', {}).get('status', 'Informational') for node in nodes])
    problem_nodes = [node for node in nodes if node.get('backups', {}).get('status') != 'Good']

    if status == 'Good':
        latest_values = [
            node.get('backups', {}).get('latest_successful_backup')
            for node in nodes
            if node.get('backups', {}).get('latest_successful_backup')
        ]
        latest = max(latest_values) if latest_values else None
        return {
            'name': 'Disaster Recovery',
            'status': 'Good',
            'detail': f'DRS responded successfully and a successful backup was detected within the last 7 days. Latest parsed success: {render_datetime(latest)}.'
        }

    drs_unavailable_nodes = [node for node in problem_nodes if node.get('backups', {}).get('drs_unavailable')]
    if drs_unavailable_nodes:
        return {
            'name': 'Disaster Recovery',
            'status': 'Critical',
            'detail': 'DRS status could not be verified on: ' + join_node_labels(drs_unavailable_nodes) + '. The DRS Master Agent may be down, busy, or not responding.'
        }

    stale_nodes = [
        node for node in problem_nodes
        if node.get('backups', {}).get('latest_successful_backup_age_days') is not None
        and node.get('backups', {}).get('latest_successful_backup_age_days') > 7
    ]
    if stale_nodes:
        return {
            'name': 'Disaster Recovery',
            'status': status,
            'detail': 'Latest successful backup is older than 7 days on: ' + join_node_labels(stale_nodes) + '.'
        }

    return {
        'name': 'Disaster Recovery',
        'status': status,
        'detail': 'No successful backup was found in parsed Disaster Recovery output for: ' + join_node_labels(problem_nodes) + '.'
    }

def core_files_summary(nodes):
    status = worst_status([node.get('core_files', {}).get('status', 'Informational') for node in nodes])
    problem_nodes = [node for node in nodes if node.get('core_files', {}).get('status') == 'Critical']

    if status == 'Good':
        return {
            'name': 'Core Files',
            'status': 'Good',
            'detail': 'No active core files detected.'
        }

    return {
        'name': 'Core Files',
        'status': status,
        'detail': f'Core files detected on: {join_node_labels(problem_nodes)}. Cisco TAC engagement/review is recommended.'
    }


def services_summary(parsed_run):
    nodes = parsed_run.get('parsed_healthchecks', [])
    summary = parsed_run.get('service_summary', {})
    status = summary.get('status') or worst_status([node.get('services', {}).get('status', 'Informational') for node in nodes])
    critical_findings = summary.get('critical_findings', [])
    advisory_findings = summary.get('advisory_findings', [])
    informational_stopped_total = sum(
        node.get('services', {}).get('informational_not_started_count', 0)
        for node in nodes
    )

    if status == 'Good':
        detail = 'All expected critical service policies are satisfied.'
        if informational_stopped_total > 0:
            detail += f' {informational_stopped_total} non-critical stopped/deactivated service(s) are listed as informational detail.'
        return {
            'name': 'Services',
            'status': 'Good',
            'detail': detail
        }

    if status == 'Advisory':
        details = [finding.get('message') for finding in advisory_findings if finding.get('message')]
        return {
            'name': 'Services',
            'status': 'Advisory',
            'detail': '; '.join(details) if details else 'Service advisory findings were detected.'
        }

    details = []
    for finding in critical_findings:
        service = finding.get('service') or 'Unknown service'
        node_ip = finding.get('node_ip') or 'Unknown node'
        hostname = finding.get('hostname') or 'Unknown'
        if node_ip == 'Cluster':
            details.append(f'{service}: {finding.get("message")}')
        else:
            details.append(f'{node_ip} ({hostname}) - {service}: {finding.get("message")}')

    return {
        'name': 'Services',
        'status': status,
        'detail': 'Critical service policy findings detected. ' + '; '.join(details)
    }

def dbreplication_summary(parsed_run):
    summary = parsed_run.get('dbreplication_summary', {})
    status = summary.get('status', 'Informational')
    detail = summary.get('executive_detail') or '; '.join(summary.get('notes', []))

    if not detail:
        if status == 'Good':
            detail = 'Database Replication is synced on all servers.'
        elif status == 'Critical':
            detail = 'Database Replication is suspect. Review Replication Setup details.'
        else:
            detail = 'Database Replication details were informational.'

    return {
        'name': 'DB Replication',
        'status': status,
        'detail': detail
    }

def aggregate_health(parsed_run):
    nodes = parsed_run.get('parsed_healthchecks', [])

    categories = [
        active_version_summary(parsed_run),
        inactive_version_summary(parsed_run),
        system_status_summary(nodes),
        ntp_summary(nodes),
        disaster_recovery_summary(nodes),
        core_files_summary(nodes),
        services_summary(parsed_run),
        dbreplication_summary(parsed_run),
    ]

    overall = worst_status([item['status'] for item in categories])
    return overall, categories


def render_text(parsed_run):
    nodes = parsed_run.get('parsed_healthchecks', [])
    version_summary = parsed_run.get('version_summary', {})
    overall, categories = aggregate_health(parsed_run)

    lines = []
    lines.append('=' * 100)
    lines.append('Cisco UC Health Report')
    lines.append('=' * 100)
    lines.append(f"Run Folder : {parsed_run.get('run_folder')}")
    lines.append(f"Technology : {parsed_run.get('technology')}")
    lines.append(f"Timestamp  : {parsed_run.get('timestamp')}")
    lines.append(f"Nodes      : {len(nodes)}")
    lines.append(f"Overall    : {status_icon(overall)} {overall}")
    lines.append('')

    lines.append('Executive Summary')
    lines.append('-' * 100)
    for item in categories:
        lines.append(f"{status_icon(item['status'])} {item['name']}: {item['status']} - {item['detail']}")
    lines.append('')

    lines.append('Node Status')
    lines.append('-' * 100)
    header = f"{'Node':<17} {'Hostname':<22} {'Role':<13} {'Uptime':<9} {'CPU Used':<11} {'Memory Used':<13} {'Status'}"
    lines.append(header)
    lines.append('-' * len(header))
    for node in nodes:
        status = node.get('status', {})
        lines.append(
            f"{node.get('node_ip', ''):<17}"
            f"{node_hostname(node):<22}"
            f"{node.get('node_role') or 'UNKNOWN':<13}"
            f"{str(status.get('uptime_days')) + 'd' if status.get('uptime_days') is not None else 'Not found':<9}"
            f"{str(status.get('cpu', {}).get('used_percent', 'Not found')) + '%':<11}"
            f"{str(status.get('memory', {}).get('used_percent', 'Not found')) + '%':<13}"
            f"{status.get('status', 'Informational')}"
        )
    lines.append('')

    lines.append('Version / Installed Software')
    lines.append('-' * 100)
    for version, node_ips in version_summary.get('active_versions', {}).items():
        lines.append(f"Active Version {version}: {', '.join(node_ips)}")
    for version, node_ips in version_summary.get('inactive_versions', {}).items():
        lines.append(f"Inactive Version {version}: {', '.join(node_ips)}")
    for note in version_summary.get('option_notes', []):
        lines.append(f"Installed Options Note: {note}")
    lines.append('')
    for node in nodes:
        active = node.get('active_version', {})
        inactive = node.get('inactive_version', {})
        lines.append(f"Node: {node_label(node)}")
        lines.append(f"  Active Version: {active.get('version') or 'Not found'}")
        lines.append(f"  Active Installed Options: {', '.join(active.get('installed_options') or []) or 'None found'}")
        lines.append(f"  Inactive Version: {inactive.get('version') or 'Not found'}")
        lines.append(f"  Inactive Installed Options: {', '.join(inactive.get('installed_options') or []) or 'None found'}")
    lines.append('')

    lines.append('Node Inventory / Resource Snapshot')
    lines.append('-' * 100)
    for node in nodes:
        status = node.get('status', {})
        hardware = node.get('hardware', {})
        lines.append(f"Node: {node_label(node)} / {node.get('node_role') or 'UNKNOWN'}")
        lines.append(f"  Product Version: {status.get('product_version') or 'Not found'}")
        lines.append(f"  Unified OS Version: {status.get('unified_os_version') or 'Not found'}")
        lines.append(f"  Uptime Days: {status.get('uptime_days') if status.get('uptime_days') is not None else 'Not found'}")
        lines.append(f"  CPU Used: {status.get('cpu', {}).get('used_percent', 'Not found')}%")
        lines.append(f"  Memory Used: {status.get('memory', {}).get('used_percent', 'Not found')}%")
        lines.append(
            f"  Hardware: {hardware.get('hw_platform') or 'Not found'} | "
            f"CPUs: {hardware.get('processors') or 'Not found'} | "
            f"Memory: {hardware.get('memory_mb') or 'Not found'}"
        )
        for disk in status.get('disks', []):
            lines.append(f"  {disk['name']}: {disk['used_percent']}% used")
        for note in status.get('notes', []):
            lines.append(f"  Note: {note}")
        lines.append('')

    lines.append('Cluster Topology')
    lines.append('-' * 100)
    topology = parsed_run.get('cluster_topology') or (nodes[0].get('cluster_nodes') if nodes else [])
    if topology:
        header = f"{'IP Address':<16}{'Hostname':<25}{'Role':<13}{'Application':<14}{'DB Role':<9}{'Auth'}"
        lines.append(header)
        lines.append('-' * len(header))
        for cluster_node in topology:
            lines.append(
                f"{cluster_node.get('ip', ''):<16}"
                f"{cluster_node.get('hostname', ''):<25}"
                f"{cluster_node.get('role', ''):<13}"
                f"{cluster_node.get('application', ''):<14}"
                f"{cluster_node.get('db_role', ''):<9}"
                f"{cluster_node.get('auth_status', '')}"
            )
    else:
        lines.append('Cluster topology was not parsed.')
    lines.append('')

    lines.append('NTP')
    lines.append('-' * 100)
    for node in nodes:
        ntp = node.get('ntp', {})
        lines.append(f"{node_label(node)}: {status_icon(ntp.get('status'))} {ntp.get('status', 'Informational')}")
        lines.append(f"  Role: {node.get('node_role') or 'UNKNOWN'}")
        lines.append(f"  Synchronized Server: {ntp.get('synchronized_server') or 'Not found'}")
        lines.append(f"  Stratum: {ntp.get('stratum') if ntp.get('stratum') is not None else 'Not found'}")
        for note in ntp.get('notes', []):
            lines.append(f"  Note: {note}")
    lines.append('')

    lines.append('Disaster Recovery')
    lines.append('-' * 100)
    for node in nodes:
        backups = node.get('backups', {})
        lines.append(f"{node_label(node)}: {status_icon(backups.get('status'))} {backups.get('status', 'Informational')}")
        lines.append(f"  Latest Successful Backup: {render_datetime(backups.get('latest_successful_backup'))}")
        lines.append(f"  Age Days: {backups.get('latest_successful_backup_age_days') if backups.get('latest_successful_backup_age_days') is not None else 'Not found'}")
        for note in backups.get('notes', []):
            lines.append(f"  Note: {note}")
    lines.append('')

    lines.append('Core Files')
    lines.append('-' * 100)
    for node in nodes:
        core = node.get('core_files', {})
        lines.append(f"{node_label(node)}: {status_icon(core.get('status'))} {core.get('status', 'Informational')}")
        for note in core.get('notes', []):
            lines.append(f"  Note: {note}")
        for core_file in core.get('core_files', [])[:10]:
            lines.append(f"  {core_file}")
    lines.append('')

    lines.append('Services')
    lines.append('-' * 100)
    service_summary = parsed_run.get('service_summary', {})
    if service_summary.get('critical_findings'):
        lines.append('Critical Service Policy Findings')
        for finding in service_summary.get('critical_findings', []):
            lines.append(f"  {finding.get('service')}: {finding.get('message')}")
    if service_summary.get('advisory_findings'):
        lines.append('Service Advisories')
        for finding in service_summary.get('advisory_findings', []):
            lines.append(f"  {finding.get('service')}: {finding.get('message')}")
    if service_summary.get('critical_findings') or service_summary.get('advisory_findings'):
        lines.append('')
    for node in nodes:
        services = node.get('services', {})
        lines.append(f"{node_label(node)}: {status_icon(services.get('status'))} {services.get('status', 'Informational')}")
        lines.append(f"  Services Parsed: {services.get('service_count', 0)}")
        lines.append(f"  Expected Critical Services: {services.get('expected_critical_count', 0)}")
        lines.append(f"  Expected Critical Running: {services.get('expected_critical_running_count', 0)}")
        lines.append(f"  Expected Critical Not Running: {services.get('expected_critical_not_running_count', 0)}")
        lines.append(f"  Informational Services Not Started: {services.get('informational_not_started_count', 0)}")
        for note in services.get('notes', []):
            lines.append(f"  Note: {note}")
        for finding in services.get('service_policy_findings', []):
            lines.append(f"  Critical Finding: {finding.get('service')} - {finding.get('message')}")
        for finding in services.get('service_advisories', []):
            lines.append(f"  Advisory: {finding.get('service')} - {finding.get('message')}")
        for svc in services.get('critical_not_started', []):
            detail = f" - {svc.get('activation_detail')}" if svc.get('activation_detail') else ''
            lines.append(f"  Expected Critical Not Running: {svc['name']} [{svc['state']}]{detail}")
        for svc in services.get('informational_not_started', [])[:20]:
            detail = f" - {svc.get('activation_detail')}" if svc.get('activation_detail') else ''
            lines.append(f"  Informational Not Started: {svc['name']} [{svc['state']}]{detail}")
    lines.append('')

    lines.append('DB Replication')
    lines.append('-' * 100)
    summary = parsed_run.get('dbreplication_summary', {})
    lines.append(f"Overall: {status_icon(summary.get('status'))} {summary.get('status', 'Informational')}")
    lines.append(f"Parsed Replication Setup Rows: {summary.get('total_rows', 0)}")
    lines.append(f"Files With Parsed Rows: {summary.get('files_with_rows', 0)}")
    for note in summary.get('notes', []):
        lines.append(f"  Note: {note}")
    for finding in summary.get('bad_findings', []):
        lines.append(
            f"  Finding: {finding.get('source_node_ip')} reports "
            f"{finding.get('reported_server')} ({finding.get('reported_ip')}) as {finding.get('setup')}"
        )
    lines.append('')
    for node in nodes:
        db = node.get('dbreplication', {})
        lines.append(f"{node_label(node)}: {status_icon(db.get('status'))} {db.get('status', 'Informational')}")
        lines.append(f"  Parsed Setup Rows: {len(db.get('replication_setup_rows', []))}")
        for row in db.get('replication_setup_rows', []):
            lines.append(f"  {row.get('server')} ({row.get('ip')}): {row.get('setup')}")
        for note in db.get('notes', []):
            lines.append(f"  Note: {note}")
    lines.append('')

    return '\n'.join(lines)


def render_markdown(parsed_run):
    nodes = parsed_run.get('parsed_healthchecks', [])
    version_summary = parsed_run.get('version_summary', {})
    overall, categories = aggregate_health(parsed_run)

    lines = []
    lines.append('# Cisco UC Health Report')
    lines.append('')
    lines.append(f"- **Run Folder:** `{parsed_run.get('run_folder')}`")
    lines.append(f"- **Technology:** `{parsed_run.get('technology')}`")
    lines.append(f"- **Timestamp:** `{parsed_run.get('timestamp')}`")
    lines.append(f"- **Nodes:** `{len(nodes)}`")
    lines.append(f"- **Overall:** `{overall}`")
    lines.append('')

    lines.append('## Executive Summary')
    lines.append('')
    lines.append('| Category | Status | Detail |')
    lines.append('|---|---:|---|')
    for item in categories:
        lines.append(f"| {item['name']} | {item['status']} | {item['detail']} |")
    lines.append('')

    lines.append('## Node Status')
    lines.append('')
    lines.append('| Node | Hostname | Role | Uptime Days | CPU Used | Memory Used | Status |')
    lines.append('|---|---|---|---:|---:|---:|---|')
    for node in nodes:
        status = node.get('status', {})
        cpu = status.get('cpu', {}).get('used_percent')
        mem = status.get('memory', {}).get('used_percent')
        lines.append(
            f"| {node.get('node_ip')} | {node_hostname(node)} | "
            f"{node.get('node_role') or 'UNKNOWN'} | {status.get('uptime_days') if status.get('uptime_days') is not None else 'Not found'} | "
            f"{cpu if cpu is not None else 'Not found'} | {mem if mem is not None else 'Not found'} | {status.get('status', 'Informational')} |"
        )
    lines.append('')

    lines.append('## Version / Installed Software')
    lines.append('')
    for version, node_ips in version_summary.get('active_versions', {}).items():
        lines.append(f"- **Active Version `{version}`:** {', '.join(node_ips)}")
    for version, node_ips in version_summary.get('inactive_versions', {}).items():
        lines.append(f"- **Inactive Version `{version}`:** {', '.join(node_ips)}")
    for note in version_summary.get('option_notes', []):
        lines.append(f"- **Installed Options Note:** {note}")
    lines.append('')

    lines.append('| Node | Hostname | Active Version | Active Options | Inactive Version | Inactive Options |')
    lines.append('|---|---|---|---|---|---|')
    for node in nodes:
        active = node.get('active_version', {})
        inactive = node.get('inactive_version', {})
        lines.append(
            f"| {node.get('node_ip')} | {node_hostname(node)} | "
            f"{active.get('version') or 'Not found'} | {', '.join(active.get('installed_options') or []) or 'None found'} | "
            f"{inactive.get('version') or 'Not found'} | {', '.join(inactive.get('installed_options') or []) or 'None found'} |"
        )
    lines.append('')

    lines.append('## NTP')
    lines.append('')
    lines.append('| Node | Hostname | Role | Status | Server | Stratum | Notes |')
    lines.append('|---|---|---|---|---|---:|---|')
    for node in nodes:
        ntp = node.get('ntp', {})
        notes = '<br>'.join(ntp.get('notes', []))
        lines.append(
            f"| {node.get('node_ip')} | {node_hostname(node)} | "
            f"{node.get('node_role') or 'UNKNOWN'} | {ntp.get('status', 'Informational')} | "
            f"{ntp.get('synchronized_server') or 'Not found'} | {ntp.get('stratum') if ntp.get('stratum') is not None else 'Not found'} | {notes} |"
        )
    lines.append('')

    lines.append('## Disaster Recovery')
    lines.append('')
    lines.append('| Node | Hostname | Status | Latest Successful Backup | Age Days | Notes |')
    lines.append('|---|---|---|---|---:|---|')
    for node in nodes:
        backups = node.get('backups', {})
        notes = '<br>'.join(backups.get('notes', []))
        lines.append(
            f"| {node.get('node_ip')} | {node_hostname(node)} | "
            f"{backups.get('status', 'Informational')} | {render_datetime(backups.get('latest_successful_backup'))} | "
            f"{backups.get('latest_successful_backup_age_days') if backups.get('latest_successful_backup_age_days') is not None else 'Not found'} | {notes} |"
        )
    lines.append('')

    lines.append('## Core Files')
    lines.append('')
    lines.append('| Node | Hostname | Status | Notes |')
    lines.append('|---|---|---|---|')
    for node in nodes:
        core = node.get('core_files', {})
        lines.append(
            f"| {node.get('node_ip')} | {node_hostname(node)} | "
            f"{core.get('status', 'Informational')} | {'<br>'.join(core.get('notes', []))} |"
        )
    lines.append('')

    lines.append('## Services')
    lines.append('')
    service_summary = parsed_run.get('service_summary', {})
    if service_summary.get('critical_findings'):
        lines.append('### Critical Service Policy Findings')
        lines.append('')
        for finding in service_summary.get('critical_findings', []):
            lines.append(f"- **{finding.get('service')}**: {finding.get('message')}")
        lines.append('')
    if service_summary.get('advisory_findings'):
        lines.append('### Service Advisories')
        lines.append('')
        for finding in service_summary.get('advisory_findings', []):
            lines.append(f"- **{finding.get('service')}**: {finding.get('message')}")
        lines.append('')
    lines.append('| Node | Hostname | Status | Services Parsed | Expected Critical | Critical Not Running | Informational Not Started | Notes |')
    lines.append('|---|---|---|---:|---:|---:|---:|---|')
    for node in nodes:
        services = node.get('services', {})
        notes = '<br>'.join(services.get('notes', []))
        lines.append(
            f"| {node.get('node_ip')} | {node_hostname(node)} | {services.get('status', 'Informational')} | "
            f"{services.get('service_count', 0)} | {services.get('expected_critical_count', 0)} | "
            f"{services.get('expected_critical_not_running_count', 0)} | {services.get('informational_not_started_count', 0)} | {notes} |"
        )
    lines.append('')

    lines.append('## DB Replication')
    lines.append('')
    summary = parsed_run.get('dbreplication_summary', {})
    lines.append(f"- **Overall:** `{summary.get('status', 'Informational')}`")
    lines.append(f"- **Parsed Replication Setup Rows:** `{summary.get('total_rows', 0)}`")
    lines.append(f"- **Files With Parsed Rows:** `{summary.get('files_with_rows', 0)}`")
    for note in summary.get('notes', []):
        lines.append(f"- {note}")
    for finding in summary.get('bad_findings', []):
        lines.append(f"- {finding.get('source_node_ip')} reports {finding.get('reported_server')} ({finding.get('reported_ip')}) as {finding.get('setup')}")
    lines.append('')
    lines.append('| Source Node | Reported Server | Reported IP | Replication Setup |')
    lines.append('|---|---|---|---|')
    for node in nodes:
        for row in node.get('dbreplication', {}).get('replication_setup_rows', []):
            lines.append(f"| {node_label(node)} | {row.get('server')} | {row.get('ip')} | {row.get('setup')} |")
    lines.append('')

    return '\n'.join(lines)
