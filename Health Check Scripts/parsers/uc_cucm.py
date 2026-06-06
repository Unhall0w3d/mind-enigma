#!/usr/bin/env python3

"""
Cisco CUCM-specific parser placeholder.

This file is intentionally light right now. CUCM-specific parsing will be added
after the common parser framework is validated and after each report category is
agreed section-by-section.
"""


def parse_run(parsed_run):
    return {
        'technology_specific_parser': 'uc_cucm',
        'status': 'placeholder',
        'notes': [
            'CUCM-specific parsing not implemented yet.',
            'Expected future target: show risdb query misc ...',
        ]
    }
