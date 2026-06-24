#!/usr/bin/env python3

"""
Cisco Collaboration Health Report Runner

Usage:
    python health_report.py <run_folder>

This runner parses a completed health-check output folder and produces:
- terminal report output
- HealthReport_<timestamp>.txt
- HealthReport_<timestamp>.md
"""

import os
import sys

from parsers import uc_common
import report_builder


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


def add_technology_specific_results(parsed_run):
    tech_parser = load_tech_specific_parser(parsed_run.get('technology'))

    if tech_parser is None:
        parsed_run['technology_specific'] = None
        return parsed_run

    try:
        parsed_run['technology_specific'] = tech_parser.parse_run(parsed_run)
    except Exception as error:
        parsed_run['technology_specific'] = {
            'technology_specific_parser': tech_parser.__name__,
            'status': 'error',
            'notes': [str(error)]
        }

    return parsed_run


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

    text_output = report_builder.render_text(parsed_run)
    markdown_output = report_builder.render_markdown(parsed_run)

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
    parsed_run = add_technology_specific_results(parsed_run)

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
