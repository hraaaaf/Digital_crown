#!/usr/bin/env python3
"""Read-only Facad D1C editor UIA measurements table extractor.

Only transcribes UIAutomation text. Never calculates patient values, infers units,
accepts clinical norms, or claims a whole definition when virtual rows are missing.
"""
import argparse
import csv
from pathlib import Path
import re

BASE_HEADERS = ['Ceph name', 'Type', 'Arg 1', 'Arg 2', 'Arg 3', 'Arg 4', 'Norm', 'Draw', 'Interpretation']
SCHEMAS = {
    'measurements': ('1317', BASE_HEADERS),
    'lines': ('1317', BASE_HEADERS),
    'markers': ('1316', ['Name', 'Long name', 'Type', 'Parent', 'Bound to', 'Sag', 'Ver', 'Place']),
}


def parse(raw: str, expected_name: str, tab: str = 'measurements'):
    grid_id, expected_headers = SCHEMAS[tab]
    lines = raw.splitlines()
    names = [m.group(1) for ln in lines if (m := re.match(r'^ControlType\.Edit\|(.*?)\|AUTOID=1022\|ENABLED=True\|', ln))]
    if names != [expected_name]:
        raise ValueError('editor name missing, mismatched or ambiguous: '+repr(names))
    starts = [i for i, ln in enumerate(lines) if ln.startswith(f'ControlType.DataGrid||AUTOID={grid_id}|ENABLED=True|OFFSCREEN=False|')]
    if len(starts) != 1:
        raise ValueError(f'expected exactly one enabled {tab} grid {grid_id}')
    i = starts[0] + 1
    if not lines[i].startswith('ControlType.Header|'):
        raise ValueError('missing grid header')
    i += 1
    headers = []
    while i < len(lines) and lines[i].startswith('ControlType.HeaderItem|'):
        headers.append(lines[i].split('|', 2)[1]); i += 1
    if headers != expected_headers:
        raise ValueError('changed grid column contract: '+repr(headers))
    # Markers grid exposes scrollbar controls between header and rows.
    n_scroll = 0
    while i < len(lines) and lines[i].startswith(('ControlType.ScrollBar|', 'ControlType.Button|', 'ControlType.Thumb|')):
        i += 1
        n_scroll += 1
        if n_scroll > 8:
            raise ValueError('unexpected controls between header and rows')
    output = []
    while i < len(lines) and lines[i].startswith('ControlType.DataItem|'):
        rowline = lines[i]
        name = rowline.split('|', 2)[1]
        visible = 'OFFSCREEN=False' in rowline
        i += 1
        cells = []
        for j in range(len(expected_headers)):
            if i >= len(lines) or not lines[i].startswith('ControlType.Text|'):
                raise ValueError(f'row {name} incomplete at col {j}')
            cells.append(lines[i].split('|', 2)[1]); i += 1
        if cells[0] != name or not name:
            raise ValueError('grid DataItem/name discrepancy')
        output.append({'row_ordinal': len(output)+1, 'analysis': expected_name, 'tab': tab,
                       **dict(zip(expected_headers, cells)), 'uia_offscreen': not visible,
                       'evidence_level': 'EDITOR_UIA_TRANSCRIPTION_ONLY'})
    if not output:
        raise ValueError('no grid rows extracted')
    label_col = 'Name' if tab == 'markers' else 'Ceph name'
    if len(output) != len({r[label_col] for r in output}):
        raise ValueError('duplicate measurement names need manual review')
    return output


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True, type=Path)
    ap.add_argument('--analysis', required=True)
    ap.add_argument('--tab', choices=list(SCHEMAS), default='measurements')
    ap.add_argument('--output', required=True, type=Path)
    args = ap.parse_args()
    rows = parse(args.input.read_text(encoding='utf-8-sig'), args.analysis, args.tab)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f'EDITOR_UIA_ROWS_TRANSCRIBED={len(rows)}; ANALYSIS={args.analysis}; TAB={args.tab}; clinical=UNVERIFIED')


if __name__ == '__main__':
    main()
