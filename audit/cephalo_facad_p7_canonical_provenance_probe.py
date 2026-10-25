"""P7: exercise the real Digital Crown canonical identity bridge, fail closed.

Synthetic evidence only. A human review contract is NOT a certified SRPose
observation and must not grant a clinical identity alias.
"""
from __future__ import annotations

import importlib

from audit.cephalo_facad_p6_identity_review_gate import validate_review

def probe(review: object) -> dict:
    gate = validate_review(review)
    from audit.cephalo_facad_robert_p3_canonical_adapter_probe import _real_typed_adapter
    ev, _, _ = _real_typed_adapter()
    bridge = importlib.import_module("backend.services.cephalo_landmark_identity_bridge")
    # Actual P4 bridge path, with manual/legacy source provenance.
    raw = ev.LandmarkEvidence(
        evidence_id="p7_synthetic_manual_Pog",
        landmark_id="Pog", x=100.0, y=155.0,
        source_image_ref="synthetic-p7-no-real-image",
        origin=ev.LandmarkOrigin.MANUAL,
        evidence_status=ev.EvidenceStatus.OBSERVED,
        evidence_refs=["synthetic-p7-no-real-image"],
    )
    projected = bridge.project_canonical_landmark_identities(
        {"Pog": raw}, previous_auto_landmarks=()
    )
    if "Pog" not in projected or "Pog_hard" in projected:
        raise AssertionError("UNSAFE: manual FACAD Pog promoted to Pog_hard")
    return {
        "schema": "FACAD_P7_CANONICAL_PROVENANCE_PROBE_V1",
        "production_bridge_exercised": True,
        "p6_independent_review_complete": gate["independent_review_complete"],
        "manual_pog_retained": True,
        "manual_pog_promoted_to_pog_hard": False,
        "certified_srpose_evidence_available": False,
        "clinical_parity_count": 0,
        "clinical_no_go": True,
    }
