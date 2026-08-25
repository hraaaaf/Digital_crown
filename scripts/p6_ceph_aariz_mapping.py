#!/usr/bin/env python3
"""Research-only Aariz -> Digital Crown cephalometric landmark adapter.

The adapter is deliberately title-based, never position-based. Aariz's Nature
Table 4 presentation order and the official repository config order differ
(e.g. Pronasale), so treating a published row number as a tensor index would be
unsafe. Clinical Wits occlusal points are not synthesized here.
"""
from __future__ import annotations

from collections.abc import Sequence
from numbers import Real

AARIZ_OFFICIAL_TITLES: tuple[str, ...] = (
    "A-point",
    "Anterior Nasal Spine",
    "B-point",
    "Menton",
    "Nasion",
    "Orbitale",
    "Pogonion",
    "Posterior Nasal Spine",
    "Pronasale",
    "Ramus",
    "Sella",
    "Articulare",
    "Condylion",
    "Gnathion",
    "Gonion",
    "Porion",
    "Lower 2nd PM Cusp Tip",
    "Lower Incisor Tip",
    "Lower Molar Cusp Tip",
    "Upper 2nd PM Cusp Tip",
    "Upper Incisor Apex",
    "Upper Incisor Tip",
    "Upper Molar Cusp Tip",
    "Lower Incisor Apex",
    "Labrale inferius",
    "Labrale superius",
    "Soft Tissue Nasion",
    "Soft Tissue Pogonion",
    "Subnasale",
)

# Only direct anatomical equivalences already consumed by CephaloEngine.
# No inferred point and no clinical-plane construction is permitted here.
AARIZ_TITLE_TO_DC: dict[str, str] = {
    "A-point": "A",
    "Anterior Nasal Spine": "ANS",
    "B-point": "B",
    "Menton": "Me",
    "Nasion": "N",
    "Orbitale": "Or",
    "Pronasale": "Prn",
    "Sella": "S",
    "Condylion": "Co",
    "Gnathion": "Gn",
    "Gonion": "Go",
    "Porion": "Po",
    "Lower Incisor Tip": "L1i",
    "Upper Incisor Apex": "U1a",
    "Upper Incisor Tip": "U1i",
    "Lower Incisor Apex": "L1a",
    "Labrale inferius": "Li",
    "Labrale superius": "Ls",
    "Soft Tissue Pogonion": "Pog_soft",
    "Subnasale": "Sn",
}

DC_DIRECT_CANONICAL_POINTS: frozenset[str] = frozenset(AARIZ_TITLE_TO_DC.values())
DC_UNSUPPORTED_OCCLUSAL_POINTS: frozenset[str] = frozenset({"Occ_Ant", "Occ_Post"})


def _coerce_xy(value: Sequence[Real], title: str) -> tuple[float, float]:
    if len(value) != 2:
        raise ValueError(f"{title}: coordinate must contain exactly x,y")
    x, y = value
    if not isinstance(x, Real) or not isinstance(y, Real):
        raise TypeError(f"{title}: coordinates must be numeric")
    x_f, y_f = float(x), float(y)
    if x_f != x_f or y_f != y_f or x_f in (float("inf"), float("-inf")) or y_f in (
        float("inf"),
        float("-inf"),
    ):
        raise ValueError(f"{title}: coordinates must be finite")
    return x_f, y_f


def adapt_aariz29_to_digital_crown(
    landmark_titles: Sequence[str],
    coords: Sequence[Sequence[Real]],
) -> dict[str, tuple[float, float]]:
    """Map one complete Aariz 29-point prediction to 20 direct DC points.

    Strictness is intentional: a changed/missing Aariz ontology must fail closed
    rather than silently shifting anatomical identities.
    """
    if len(landmark_titles) != 29 or len(coords) != 29:
        raise ValueError("Aariz adapter requires exactly 29 titles and 29 coordinates")

    normalized_titles = tuple(str(title).strip() for title in landmark_titles)
    if len(set(normalized_titles)) != 29:
        raise ValueError("Aariz landmark titles must be unique")

    expected = set(AARIZ_OFFICIAL_TITLES)
    observed = set(normalized_titles)
    if observed != expected:
        missing = sorted(expected - observed)
        extra = sorted(observed - expected)
        raise ValueError(f"Aariz ontology mismatch; missing={missing}, extra={extra}")

    by_title = {
        title: _coerce_xy(coord, title)
        for title, coord in zip(normalized_titles, coords, strict=True)
    }
    mapped = {
        canonical: by_title[title]
        for title, canonical in AARIZ_TITLE_TO_DC.items()
    }

    if set(mapped) != set(DC_DIRECT_CANONICAL_POINTS):
        raise RuntimeError("internal Aariz -> Digital Crown mapping contract is inconsistent")
    return mapped
