"""Private FACAD Robert -> actual versioned Digital Crown geometry helper probe.

Input: six private original exports plus the integrity manifest, OUTSIDE Git.
No patient files, FACAD binaries or point coordinates in the repository.
Geometry HELPER results are not clinical adapter execution or clinical parity.
The Object Values coordinates are already [mm]: never rescale by mm_per_pixel.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
from backend.services import cephalo_ricketts_geometry as rg
from backend.services import cephalo_steiner_geometry as sg

ROOT = Path(__file__).resolve().parents[1]
FACTOR_32 = {'InterIncisal','Convexity','Ii to A-Pog','Is to A-Pog','ILi/A-Pog','ILs/A-Pog','Li-EL','Upper lip len','Facial cone angle'}
FACTOR_13 = {'InterIncisal','Convexity','Ii to A-Pog','ILi/A-Pog','Li-EL'}
BLOCKED = {
    'Convexity': 'NO_FH_REFERENCE_P_OR_FOR_SIGN',
    'Ii to A-Pog': 'NO_FH_REFERENCE_P_OR_FOR_SIGN',
    'Is to A-Pog': 'NO_FH_REFERENCE_P_OR_FOR_SIGN',
    'Li-EL': 'NO_FH_REFERENCE_P_OR_FOR_SIGN',
    'Upper lip len': 'FACAD_ANS_STS_DIFFERS_FROM_DC_ANS_COMMISSURE',
}

def require(condition, reason):
    if not condition:
        raise ValueError(reason)

def parse_values(source, profile):
    require(f"Ricketts ({profile[:-1]} F)" in source and 'Pretreatment tracing (Copie)' in source, 'wrong FACAD profile/trace')
    rows = {}
    body = False
    for line in source.splitlines():
        if line.startswith('Valeur\tOriginal\t'):
            body = True
            continue
        cols = line.split('\t')
        if body and len(cols) == 5:
            label, num, norm, unit, deviation = cols
            require(label not in rows and unit in ('mm', '°') and norm, 'invalid FACAD factor')
            value = float(num.replace(',', '.'))
            require(math.isfinite(value), 'FACAD number not finite')
            rows[label] = (value, unit)
    require(set(rows) == (FACTOR_32 if profile == '32F' else FACTOR_13),
            'source numeric factor roster has changed')
    return rows

def parse_points(source):
    require('Pretreatment tracing (Copie)' in source and
            'Points\t[mm]\t[mm]' in source, 'Object Values is not the metric marker export')
    rows = {}
    body = False
    for line in source.splitlines():
        if line.startswith('Points\t[mm]\t[mm]'):
            body = True
            continue
        cols = line.split('\t')
        if body and len(cols) == 3:
            label, x, y = cols
            require(label not in rows, 'duplicate FACAD point')
            xy = (float(x.replace(',', '.')), float(y.replace(',', '.')))
            require(all(map(math.isfinite, xy)), 'nonfinite FACAD point')
            rows[label] = xy
    require(len(rows) == 30, 'FACAD points must contain exactly 30 landmarks')
    return rows

def raw_helpers(points):
    p = points
    vec = lambda a, b: (p[b][0] - p[a][0], p[b][1] - p[a][1])
    values = {
        'ILi/A-Pog': rg.ricketts_l1_apog_inclination_deg_v1(p['Ii'],p['Iia'],p['A'],p['Pog']),
        'ILs/A-Pog': rg.ricketts_u1_apog_inclination_deg_v1(p['Is'],p['Isa'],p['A'],p['Pog']),
        'InterIncisal': sg._ray_angle_deg(p['Is'],p['Isa'],p['Ii'],p['Iia']),
        'Facial cone angle': rg.ricketts_line_angle_acute_deg_v1(vec('Go','Me'),vec('N','Pog')),
    }
    require(all(v is not None and math.isfinite(v) for v in values.values()),
            'DC geometry helper undefined')
    return values

def comparison(v32, v13, p32, p13):
    require(set(v32) == FACTOR_32 and set(v13) == FACTOR_13, 'unexpected factor set')
    require(p32 == p13, '13F/32F markers disagree')
    require(all(v13[name] == v32[name] for name in v13), 'shared vendor values disagree')
    helpers = raw_helpers(p32)
    rows = []
    for label, (source, unit) in v32.items():
        row = {'factor': label, 'facad_value': source, 'unit': unit, 'clinical_parity': False}
        if label in BLOCKED:
            row.update({'dc_helper': None, 'raw_delta': None, 'gate': BLOCKED[label]})
        else:
            value = helpers[label]
            row.update({'dc_helper': round(value, 6), 'raw_delta': round(value - source, 6),
                        'gate': 'HELPER_ONLY_NO_VERIFIED_RUNTIME_ADAPTER_FRAME_OR_ROUNDING'})
        rows.append(row)
    return {
        'status': 'PRIVATE_DC_GEOMETRY_HELPERS_ONLY',
        'verified_vendor_export_hashes': 6,
        'vendor_factor_count_32f': len(v32),
        'vendor_factor_count_13f': len(v13),
        'vendor_shared_values_equal': len(v13),
        'source_points_each_profile': len(p32),
        'source_coordinates_are_mm_not_pixels': True,
        'dc_geometry_helpers_executed': len(helpers),
        'dc_full_runtime_adapter_executed': False,
        'clinical_numeric_parities_verified': 0,
        'clinical_no_go': True,
        'rows': rows,
    }

def probe(private_dir: Path, integrity: Path):
    folder, manifest_path = private_dir.resolve(strict=True), integrity.resolve(strict=True)
    require(ROOT not in folder.parents and folder != ROOT and
            ROOT not in manifest_path.parents and manifest_path != ROOT,
            'original FACAD inputs must be outside Git checkout')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
    require(manifest.get('application') == 'FACAD 3.14.1.1111' and
            manifest.get('trace_identity') == 'Robert Example / Pretreatment tracing (Copie)' and
            len(manifest['files']) == 6, 'incorrect FACAD source identity')
    sources = {}
    for profile in ('32F', '13F'):
        for kind, suffix in (('analysis-values','Analysis_Values'),
                             ('analysis-properties','Analysis_Properties'),
                             ('object-values','Object_Values')):
            file = (folder / (profile + '_' + suffix + '.txt')).resolve(strict=True)
            require(ROOT not in file.parents, 'FACAD export inside Git checkout')
            content = file.read_bytes()
            require(0 < len(content) <= 100_000, 'export missing/oversized')
            matches = [
                x for x in manifest['files']
                if x.get('profile') == profile
                and kind in x.get('file','').replace('\\','/').lower().split('/')
            ]
            require(len(matches) == 1 and matches[0]['bytes'] == len(content) and
                    matches[0]['sha256'].lower() == hashlib.sha256(content).hexdigest(),
                    'FACAD SHA256/role/size mismatch')
            sources[(profile, kind)] = content.decode('utf-8-sig')
        require(f"Ricketts ({profile[:-1]} F)" in
                sources[(profile,'analysis-properties')] and
                'Pretreatment tracing (Copie)' in sources[(profile,'analysis-properties')],
                'properties profile/trace mismatch')
    return comparison(
        parse_values(sources[('32F','analysis-values')], '32F'),
        parse_values(sources[('13F','analysis-values')], '13F'),
        parse_points(sources[('32F','object-values')]),
        parse_points(sources[('13F','object-values')]),
    )

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--private-dir', type=Path, required=True)
    parser.add_argument('--integrity', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = probe(args.private_dir, args.integrity)
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"FACAD_DC_PRIVATE_HELPERS_FAIL_CLOSED={type(exc).__name__}: {exc}")
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
