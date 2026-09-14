#!/usr/bin/env python3
"""R18 audit-only backend extractor for frontend/backend cephalometric concordance."""
from __future__ import annotations

import json
import math
from pathlib import Path

from backend.services.cephalo_steiner_geometry import (
    steiner_sna_deg_v1, steiner_snb_deg_v1, steiner_anb_deg_v1,
    steiner_u1_na_deg_v1, steiner_l1_nb_deg_v1,
)
from backend.services.cephalo_tweed_merrifield_geometry import (
    tweed_fma_deg_v1, tweed_impa_deg_v1, tweed_fmia_deg_v1,
)
from backend.services.cephalo_craniom_angular import (
    craniom_u1_frankfort_deg_v1, craniom_l1_downs_deg_v1,
    craniom_interincisal_deg_v1,
)
from backend.services.cephalo_ricketts_geometry import (
    ricketts_e_line_horizontal_signed_distance_px_v1,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'audit' / 'cephalo_r18_concordance_fixtures.json'
OUT = ROOT / 'audit' / 'out' / 'backend.json'


def js_round(value: float, decimals: int = 0) -> float:
    factor = 10 ** decimals
    return math.floor(value * factor + 0.5) / factor


def point(points: dict[str, tuple[float, float]], key: str):
    return points.get(key)


def have(points: dict[str, tuple[float, float]], *keys: str) -> bool:
    return all(key in points for key in keys)


def safe(call, points, keys, transform=lambda x: x):
    if not have(points, *keys):
        return None
    value = call(*[point(points, k) for k in keys])
    return None if value is None else transform(value)


def extract(case: dict) -> dict[str, float | None]:
    p = {lm['id']: (float(lm['x']), float(lm['y'])) for lm in case['landmarks']}
    ratio = case['mmPerPixel']
    out: dict[str, float | None] = {}
    out['sna'] = safe(steiner_sna_deg_v1, p, ('S','N','A'), lambda v: js_round(v,1))
    out['snb'] = safe(steiner_snb_deg_v1, p, ('S','N','B'), lambda v: js_round(v,1))
    out['anb'] = safe(steiner_anb_deg_v1, p, ('S','N','A','B'), lambda v: js_round(v,1))
    out['i_na_angle'] = safe(steiner_u1_na_deg_v1, p, ('U1_apex','U1_incisal','N','A'), lambda v: js_round(v,0))
    out['i_nb_angle'] = safe(steiner_l1_nb_deg_v1, p, ('L1_apex','L1_incisal','N','B'), lambda v: js_round(v,0))
    out['fma'] = safe(tweed_fma_deg_v1, p, ('Go','Me','Po','Or'), lambda v: js_round(v,0))
    out['impa'] = safe(tweed_impa_deg_v1, p, ('L1_apex','L1_incisal','Go','Me'), lambda v: js_round(v,1))
    out['fmia'] = safe(tweed_fmia_deg_v1, p, ('L1_apex','L1_incisal','Po','Or'), lambda v: js_round(v,0))
    out['u1_frankfort'] = safe(craniom_u1_frankfort_deg_v1, p, ('U1_apex','U1_incisal','Po','Or'), lambda v: js_round(v,1))
    out['l1_downs_craniom'] = safe(craniom_l1_downs_deg_v1, p, ('L1_apex','L1_incisal','Go','Me'), lambda v: js_round(v,1))
    out['interincisal'] = safe(craniom_interincisal_deg_v1, p, ('U1_apex','U1_incisal','L1_apex','L1_incisal'), lambda v: js_round(v,0))
    for out_key, lip_key in (('eline_ls','Ls_soft'),('eline_li','Li_soft')):
        if ratio is not None and have(p, lip_key,'Prn','Pog_soft','Po','Or'):
            value = ricketts_e_line_horizontal_signed_distance_px_v1(p[lip_key],p['Prn'],p['Pog_soft'],p['Po'],p['Or'])
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
