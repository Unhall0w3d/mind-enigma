#!/usr/bin/env python3

"""
Cisco UC common parser helpers.

This module intentionally starts with neutral extraction only:
- run folder inventory
- section splitting
- per-node file inventory

Health rules will be added after each section's meaning and thresholds are agreed.
"""

import os
import re

SECTION_PATTERN = re.compile(r'^#{5}(.+?)#{5}\s*$', re.MULTILINE)


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


def split_sections(file_contents):
    """
    Split a collected health-check file into command sections using:
        #####command#####

    Returns an ordered dict-like list of tuples:
        [(section_name, section_text), ...]
    """

    matches = list(SECTION_PATTERN.finditer(file_contents))
    sections = []

    for index, match in enumerate(matches):
        section_name = match.group(1).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(file_contents)
        section_text = file_contents[start:end].strip('\n')
        sections.append((section_name, section_text))

    return sections


def parse_healthcheck_file(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as file_read:
        contents = file_read.read()

    sections = split_sections(contents)

    return {
        'path': path,
        'filename': os.path.basename(path),
        'sections': sections,
        'section_names': [section[0] for section in sections],
        'section_count': len(sections),
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


def parse_run_folder(run_folder):
    summary_files, discovery_files, healthcheck_files = find_files(run_folder)

    parsed_healthchecks = [
        parse_healthcheck_file(path)
        for path in healthcheck_files
    ]

    return {
        'run_folder': run_folder,
        'technology': infer_technology_from_folder(run_folder),
        'timestamp': infer_timestamp_from_folder(run_folder),
        'summary_files': summary_files,
        'discovery_files': discovery_files,
        'healthcheck_files': healthcheck_files,
        'parsed_healthchecks': parsed_healthchecks,
    }


def render_inventory_text(parsed_run):
    lines = []
    lines.append('=' * 80)
    lines.append('Health Report Parser - Run Inventory')
    lines.append('=' * 80)
    lines.append(f"Run Folder: {parsed_run['run_folder']}")
    lines.append(f"Technology: {parsed_run['technology']}")
    lines.append(f"Timestamp: {parsed_run['timestamp']}")
    lines.append('')
    lines.append(f"Summary Files: {len(parsed_run['summary_files'])}")
    lines.append(f"Discovery Files: {len(parsed_run['discovery_files'])}")
    lines.append(f"Health Check Files: {len(parsed_run['healthcheck_files'])}")
    lines.append('')

    lines.append('Per-Node File Inventory')
    lines.append('-' * 80)

    for parsed_file in parsed_run['parsed_healthchecks']:
        lines.append(f"File: {parsed_file['filename']}")
        lines.append(f"Sections Found: {parsed_file['section_count']}")
        lines.append('Sections:')

        for section_name in parsed_file['section_names']:
            lines.append(f"  - {section_name}")

        lines.append('')

    return '\n'.join(lines)


def render_inventory_markdown(parsed_run):
    lines = []
    lines.append('# Health Report Parser - Run Inventory')
    lines.append('')
    lines.append(f"**Run Folder:** `{parsed_run['run_folder']}`")
    lines.append(f"**Technology:** `{parsed_run['technology']}`")
    lines.append(f"**Timestamp:** `{parsed_run['timestamp']}`")
    lines.append('')
    lines.append('## Files')
    lines.append('')
    lines.append(f"- Summary files: **{len(parsed_run['summary_files'])}**")
    lines.append(f"- Discovery files: **{len(parsed_run['discovery_files'])}**")
    lines.append(f"- Health check files: **{len(parsed_run['healthcheck_files'])}**")
    lines.append('')
    lines.append('## Per-Node Section Inventory')
    lines.append('')

    for parsed_file in parsed_run['parsed_healthchecks']:
        lines.append(f"### {parsed_file['filename']}")
        lines.append('')
        lines.append(f"Sections found: **{parsed_file['section_count']}**")
        lines.append('')

        for section_name in parsed_file['section_names']:
            lines.append(f"- `{section_name}`")

        lines.append('')

    return '\n'.join(lines)
