"""Tiny JSON-file persistence layer.

Each entity type is stored as a list of dicts in its own file next to
manage.py: reporters.json and issues.json. Files are created on first write.
"""

import json
import os

from django.conf import settings

REPORTERS_FILE = os.path.join(settings.BASE_DIR, 'reporters.json')
ISSUES_FILE = os.path.join(settings.BASE_DIR, 'issues.json')


def _read(path):
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _write(path, records):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2)


def read_reporters():
    """Load all reporter records from reporters.json."""
    return _read(REPORTERS_FILE)


def write_reporters(records):
    """Persist the full reporter list to reporters.json."""
    _write(REPORTERS_FILE, records)


def read_issues():
    """Load all issue records from issues.json."""
    return _read(ISSUES_FILE)


def write_issues(records):
    """Persist the full issue list to issues.json."""
    _write(ISSUES_FILE, records)


def next_id(records):
    """Return the next integer id given a list of existing records."""
    if not records:
        return 1
    return max(int(r['id']) for r in records) + 1
