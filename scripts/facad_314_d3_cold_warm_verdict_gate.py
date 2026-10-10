#!/usr/bin/env python3
"""Experimental Facad D3 cold/warm *verdict-only* comparison.

Never reads raw snapshots, paths, files, registry or patient data; never clears
real D3. Exit 1 for any observed drift, 2 for invalid evidence, 3 for no
observed drift (INCONCLUSIVE, still NOT a safety clearance).
"""
import argparse
import json
from pathlib import Path

from facad_314_d3_snapshot_diff_gate import SCOPES

KINDS = frozenset(("ADDED", "MODIFIED", "DELETED", "ROOT_APPEARED_OR_DISAPPEARED"))
REQUIRED = frozenset((
    "capture_session_id", "monitored_scope_count", "observed_change_count",
    "observed_changes", "verdict", "d3_isolation_verified",
    "clinical_edit_allowed",
))


class ResearchEvidenceError(ValueError):
    pass


def _validated_verdict(verdict):
    if not isinstance(verdict, dict) or frozenset(verdict) != REQUIRED:
        raise ResearchEvidenceError("Incomplete/unexpected verdict schema")
    if verdict["d3_isolation_verified"] is not False or verdict["clinical_edit_allowed"] is not False:
        raise ResearchEvidenceError("Unjustified clinical/isolation assertion")
    if type(verdict["monitored_scope_count"]) is not int or verdict["monitored_scope_count"] != len(SCOPES):
        raise ResearchEvidenceError("Incomplete observation scope count")
    if not isinstance(verdict["capture_session_id"], str) or not verdict["capture_session_id"]:
        raise ResearchEvidenceError("Missing capture session")
    changes=verdict["observed_changes"]
    if not isinstance(changes, list) or type(verdict["observed_change_count"]) is not int:
        raise ResearchEvidenceError("Invalid change ledger")
    if verdict["observed_change_count"] != len(changes):
        raise ResearchEvidenceError("Inconsistent observed-change count")
    for change in changes:
        if not isinstance(change, dict) or frozenset(change) not in (
            frozenset(("scope", "change")), frozenset(("scope", "change", "entries"))):
            raise ResearchEvidenceError("Unexpected sensitive event fields")
        if change["scope"] not in SCOPES or change["change"] not in KINDS:
            raise ResearchEvidenceError("Unknown scope or event type")
        if "entries" in change and (
            change["change"] != "ROOT_APPEARED_OR_DISAPPEARED" or
            type(change["entries"]) is not int or change["entries"] != 0
        ):
            raise ResearchEvidenceError("Malformed root-drift event")
    expected=("BLOCKED_OBSERVED_STORAGE_DRIFT" if changes else
              "INCONCLUSIVE_NO_OBSERVED_STORAGE_DRIFT")
    if verdict["verdict"] != expected:
        raise ResearchEvidenceError("Verdict contradicts observed changes")
    return {
        kind: sum(x["change"] == kind for x in changes)
        for kind in sorted(KINDS)
    }


def classify(cold, warm):
    cold_counts=_validated_verdict(cold)
    warm_counts=_validated_verdict(warm)
    if cold["capture_session_id"] == warm["capture_session_id"]:
        raise ResearchEvidenceError("Cold and warm captures must be independent sessions")
    c, w = cold["observed_change_count"], warm["observed_change_count"]
    situation=("REPEATED_OBSERVED_DRIFT" if c and w else
               "COLD_ONLY_OBSERVED_DRIFT" if c else
               "WARM_ONLY_OBSERVED_DRIFT" if w else
               "NO_DRIFT_IN_SELECTED_SCOPES_ONLY")
    return {
        "schema": "facad314_d3_cold_warm_verdict_v1",
        "evidence_type": "TWO_SEQUENTIAL_SYNTHETIC_DEMO_SESSIONS_NOT_CAUSAL",
        "cold_count": c,
        "warm_count": w,
        "cold_kind_counts": cold_counts,
        "warm_kind_counts": warm_counts,
        "classification": situation,
        "d3_isolation_verified": False,
        "clinical_edit_allowed": False,
        "patient_data_root_verified": False,
        "facad_process_write_path_attribution": False,
        "same_landmark_parity_executed": False,
        "verdict": ("BLOCKED_OBSERVED_STORAGE_DRIFT" if c or w else
                    "INCONCLUSIVE_NO_OBSERVED_STORAGE_DRIFT"),
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cold", type=Path, required=True)
    p.add_argument("--warm", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a=p.parse_args()
    try:
        cold=json.loads(a.cold.read_text(encoding="utf-8"))
        warm=json.loads(a.warm.read_text(encoding="utf-8"))
        result=classify(cold,warm)
        code=1 if result["verdict"] == "BLOCKED_OBSERVED_STORAGE_DRIFT" else 3
    except (ResearchEvidenceError, OSError, ValueError) as error:
        # No exception strings: file names and paths must not enter reports.
        result={
            "schema": "facad314_d3_cold_warm_verdict_v1",
            "verdict": "BLOCKED_INVALID_OR_INCOMPLETE_EVIDENCE",
            "error_category": type(error).__name__,
            "d3_isolation_verified": False,
            "clinical_edit_allowed": False,
        }
        code=2
    a.output.write_text(json.dumps(result, sort_keys=True, indent=2)+"\n",encoding="utf-8")
    print("D3_COLD_WARM_VERDICT="+result["verdict"])
    if code != 2:
        print("D3_COLD_WARM_CLASSIFICATION="+result["classification"])
        print("D3_COLD_OBSERVED_CHANGES="+str(result["cold_count"]))
        print("D3_WARM_OBSERVED_CHANGES="+str(result["warm_count"]))
    print("D3_ISOLATION_VERIFIED=false")
    print("CLINICAL_EDIT_ALLOWED=false")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
