#!/usr/bin/env python3
"""J14 public-safe, synthetic-only decision gate for mixed dentition.

Do not apply a provisional deciduous FDI to a permanent-only model.
This module NEVER reads radiographs, private manifests or original case IDs.
"""
from __future__ import annotations
from collections import Counter

PERMANENT_32 = frozenset(f"{q}{t}" for q in "1234" for t in "12345678")
PRIMARY_20 = frozenset(f"{q}{t}" for q in "5678" for t in "12345")
assert len(PERMANENT_32) == 32 and len(PRIMARY_20) == 20
assert not (PERMANENT_32 & PRIMARY_20)
ALLOWED_STATES = frozenset(("confirmed", "tentative", "unresolved"))

class OntologyGateError(ValueError):
    """Invalid schema, unknown class or refusal to infer patient class."""

def classify_fdi(value: object) -> str:
    if type(value) is not str or len(value) != 2 or not value.isascii():
        raise OntologyGateError("invalid_fdi_code")
    if value in PERMANENT_32:
        return "permanent"
    if value in PRIMARY_20:
        return "primary"
    raise OntologyGateError("unsupported_fdi_code")

def gate_decision(candidate: dict) -> str:
    if type(candidate) is not dict:
        raise OntologyGateError("invalid_clinical_decision")
    if set(candidate) != {"fdi", "clinical_status"}:
        raise OntologyGateError("invalid_clinical_decision_fields")
    status = candidate["clinical_status"]
    if type(status) is not str or status not in ALLOWED_STATES:
        raise OntologyGateError("invalid_clinical_certainty")
    tooth_kind = classify_fdi(candidate["fdi"])
    if status != "confirmed":
        return "BLOCK_UNCONFIRMED_CLINICAL_DECISION"
    if tooth_kind == "primary":
        return "BLOCK_PRIMARY_OUTSIDE_PERMANENT32_ONTOLOGY"
    return "ELIGIBLE_FOR_LATER_PRIVATE_GEOMETRY_AND_COLLISION_QA"

def aggregate_only(candidate_decisions: list[dict]) -> dict:
    if type(candidate_decisions) is not list:
        raise OntologyGateError("decision_list_required")
    results = Counter(gate_decision(x) for x in candidate_decisions)
    return {
        "schema": "digital-crown-lot05-j14-aggregate-only-v1",
        "decision_count": len(candidate_decisions),
        "confirmed_permanent_candidates_needing_private_QA":
            results["ELIGIBLE_FOR_LATER_PRIVATE_GEOMETRY_AND_COLLISION_QA"],
        "blocked_primary_decisions":
            results["BLOCK_PRIMARY_OUTSIDE_PERMANENT32_ONTOLOGY"],
        "blocked_unconfirmed_decisions":
            results["BLOCK_UNCONFIRMED_CLINICAL_DECISION"],
        "private_clinical_manifest_loaded": False,
        "no_media_or_patient_identifiers_processed": True,
        "clinically_validated": False,
        "patient_independence_proven": False,
        "commercial_rights_cleared": False,
    }
