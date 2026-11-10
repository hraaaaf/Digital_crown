"""FACAD P8: source provenance gate. Synthetic contract; no clinical release."""
from __future__ import annotations
import hashlib
import re
from audit.cephalo_facad_p8_png_integrity import inspect_png
from audit.cephalo_facad_p8_manifest_integrity import verify_bundle

SCHEMA = "FACAD_P8_SOURCE_ATTESTATION_V1"
FLAGS = ("native_source", "no_overlay", "same_case", "same_trace", "rights")
KEYS = {"schema", "image_hash", "export_bundle_hash", "source_width",
        "source_height", "facad_version", "screen_capture", *FLAGS}

def verify(image_data: bytes, export_bundle_data: bytes, attestation: dict) -> dict:
    if not isinstance(attestation, dict) or set(attestation) != KEYS:
        raise ValueError("invalid attestation")
    if attestation["schema"] != SCHEMA or attestation["facad_version"] != "3.14.1.1111":
        raise ValueError("wrong schema or version")
    if any(type(attestation[k]) is not bool for k in (*FLAGS, "screen_capture")):
        raise ValueError("non-boolean declaration")
    if any(type(attestation[k]) is not int or attestation[k] < 512 for k in ("source_width", "source_height")):
        raise ValueError("missing full resolution declaration")
    for key in ("image_hash", "export_bundle_hash"):
        if not isinstance(attestation[key], str) or not re.fullmatch("[0-9a-f]{64}", attestation[key]):
            raise ValueError("invalid SHA256")
    if type(image_data) is not bytes or type(export_bundle_data) is not bytes:
        raise ValueError("binary inputs required")
    # Verify full PNG chunk CRC, decompression and row structure.
    # Manifest checks are structural; actual six private exports are NOT in CI.
    dimensions = inspect_png(image_data)
    verify_bundle(export_bundle_data)
    if dimensions != (attestation["source_width"], attestation["source_height"]):
        raise ValueError("image pixel dimensions do not match attestation")
    hashes_match = (hashlib.sha256(image_data).hexdigest() == attestation["image_hash"]
                    and hashlib.sha256(export_bundle_data).hexdigest() == attestation["export_bundle_hash"])
    declared = all(attestation[k] for k in FLAGS) and attestation["screen_capture"] is False
    return {
        "byte_integrity_matches": hashes_match,
        "operator_declarations_complete": declared,
        "intake_candidate_only": hashes_match and declared,
        "png_structural_integrity": True,
        "facad_manifest_structure_verified": True,
        "original_image_authenticated": False,
        "six_private_exports_verified_by_bytes": False,
        "anatomical_validation": False,
        "same_trace_independently_verified": False,
        "clinical_parities": 0,
        "clinical_no_go": True,
    }
