"""Overlay profile for the cabinet-validated derived FAR 2021-1 dental reference.

The exact original FAR binary was not recovered. This profile is valid only for the
cabinet-accepted two-page reconstructed reference bound to the SHA-256 below.
Dental lines are written on logical Page 4 (physical page 1, left half). Logical Page 2
ORDONNANCE and logical Page 3 are intentionally untouched by this dental-claim profile.
Signature/cachet, medical-control and insurer-decision zones are intentionally absent.
"""

from backend.services.insurance_pdf_overlay import (
    InsuranceOverlayPlacement,
    InsuranceOverlayProfile,
    OverlayKind,
)
from backend.services.insurance_template_registry import FAR_2021_1


FAR_2021_1_DERIVED_TEMPLATE_SHA256 = (
    "c953d74f25ee5e3160683f16c45783448d55ea89640c710653a3e2cbf782bf42"
)
FAR_2021_1_DERIVED_PROFILE_VERSION = "far-2021-1-derived-c953d74f-v2"
FAR_2021_1_DERIVED_MAX_LINES = 6


# Coordinates are PDF points on the accepted A4-landscape reconstructed reference.
# Physical page 1 contains logical Page 4 on the left and logical Page 1 on the right.
_PAGE_1_ADMIN = (
    InsuranceOverlayPlacement("administrative.insured_national_id", 0, 558, 167, 6.4, max_chars=20),
    InsuranceOverlayPlacement("administrative.insured_account_number", 0, 558, 187, 6.4, max_chars=24),
    InsuranceOverlayPlacement("administrative.insured_phone", 0, 558, 206, 6.4, max_chars=20),
    InsuranceOverlayPlacement("administrative.insured_full_name", 0, 558, 233, 6.4, max_chars=38),
    InsuranceOverlayPlacement("administrative.insured_grade", 0, 558, 251, 6.4, max_chars=28),
    InsuranceOverlayPlacement("administrative.insured_unit", 0, 558, 270, 6.4, max_chars=28),
    InsuranceOverlayPlacement("administrative.insured_address", 0, 558, 288, 6.0, max_chars=52),
    InsuranceOverlayPlacement("administrative.beneficiary_full_name", 0, 558, 334, 6.4, max_chars=38),
    InsuranceOverlayPlacement("administrative.beneficiary_birth_date", 0, 558, 351, 6.4, max_chars=10),
    InsuranceOverlayPlacement(
        "choice.relationship_to_insured.ADHERENT", 0, 537, 375, 8,
        kind=OverlayKind.MARK,
    ),
    InsuranceOverlayPlacement(
        "choice.relationship_to_insured.CONJOINT", 0, 656, 375, 8,
        kind=OverlayKind.MARK,
    ),
    InsuranceOverlayPlacement(
        "choice.relationship_to_insured.ENFANT", 0, 766, 375, 8,
        kind=OverlayKind.MARK,
    ),
    InsuranceOverlayPlacement(
        "choice.claim_context.MALADIE", 0, 504, 407, 8,
        kind=OverlayKind.MARK,
    ),
    InsuranceOverlayPlacement(
        "choice.claim_context.MATERNITE", 0, 634, 407, 8,
        kind=OverlayKind.MARK,
    ),
    InsuranceOverlayPlacement(
        "choice.claim_context.ACCIDENT", 0, 762, 407, 8,
        kind=OverlayKind.MARK,
    ),
    InsuranceOverlayPlacement("administrative.practitioner_inpe", 0, 558, 450, 6.4, max_chars=18),
    InsuranceOverlayPlacement("computed.total_amount_mad", 0, 447, 519, 6.4, max_chars=12),
    InsuranceOverlayPlacement("computed.attachments_count", 0, 570, 508, 6.4, max_chars=2),
    InsuranceOverlayPlacement(
        "choice.care_type.SOINS", 0, 168, 206, 8,
        kind=OverlayKind.MARK,
    ),
    InsuranceOverlayPlacement(
        "choice.care_type.PROTHESE", 0, 292, 206, 8,
        kind=OverlayKind.MARK,
    ),
)


# Six full dental rows are visible in the accepted logical Page 4 table. Baselines were
# calibrated against the rendered frozen PDF, not copied from CNSS/CNOPS coordinates.
_ROW_Y = (95.0, 110.0, 125.0, 140.0, 155.0, 170.0)


def _dental_line_placements() -> tuple[InsuranceOverlayPlacement, ...]:
    placements: list[InsuranceOverlayPlacement] = []
    for index, y in enumerate(_ROW_Y):
        placements.extend((
            InsuranceOverlayPlacement(f"lines[{index}].service_date", 0, 31, y, 5.5, max_chars=10),
            InsuranceOverlayPlacement(f"lines[{index}].teeth", 0, 83, y, 5.5, max_chars=12),
            InsuranceOverlayPlacement(f"lines[{index}].label", 0, 128, y, 5.5, max_chars=40),
            InsuranceOverlayPlacement(f"lines[{index}].ngap_coefficient", 0, 292, y, 5.5, max_chars=10),
            InsuranceOverlayPlacement(f"lines[{index}].amount_mad", 0, 350, y, 5.5, max_chars=12),
        ))
    return tuple(placements)


FAR_2021_1_DERIVED_PROFILE = InsuranceOverlayProfile(
    organization="FAR",
    template_version=FAR_2021_1.version,
    template_hash=FAR_2021_1_DERIVED_TEMPLATE_SHA256,
    profile_version=FAR_2021_1_DERIVED_PROFILE_VERSION,
    placements=_PAGE_1_ADMIN + _dental_line_placements(),
    max_lines=FAR_2021_1_DERIVED_MAX_LINES,
)
