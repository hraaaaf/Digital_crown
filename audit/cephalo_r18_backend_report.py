#!/usr/bin/env python3
"""R18 audit-only backend extractor for frontend/backend cephalometric concordance."""
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'audit' / 'cephalo_r18_concordance_fixtures.json'
OUT = ROOT / 'audit' / 'out' / 'backend.json'


def load_module(name: str, relative_path: str):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Cannot load {path}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


steiner = load_module('audit_steiner_geometry', 'backend/services/cephalo_steiner_geometry.py')
tweed = load_module('audit_tweed_geometry', 'backend/services/cephalo_tweed_merrifield_geometry.py')
craniom = load_module('audit_craniom_angular', 'backend/services/cephalo_craniom_angular.py')
ricketts = load_module('audit_ricketts_geometry', 'backend/services/cephalo_ricketts_geometry.py')


def js_round(value: float, decimals: int = 0) -> float:
    factor = 10 ** decimals
    return math.floor(value * factor + 0.5) / factor


def have(points: dict[str, tuple[float, float]], *keys: str) -> bool:
    return all(key in points for key in keys)


def safe(call, points, keys, transform=lambda x: x):
    if not have(points, *keys):
        return None
    value = call(*[points[k] for k in keys])
    return None if value is None else transform(value)


def extract(case: dict) -> dict[str, float | None]:
    p = {lm['id']: (float(lm['x']), float(lm['y'])) for lm in case['landmarks']}
    ratio = case['mmPerPixel']
    out: dict[str, float | None] = {}
    out['sna'] = safe(steiner.steiner_sna_deg_v1, p, ('S','N','A'), lambda v: js_round(v,1))
    out['snb'] = safe(steiner.steiner_snb_deg_v1, p, ('S','N','B'), lambda v: js_round(v,1))
    out['anb'] = safe(steiner.steiner_anb_deg_v1, p, ('S','N','A','B'), lambda v: js_round(v,1))
    out['i_na_angle'] = safe(steiner.steiner_u1_na_deg_v1, p, ('U1_apex','U1_incisal','N','A'), lambda v: js_round(v,0))
    out['i_nb_angle'] = safe(steiner.steiner_l1_nb_deg_v1, p, ('L1_apex','L1_incisal','N','B'), lambda v: js_round(v,0))
    # Source-strict Steiner linear distances require a crown landmark that the
    # current contract does not expose. Both runtimes therefore fail closed.
    out['i_na_mm'] = None
    out['i_nb_mm'] = None
    out['fma'] = safe(tweed.tweed_fma_deg_v1, p, ('Go','Me','Po','Or'), lambda v: js_round(v,0))
    out['impa'] = safe(tweed.tweed_impa_deg_v1, p, ('L1_apex','L1_incisal','Go','Me'), lambda v: js_round(v,1))
    out['fmia'] = safe(tweed.tweed_fmia_deg_v1, p, ('L1_apex','L1_incisal','Po','Or'), lambda v: js_round(v,0))
    out['u1_frankfort'] = safe(craniom.craniom_u1_frankfort_deg_v1, p, ('U1_apex','U1_incisal','Po','Or'), lambda v: js_round(v,1))
    out['l1_downs_craniom'] = safe(craniom.craniom_l1_downs_deg_v1, p, ('L1_apex','L1_incisal','Go','Me'), lambda v: js_round(v,1))
    out['interincisal'] = safe(craniom.craniom_interincisal_deg_v1, p, ('U1_apex','U1_incisal','L1_apex','L1_incisal'), lambda v: js_round(v,0))
    if ratio is not None and have(p, 'Po','Or','U1_incisal','L1_incisal'):
        dx = p['Or'][0] - p['Po'][0]
        dy = p['Or'][1] - p['Po'][1]
        length = math.hypot(dx, dy)
        if length > 1e-12:
            ux, uy = dx / length, dy / length
            px, py = -uy, ux
            if py < 0:
                px, py = -px, -py
            vx = p['U1_incisal'][0] - p['L1_incisal'][0]
            vy = p['U1_incisal'][1] - p['L1_incisal'][1]
            out['overjet'] = js_round((vx * ux + vy * uy) * float(ratio), 1)
            out['overbite'] = js_round((vx * px + vy * py) * float(ratio), 1)
        else:
            out['overjet'] = None
            out['overbite'] = None
    else:
        out['overjet'] = None
        out['overbite'] = None
    for out_key, lip_key in (('eline_ls','Ls_soft'),('eline_li','Li_soft')):
        if ratio is not None and have(p, lip_key,'Prn','Pog_soft','Po','Or'):
            value = ricketts.ricketts_e_line_perpendicular_signed_distance_px_v2(
                p[lip_key], p['Prn'], p['Pog_soft'], p['Po'], p['Or']
            )
            out[out_key] = None if value is None else js_round(value * float(ratio),1)
        else:
            out[out_key] = None
    return out


def main() -> None:
    cases = json.loads(FIXTURES.read_text())['cases']
    result = {case['id']: extract(case) for case in cases}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
