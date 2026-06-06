#!/usr/bin/env python3

"""
Cisco Collaboration Health Report Runner

Usage:
    python health_report.py <run_folder>

This is the first-stage parser/report runner. It does not perform health scoring yet.
It inventories the collected files and verifies section parsing is working.
"""

import os
import sys

from parsers import uc_common


TECH_SPECIFIC_PARSERS = {
    'CUCM': 'uc_cucm',
    'CUC': 'uc_cuc',
}


def load_tech_specific_parser(technology):
    parser_name = TECH_SPECIFIC_PARSERS.get(technology)

    if parser_name is None:
        return None

    try:
        module = __import__(
            f'parsers.{parser_name}',
            fromlist=['parse_run']
        )
        return module

    except Exception:
        return None


def write_report_files(run_folder, parsed_run):
    timestamp = parsed_run['timestamp']

    text_report = os.path.join(
        run_folder,
        f'HealthReport_{timestamp}.txt'
    )

    markdown_report = os.path.join(
        run_folder,
        f'HealthReport_{timestamp}.md'
    )

    text_output = uc_common.render_inventory_text(parsed_run)
    markdown_output = uc_common.render_inventory_markdown(parsed_run)

    tech_parser = load_tech_specific_parser(parsed_run['technology'])

    if tech_parser is not None:
        tech_result = tech_parser.parse_run(parsed_run)
        text_output += '\n\n' + '=' * 80 + '\nTechnology-Specific Parser\n' + '=' * 80 + '\n'
        text_output += f"Parser: {tech_result.get('technology_specific_parser')}\n"
        text_output += f"Status: {tech_result.get('status')}\n"
        for note in tech_result.get('notes', []):
            text_output += f"- {note}\n"

        markdown_output += '\n## Technology-Specific Parser\n\n'
        markdown_output += f"- Parser: `{tech_result.get('technology_specific_parser')}`\n"
        markdown_output += f"- Status: `{tech_result.get('status')}`\n"
        for note in tech_result.get('notes', []):
            markdown_output += f"- {note}\n"

    with open(text_report, 'w', encoding='utf-8') as file_write:
        file_write.write(text_output)

    with open(markdown_report, 'w', encoding='utf-8') as file_write:
        file_write.write(markdown_output)

    return text_report, markdown_report, text_output


def main():
    if len(sys.argv) < 2:
        run_folder = input('Run folder path: ').strip()
    else:
        run_folder = sys.argv[1]

    if not os.path.isdir(run_folder):
        print(f'Invalid run folder: {run_folder}')
        sys.exit(1)

    parsed_run = uc_common.parse_run_folder(run_folder)
    text_report, markdown_report, text_output = write_report_files(
        run_folder,
        parsed_run
    )

    print()
    print(text_output)
    print()
    print(f'Text report written to: {text_report}')
    print(f'Markdown report written to: {markdown_report}')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        print('Interrupted by user.')
        sys.exit(0)
