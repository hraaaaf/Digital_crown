"""Calibrated CNSS 610-1-04 dental-care PDF overlay profile.

Coordinates are valid only for the exact cabinet-validated binary with SHA-256
``e1fb63afb1893886d518135dfb209f24f2464e8cd664e89881fc7c373854864d``.
The source is the 2-page bilingual CNSS/AMO dental form validated by the cabinet on
2026-09-15. Human visual validation restricts page 1 auto-fill to the practitioner
section starting at ``Déclaration du Chirurgien Dentiste``. The insured section,
signature/cachet areas and insurer-only areas are deliberately never written.
"""

from __future__ import annotations

from backend.services.insurance_pdf_overlay import (
    InsuranceOverlayPlacement,
    InsuranceOverlayProfile,
    OverlayKind,
)


CNSS_610_1_04_TEMPLATE_SHA256 = (
    "e1fb63afb1893886d518135dfb209f24f2464e8cd664e89881fc7c373854864d"
)
CNSS_610_1_04_PROFILE_VERSION = "cnss-610-1-04-e1fb63af-v2"
CNSS_610_1_04_MAX_LINES = 3


def _mark(field_key: str, x: float, y: float) -> InsuranceOverlayPlacement:
    return InsuranceOverlayPlacement(
        field_key=field_key,
        page_index=0,
        x=x,
        y=y,
        font_size=8.0,
        kind=OverlayKind.MARK,
        max_chars=1,
    )


# Page 1 is intentionally restricted to the practitioner declaration zone validated
# by the practitioner. The upper "Partie réservée à l'assuré(e)" stays untouched.
_PAGE_1 = (
    InsuranceOverlayPlacement("administrative.beneficiary_full_name", 0, 680, 275, 8.0, max_chars=42),
    InsuranceOverlayPlacement("administrative.beneficiary_birth_date", 0, 790, 291, 7.0, max_chars=10),
    InsuranceOverlayPlacement("administrative.beneficiary_national_id", 0, 800, 312, 8.0, max_chars=16),
    _mark("choice.beneficiary_sex.M", 846, 331),
    _mark("choice.beneficiary_sex.F", 921, 331),
    InsuranceOverlayPlacement("administrative.practitioner_inpe", 0, 665, 365, 8.0, max_chars=14),
    _mark("choice.care_type.SOINS", 789, 393),
    _mark("choice.care_type.PROTHESE", 789, 411),
    _mark("choice.care_type.ORTHODONTIE_FACIALE", 789, 429),
    _mark("choice.care_type.AUTRES", 789, 446),
    InsuranceOverlayPlacement("administrative.prior_approval_number", 0, 790, 464, 7.0, max_chars=18),
    InsuranceOverlayPlacement("administrative.accident_circumstances", 0, 770, 478, 7.0, max_chars=28),
    InsuranceOverlayPlacement("administrative.accident_date", 0, 790, 484, 7.0, max_chars=10),
)


def _line(index: int, y: float) -> tuple[InsuranceOverlayPlacement, ...]:
    return (
        InsuranceOverlayPlacement(f"lines[{index}].teeth", 1, 590, y, 7.0, max_chars=12),
        InsuranceOverlayPlacement(f"lines[{index}].ngap_code", 1, 640, y, 7.0, max_chars=10),
        InsuranceOverlayPlacement(f"lines[{index}].service_date", 1, 686, y, 7.0, max_chars=10),
        InsuranceOverlayPlacement(f"lines[{index}].ngap_coefficient", 1, 752, y, 7.0, max_chars=8),
        InsuranceOverlayPlacement(f"lines[{index}].amount_mad", 1, 850, y, 7.0, max_chars=10),
    )


CNSS_610_1_04_PROFILE_V1 = InsuranceOverlayProfile(
    organization="CNSS",
    template_version="CNSS-610-1-04",
    template_hash=CNSS_610_1_04_TEMPLATE_SHA256,
    profile_version=CNSS_610_1_04_PROFILE_VERSION,
    placements=_PAGE_1 + _line(0, 105) + _line(1, 176) + _line(2, 247),
    max_lines=CNSS_610_1_04_MAX_LINES,
)
