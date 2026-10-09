#!/usr/bin/env python3
"""Read-only Facad D1C editor UIA measurements table extractor.

Only transcribes UIAutomation text. Never calculates patient values, infers units,
accepts clinical norms, or claims a whole definition when virtual rows are missing.
"""
import argparse
import csv
from pathlib import Path
import re

HEADERS = ['Ceph name', 'Type', 'Arg 1', 'Arg 2', 'Arg 3', 'Arg 4', 'Norm', 'Draw', 'Interpretation']


def parse(raw: str, expected_name: str):
    lines = raw.splitlines()
    names = [m.group(1) for ln in lines if (m := re.match(r'^ControlType\.Edit\|(.*?)\|AUTOID=1022\|ENABLED=True\|', ln))]
    if names != [expected_name]:
        raise ValueError('editor name missing, mismatched or ambiguous: '+repr(names))
    starts = [i for i, ln in enumerate(lines) if ln.startswith('ControlType.DataGrid||AUTOID=1317|ENABLED=True|OFFSCREEN=False|')]
    if len(starts) != 1:
        raise ValueError('expected exactly one enabled measurements grid 1317')
    i = starts[0] + 1
    if not lines[i].startswith('ControlType.Header|'):
        raise ValueError('missing grid header')
    i += 1
    headers = []
    while i < len(lines) and lines[i].startswith('ControlType.HeaderItem|'):
        headers.append(lines[i].split('|', 2)[1]); i += 1
    if headers != HEADERS:
        raise ValueError('changed measurement column contract: '+repr(headers))
    output = []
    while i < len(lines) and lines[i].startswith('ControlType.DataItem|'):
        rowline = lines[i]
        name = rowline.split('|', 2)[1]
        visible = 'OFFSCREEN=False' in rowline
        i += 1
        cells = []
        for j in range(len(HEADERS)):
            if i >= len(lines) or not lines[i].startswith('ControlType.Text|'):
                raise ValueError(f'row {name} incomplete at col {j}')
            cells.append(lines[i].split('|', 2)[1]); i += 1
        if cells[0] != name or not name:
            raise ValueError('grid DataItem/name discrepancy')
        output.append({'row_ordinal': len(output)+1, 'analysis': expected_name,
                       **dict(zip(HEADERS, cells)), 'uia_offscreen': not visible,
                       'evidence_level': 'EDITOR_UIA_TRANSCRIPTION_ONLY'})
    if not output:
        raise ValueError('no measurement rows extracted')
    if len(output) != len({r['Ceph name'] for r in output}):
        raise ValueError('duplicate measurement names need manual review')
    return output


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True, type=Path)
    ap.add_argument('--analysis', required=True)
    ap.add_argument('--output', required=True, type=Path)
    args = ap.parse_args()
    rows = parse(args.input.read_text(encoding='utf-8-sig'), args.analysis)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f'EDITOR_UIA_ROWS_TRANSCRIBED={len(rows)}; ANALYSIS={args.analysis}; clinical=UNVERIFIED')


if __name__ == '__main__':
    main()
