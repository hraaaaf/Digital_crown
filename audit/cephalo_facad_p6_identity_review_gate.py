"""P6: validate *evidence claims*, never certify anatomy from red pixels.

Synthetic CI only. Actual FACAD screenshots and review notes stay outside the
public repository and GitHub Actions artifacts.
"""
from __future__ import annotations

from collections.abc import Mapping

REQUIRED = ("Ii", "Iia", "Is", "Isa", "A", "Pog", "PGs")
CANONICAL = {"Ii": "L1_incisal", "Iia": "L1_apex", "Is": "U1_incisal",
             "Isa": "U1_apex", "A": "A", "Pog": "Pog_hard", "PGs": "Pog_soft"}
FORBIDDEN = {"name", "patient", "image", "screenshot", "pixel", "coordinates",
             "date_of_birth", "case_id", "demographics"}

def validate_review(review: object) -> dict:
    """Return a fail-closed aggregate; NEVER authorize production identities."""
    if not isinstance(review, Mapping):
        raise ValueError("review must be a mapping")
    if set(review) != {"schema", "source_unannotated_full_resolution",
                       "source_rights_confirmed", "independent_reviewer",
                       "same_trace_verified", "landmarks"}:
        raise ValueError("unexpected or missing evidence fields")
    if review["schema"] != "FACAD_P6_INDEPENDENT_IDENTITY_REVIEW_V1":
        raise ValueError("schema mismatch")
    flags = ("source_unannotated_full_resolution", "source_rights_confirmed",
             "independent_reviewer", "same_trace_verified")
    if any(type(review[k]) is not bool for k in flags):
        raise ValueError("review flags must be boolean")
    landmarks = review["landmarks"]
    if not isinstance(landmarks, Mapping) or set(landmarks) != set(REQUIRED):
        raise ValueError("exact priority landmark roster required")
    supported = 0
    for label in REQUIRED:
        record = landmarks[label]
        if not isinstance(record, Mapping) or set(record) != {
            "independent_image_identification", "selected_tooth_confirmed",
            "anatomical_definition_confirmed", "reviewer_signed"}:
            raise ValueError("invalid landmark evidence structure")
        if any(type(value) is not bool for value in record.values()):
            raise ValueError("landmark flags must be boolean")
        if label in ("Ii", "Iia", "Is", "Isa") and not record["selected_tooth_confirmed"]:
            continue
        if all(record[k] for k in ("independent_image_identification",
                                  "anatomical_definition_confirmed",
                                  "reviewer_signed")):
            supported += 1
    gates = all(review[k] for k in flags)
    return {
        "schema": "FACAD_P6_REVIEW_GATE_RESULT_V1",
        "priority_count": len(REQUIRED),
        "independent_review_complete": gates and supported == len(REQUIRED),
        "priority_landmarks_review_supported": supported if gates else 0,
        "raw_facad_pog_promotable_to_dc_pog_hard": False,
        "canonical_bridge_executed": False,
        "clinical_parity_count": 0,
        "clinical_no_go": True,
        "real_image_processed_in_public_ci": False,
    }
