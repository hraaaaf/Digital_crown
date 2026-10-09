#!/usr/bin/env python3
"""Offline, read-only Facad D3 snapshot diff. Never authorizes clinical editing."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SCHEMA = 'facad314_d3_snapshot_v1'
SCOPES = {
    'official_examples_tree': 'filetree',
    'disposable_examples_tree': 'filetree',
    'facad_install_tree': 'filetree',
    'facad_appdata_roaming': 'filetree',
    'facad_ilexis_roaming_settings': 'filetree',
    'facad_appdata_local': 'filetree',
    'facad_programdata': 'filetree',
    'facad_documents': 'filetree',
    'facad_registry_hkcu': 'registry',
    'facad_registry_hklm': 'registry',
}
SHA = re.compile(r'^[0-9a-fA-F]{64}$')


class EvidenceError(ValueError):
    pass


def validate(snapshot: object, phase: str) -> dict:
    if not isinstance(snapshot, dict) or set(snapshot) != {'schema', 'phase', 'session_id', 'scopes'}:
        raise EvidenceError('Snapshot schema fields incomplete or unexpected')
    if snapshot['schema'] != SCHEMA or snapshot['phase'] != phase:
        raise EvidenceError('Wrong schema or capture phase')
    if not isinstance(snapshot['session_id'], str) or not snapshot['session_id'].strip():
        raise EvidenceError('Missing capture session ID')
    scopes = snapshot['scopes']
    if not isinstance(scopes, dict) or set(scopes) != set(SCOPES):
        raise EvidenceError('Missing or unexpected storage/registry scope')
    for name, kind in SCOPES.items():
        scope = scopes[name]
        if not isinstance(scope, dict) or set(scope) != {'kind', 'root_fingerprint', 'capture_ok', 'present', 'entries'}:
            raise EvidenceError(f'Incomplete scope: {name}')
        if scope['kind'] != kind or scope['capture_ok'] is not True:
            raise EvidenceError(f'Wrong kind or incomplete capture: {name}')
        if not isinstance(scope['root_fingerprint'], str) or not SHA.fullmatch(scope['root_fingerprint']):
            raise EvidenceError(f'Invalid root identifier: {name}')
        if type(scope['present']) is not bool or not isinstance(scope['entries'], dict):
            raise EvidenceError(f'Invalid presence or entries: {name}')
        if not scope['present'] and scope['entries']:
            raise EvidenceError(f'Absent scope with entries: {name}')
        for entry, value in scope['entries'].items():
            if not isinstance(entry, str) or not entry or not isinstance(value, dict):
                raise EvidenceError(f'Invalid entry: {name}')
            if set(value) != {'sha256', 'size'} or not isinstance(value['sha256'], str) or not SHA.fullmatch(value['sha256']):
                raise EvidenceError(f'Invalid entry hash: {name}')
            if type(value['size']) is not int or value['size'] < 0:
                raise EvidenceError(f'Invalid entry size: {name}')
    return snapshot


def compare(before: object, after: object) -> dict:
    before = validate(before, 'before')
    after = validate(after, 'after')
    if before['session_id'] != after['session_id']:
        raise EvidenceError('Before/after session IDs do not match')
    changes = []
    for name in sorted(SCOPES):
        a, b = before['scopes'][name], after['scopes'][name]
        if a['root_fingerprint'].lower() != b['root_fingerprint'].lower():
            raise EvidenceError(f'Before/after scope root changed: {name}')
        if a['present'] != b['present']:
            changes.append({'scope': name, 'change': 'ROOT_APPEARED_OR_DISAPPEARED', 'entries': 0})
        keys = set(a['entries']) | set(b['entries'])
        for key in sorted(keys):
            old, new = a['entries'].get(key), b['entries'].get(key)
            if old != new:
                category = 'ADDED' if old is None else ('DELETED' if new is None else 'MODIFIED')
                # Never emit even pseudonymous path hashes in the verdict.
                # Small-dictionary file names can be guessed from unsalted hashes.
                changes.append({'scope': name, 'change': category})
    return {
        'd3_isolation_verified': False,
        'clinical_edit_allowed': False,
        'capture_session_id': before['session_id'],
        'monitored_scope_count': len(SCOPES),
        'observed_change_count': len(changes),
        'observed_changes': changes,
        'verdict': 'BLOCKED_OBSERVED_STORAGE_DRIFT' if changes else 'INCONCLUSIVE_NO_OBSERVED_STORAGE_DRIFT',
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', type=Path, required=True)
    parser.add_argument('--after', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        before = json.loads(args.before.read_text(encoding='utf-8'))
        after = json.loads(args.after.read_text(encoding='utf-8'))
        result = compare(before, after)
        status = 1 if result['observed_change_count'] else 3  # INCONCLUSIVE is NOT a green D3 gate
    except (OSError, json.JSONDecodeError, EvidenceError) as exc:
        result = {
            'd3_isolation_verified': False, 'clinical_edit_allowed': False,
            'verdict': 'BLOCKED_INVALID_OR_INCOMPLETE_EVIDENCE',
            'error': str(exc),
        }
        status = 2
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(result['verdict'])
    return status


if __name__ == '__main__':
    raise SystemExit(main())
