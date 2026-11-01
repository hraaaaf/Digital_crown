#!/usr/bin/env python3
"""Experimental historic FACAD Bergen Short recalculation, audit only.

Recovered from FACAD_Decortication_DigitalCrown_2026-10-31.zip in user Drive.
The angle rules are candidates for ONE synthetic FACAD trace, NOT a FACAD-wide
specification, a certified clinical engine, or a patient/runtime dependency.
"""
from __future__ import annotations

import argparse
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

FACAD_DISPLAY = {
    "SNA": 82.2, "SNB": 80.2, "ANB": 2.0, "SNPog": 83.6,
    "NSBa": 3.1, "ML/NSL": 58.6, "NL/NSL": 145.7,
    "ML/NL": -87.1, "InterIncisal": 10.1, "ILs/NSL": -128.7,
    "ILi/ML": 59.9, "Pog-NB": 8.8,
}

def load_markers(path: Path) -> dict[str, tuple[float, float]]:
    result = {}
    for marker in ET.parse(path).getroot().iter("marker"):
        name, coord = marker.findtext("name"), marker.findtext("coord")
        if name and coord:
            x, y = map(float, coord.split())
            result[name] = (x, y)
    return result

def vector(points, start: str, end: str) -> tuple[float, float] | None:
    """Undefined vectors must never become zero-degree clinical measurements."""
    try:
        x0, y0 = points[start]
        x1, y1 = points[end]
        if any(isinstance(v, bool) for v in (x0, y0, x1, y1)):
            return None
        dx, dy = float(x1) - float(x0), float(y1) - float(y0)
        norm = math.hypot(dx, dy)
    except (KeyError, TypeError, ValueError, OverflowError):
        return None
    if not all(math.isfinite(v) for v in (dx, dy, norm)) or norm <= 1e-12:
        return None
    return dx, dy

def angle3(points, vertex: str, ray1: str, ray2: str) -> float | None:
    """Empirical signed ray1->ray2 angle; screen y increases downward."""
    u, v = vector(points, vertex, ray1), vector(points, vertex, ray2)
    if u is None or v is None:
        return None
    determinant, dot = u[0]*v[1]-u[1]*v[0], u[0]*v[0]+u[1]*v[1]
    if not math.isfinite(determinant) or not math.isfinite(dot):
        return None
    result = math.degrees(math.atan2(determinant, dot))
    return result if math.isfinite(result) else None

def line_direction(points, start: str, end: str) -> float | None:
    ray = vector(points, start, end)
    return math.atan2(ray[1], ray[0]) if ray is not None else None

def angle4(points, a: str, b: str, c: str, d: str) -> float | None:
    """Empirical signed line difference wrapped to [-180,180)."""
    first, second = line_direction(points, a, b), line_direction(points, c, d)
    if first is None or second is None:
        return None
    result = math.degrees(((second-first)+math.pi) % (2*math.pi)-math.pi)
    return result if math.isfinite(result) else None

def point_line_signed(points, line_start: str, line_end: str,
                      point: str, mm_per_pixel: float) -> float | None:
    direction = vector(points, line_start, line_end)
    target, origin = points.get(point), points.get(line_start)
    if direction is None or target is None or origin is None:
        return None
    if isinstance(mm_per_pixel, bool):
        return None
    try:
        ratio = float(mm_per_pixel)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(ratio) or ratio <= 0:
        return None
    try:
        if any(isinstance(v, bool) for v in (*target, *origin)):
            return None
        x, y = map(float, target)
        x0, y0 = map(float, origin)
        dx, dy = direction
        value = (dx*(y-y0)-dy*(x-x0)) / math.hypot(dx, dy) * ratio
    except (ValueError, TypeError, OverflowError, ZeroDivisionError):
        return None
    return value if math.isfinite(value) else None

def calculate_bergen_short(points, mm_per_pixel: float) -> dict[str, float | None]:
    """The twelve operations and directions of the historical Bergen short.cph trace."""
    a3, a4 = angle3, angle4
    return {
        "SNA": a3(points,"N","A","S"),
        "SNB": a3(points,"N","B","S"),
        "ANB": a3(points,"N","A","B"),
        "SNPog": a3(points,"N","Pog","S"),
        "NSBa": a3(points,"S","N","Ba"),
        "ML/NSL": a4(points,"S","N","Go","Me"),
        "NL/NSL": a4(points,"S","N","PNS","ANS"),
        "ML/NL": a4(points,"PNS","ANS","Go","Me"),
        "InterIncisal": a4(points,"Iia","Ii","Isa","Is"),
        "ILs/NSL": a4(points,"Is","Isa","S","N"),
        "ILi/ML": a4(points,"Go","Me","Ii","Iia"),
        "Pog-NB": point_line_signed(points,"B","N","Pog",mm_per_pixel),
    }

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("fcd", type=Path, help="Explicit synthetic reference FCD/XML; never patient data.")
    parser.add_argument("--mm-per-pixel", type=float, default=0.2)
    args = parser.parse_args()
    points = load_markers(args.fcd)
    results = calculate_bergen_short(points, args.mm_per_pixel)
    rows = []
    for name, value in results.items():
        rounded = round(value,1) if value is not None and math.isfinite(value) else None
        expected = FACAD_DISPLAY[name]
        rows.append({
            "factor": name,
            "independent_raw": round(value,8) if rounded is not None else None,
            "facad_ui_historical": expected,
            "independent_round_0_1": rounded,
            "matches_display": rounded is not None and abs(rounded-expected)<1e-9,
        })
    blocked = [row["factor"] for row in rows if not row["matches_display"]]
    output = {
        "case": str(args.fcd), "mm_per_pixel": args.mm_per_pixel, "rows": rows,
        "status": "HOLD" if blocked else "SYNTHETIC_RECONSTRUCTION_PARITY",
        "blocking_factors": blocked,
        "scope_note": "Reconstructed single synthetic case: not original FCD, new FACAD run, or clinical approval.",
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))
    if blocked:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
