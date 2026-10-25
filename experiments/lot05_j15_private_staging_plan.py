#!/usr/bin/env python3
"""LOT05/J15: synthetic-only fail-closed private staging plan, NO staging execution.

Never consumes case-level manifests, original images, private label trees or patient IDs.
Existing J13 engine has hard-coded obsolete 21/10 census; do not bypass its checks.
"""
from __future__ import annotations
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from lot05_j14_mixed_dentition_ontology_gate import gate_decision, OntologyGateError

EXPECTED_PRIVATE_SCHEMA = "digital-crown-lot05-j13-private-decision-map-v1"
EXPECTED_SOURCE_PIN = "92e2cc3ae5eebc9de509311a3edefb7106fca7dd"
EXPECTED_SPLITS = {"train":266,"val":33,"test":34}
ALLOWED = "ELIGIBLE_FOR_LATER_PRIVATE_GEOMETRY_AND_COLLISION_QA"

class J15Error(ValueError):
    pass

def plan_synthetic(summary: dict) -> dict:
    """Accept aggregate counts only; do not accept private manifest or sample keys."""
    if type(summary) is not dict or set(summary) != {
        "source_pin", "source_counts", "active_permanent_proposals",
        "blocked_clinical_decisions", "unresolved_clinical_decisions",
        "collision_groups_pending", "exact_dedupe_pending",
        "originals_unchanged", "private_geometry_qa_passed",
        "private_staging_engine_integrated",
    }:
        raise J15Error("invalid_aggregate_summary")
    counts=summary["source_counts"]
    if type(counts) is not dict or counts != EXPECTED_SPLITS:
        raise J15Error("source_counts_mismatch")
    if summary["source_pin"] != EXPECTED_SOURCE_PIN:
        raise J15Error("source_pin_mismatch")
    keys=("active_permanent_proposals","blocked_clinical_decisions",
          "unresolved_clinical_decisions","collision_groups_pending",
          "exact_dedupe_pending")
    if any(type(summary[k]) is not int or summary[k]<0 for k in keys):
        raise J15Error("invalid_aggregate_count")
    if any(type(summary[k]) is not bool for k in (
            "originals_unchanged","private_geometry_qa_passed",
            "private_staging_engine_integrated")):
        raise J15Error("invalid_gate_boolean")
    if not summary["originals_unchanged"]:
        raise J15Error("source_modified")
    blockers=[]
    if summary["blocked_clinical_decisions"]:
        blockers.append("blocked_clinical_decisions")
    if summary["unresolved_clinical_decisions"]:
        blockers.append("unresolved_clinical_decisions")
    if summary["collision_groups_pending"]:
        blockers.append("collision_groups_pending")
    if summary["exact_dedupe_pending"]:
        blockers.append("exact_dedupe_pending")
    if not summary["private_geometry_qa_passed"]:
        blockers.append("private_geometry_qa_not_verified")
    if not summary["private_staging_engine_integrated"]:
        blockers.append("private_staging_engine_not_integrated")
    return {
        "schema":"digital-crown-lot05-j15-synthetic-private-stage-plan-v1",
        "status":"BLOCKED_NO_REAL_STAGING" if blockers else "PRECHECK_ONLY_NOT_STAGING",
        "blockers":blockers,
        "expected_source_files":sum(EXPECTED_SPLITS.values()),
        "source_pin_verified_from_claim_only":True,
        "manifest_schema_expected":EXPECTED_PRIVATE_SCHEMA,
        "originals_modified":False,
        "real_private_manifest_loaded":False,
        "private_corrected_dataset_created":False,
        "clinical_training_allowed":False,
        "clinical_activation_allowed":False,
        "commercial_rights_cleared":False,
        "patient_independence_proven":False,
    }

def main() -> int:
    # A fixed SYNTHETIC example, NOT an import of private V22.
    summary={
        "source_pin":EXPECTED_SOURCE_PIN,
        "source_counts":EXPECTED_SPLITS.copy(),
        "active_permanent_proposals":4,
        "blocked_clinical_decisions":1,
        "unresolved_clinical_decisions":1,
        "collision_groups_pending":1,
        "exact_dedupe_pending":1,
        "originals_unchanged":True,
        "private_geometry_qa_passed":False,
        "private_staging_engine_integrated":False,
    }
    result=plan_synthetic(summary)
    print("J15_SYNTHETIC_ONLY="+json.dumps(result,sort_keys=True))
    return 0 if result["status"]=="BLOCKED_NO_REAL_STAGING" else 1

if __name__=="__main__":
    raise SystemExit(main())
