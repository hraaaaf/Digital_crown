"""Overlay profile for the exact cabinet-validated CNOPS dental form.

This profile is valid only for the two-page binary whose SHA-256 is declared below.
Coordinates were calibrated against that exact binary. Signature/cachet, insurer and
agent zones are intentionally absent. The form exposes nine dental act rows.
"""

from backend.services.insurance_pdf_overlay import (
    InsuranceOverlayPlacement,
    InsuranceOverlayProfile,
    OverlayKind,
)


CNOPS_DENTAL_TEMPLATE_SHA256 = (
    "89097caca32aef6b4d34d2d06fb9cc6f9bdc1f3c4385cf5558b5742a3af6f505"
)
CNOPS_DENTAL_TEMPLATE_VERSION = "CNOPS-DENTAL-CABINET-2026-09-16"
CNOPS_DENTAL_PROFILE_VERSION = "cnops-dental-cabinet-2026-09-16-89097cac-v1"
CNOPS_DENTAL_MAX_LINES = 9


_PAGE_1 = (
    InsuranceOverlayPlacement(
        "choice.request_nature.PRIOR_APPROVAL", 0, 639, 78, 8,
        kind=OverlayKind.MARK,
    ),
    InsuranceOverlayPlacement(
        "choice.request_nature.EXECUTION", 0, 700, 78, 8,
        kind=OverlayKind.MARK,
    ),
    InsuranceOverlayPlacement("administrative.insured_full_name", 0, 530, 124, 7, max_chars=35),
    InsuranceOverlayPlacement("administrative.insured_affiliation_number", 0, 529, 136, 7, max_chars=22),
    InsuranceOverlayPlacement("administrative.insured_registration_number", 0, 532, 149, 7, max_chars=22),
    InsuranceOverlayPlacement("administrative.insured_national_id", 0, 530, 163, 7, max_chars=20),
    InsuranceOverlayPlacement(
        "choice.relationship_to_insured.CONJOINT", 0, 614, 181, 8,
        kind=OverlayKind.MARK,
    ),
    InsuranceOverlayPlacement(
        "choice.relationship_to_insured.ENFANT", 0, 688, 181, 8,
        kind=OverlayKind.MARK,
    ),
    InsuranceOverlayPlacement("administrative.insured_address", 0, 500, 203, 7, max_chars=70),
    InsuranceOverlayPlacement("computed.total_amount_mad", 0, 563, 229, 7, max_chars=12),
    InsuranceOverlayPlacement("computed.attachments_count", 0, 585, 242, 7, max_chars=2),
    InsuranceOverlayPlacement("administrative.beneficiary_full_name", 0, 532, 286, 7, max_chars=35),
    InsuranceOverlayPlacement("administrative.beneficiary_birth_date", 0, 606, 298, 7, max_chars=10),
    InsuranceOverlayPlacement("administrative.beneficiary_national_id", 0, 610, 311, 7, max_chars=20),
    InsuranceOverlayPlacement(
        "choice.beneficiary_sex.M", 0, 601, 322, 8,
        kind=OverlayKind.MARK,
    ),
    InsuranceOverlayPlacement(
        "choice.beneficiary_sex.F", 0, 686, 322, 8,
        kind=OverlayKind.MARK,
    ),
    InsuranceOverlayPlacement("administrative.practitioner_inpe", 0, 615, 353, 7, max_chars=18),
    InsuranceOverlayPlacement(
        "choice.care_type.SOINS", 0, 541, 387, 8,
        kind=OverlayKind.MARK,
    ),
    InsuranceOverlayPlacement(
        "choice.care_type.PROTHESE", 0, 725, 387, 8,
        kind=OverlayKind.MARK,
    ),
    InsuranceOverlayPlacement(
        "choice.care_type.ORTHODONTIE_FACIALE", 0, 541, 401, 8,
        kind=OverlayKind.MARK,
    ),
    InsuranceOverlayPlacement(
        "choice.care_type.AUTRES", 0, 725, 401, 8,
        kind=OverlayKind.MARK,
    ),
    InsuranceOverlayPlacement("administrative.prior_approval_number", 0, 617, 416, 7, max_chars=18),
    InsuranceOverlayPlacement("administrative.accident_date", 0, 611, 440, 7, max_chars=10),
    InsuranceOverlayPlacement("administrative.accident_circumstances", 0, 529, 452, 7, max_chars=50),
)


# At 160 dpi, the exact binary table boundaries are approximately:
# y = 181, 215, 252, 290, 329, 368, 407, 442, 481, 518 px.
# The baseline values below are the corresponding PDF-point row centres plus a small
# baseline correction. The value-key column is deliberately left blank: no trustworthy
# source field exists for it in the current submission schema.
_ROW_Y = (92.10, 108.075, 124.95, 142.275, 159.825, 177.375, 194.025, 210.675, 227.775)


def _line_placements() -> tuple[InsuranceOverlayPlacement, ...]:
    placements: list[InsuranceOverlayPlacement] = []
    for index, y in enumerate(_ROW_Y):
        placements.extend((
            InsuranceOverlayPlacement(f"lines[{index}].teeth", 1, 452.8, y, 6.5, max_chars=12),
            InsuranceOverlayPlacement(f"lines[{index}].ngap_code", 1, 500.4, y, 6.5, max_chars=14),
            InsuranceOverlayPlacement(f"lines[{index}].service_date", 1, 541.35, y, 6.5, max_chars=10),
            InsuranceOverlayPlacement(f"lines[{index}].ngap_coefficient", 1, 601.525, y, 6.5, max_chars=10),
            InsuranceOverlayPlacement(f"lines[{index}].amount_mad", 1, 682.425, y, 6.5, max_chars=12),
        ))
    return tuple(placements)


CNOPS_DENTAL_PROFILE = InsuranceOverlayProfile(
    organization="CNOPS",
    template_version=CNOPS_DENTAL_TEMPLATE_VERSION,
    template_hash=CNOPS_DENTAL_TEMPLATE_SHA256,
    profile_version=CNOPS_DENTAL_PROFILE_VERSION,
    placements=_PAGE_1 + _line_placements(),
    max_lines=CNOPS_DENTAL_MAX_LINES,
)
