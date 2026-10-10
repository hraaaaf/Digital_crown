#!/usr/bin/env python3
"""D3E9: reject malformed/unsafe public independent-arm metadata.

No path, filename, file hash, PID, raw ACL, or individual size may be exported.
One arm is never evidence of counterfactual causality or safe clinical isolation.
"""
import argparse
import json
from pathlib import Path

ARMS = {"passive_1", "passive_2", "sacl_1", "sacl_2"}
FIELDS = {
    "schema", "source", "arm", "intervention", "pre_intervention_file_count",
    "post_intervention_file_count", "changed_size_count", "created_count",
    "removed_count", "passive_wait_seconds", "sacl_restored",
    "audit_policy_restored", "separate_ephemeral_windows_runner",
    "facad_root_launched_during_trial", "raw_file_metadata_exported",
    "file_identity_or_path_exported", "matched_counterfactual_proven",
    "writer_causality_proven", "complete_audit_event_delivery",
    "shared_app_storage_isolation_verified", "clinical_edit_allowed", "verdict",
}


class InvalidD3E9(ValueError):
    pass


def validate(document, arm):
    if not isinstance(document, dict) or set(document) != FIELDS or arm not in ARMS:
        raise InvalidD3E9("FIELDS_OR_EXPECTED_ARM_INVALID")
    if (document["schema"] != "facad314_d3e9_independent_arm_v1"
            or document["source"] != "BOUNDED_INDEPENDENT_WINDOWS_RUNNER_METADATA_ONLY"
            or document["arm"] != arm
            or document["intervention"] != ("sacl_applied" if arm.startswith("sacl_") else "passive_no_sacl")
            or document["verdict"] != "BOUNDED_CONTROLLED_ARM_NOT_CAUSALITY"):
        raise InvalidD3E9("PROVENANCE_OR_ARM_INCONSISTENT")
    for key in ("pre_intervention_file_count", "post_intervention_file_count",
                "changed_size_count", "created_count", "removed_count"):
        value = document[key]
        if type(value) is not int or not 0 <= value <= 5000:
            raise InvalidD3E9("BAD_COUNT")
    if document["passive_wait_seconds"] != 2 or type(document["passive_wait_seconds"]) is not int:
        raise InvalidD3E9("CONTROL_DURATION_MISMATCH")
    if (document["changed_size_count"] > document["pre_intervention_file_count"]
            or document["changed_size_count"] > document["post_intervention_file_count"]
            or (document["pre_intervention_file_count"] - document["removed_count"]
                + document["created_count"] != document["post_intervention_file_count"])):
        raise InvalidD3E9("UNRECONCILED_COUNTS")
    truth = ("sacl_restored", "audit_policy_restored", "separate_ephemeral_windows_runner")
    falsity = ("facad_root_launched_during_trial", "raw_file_metadata_exported",
               "file_identity_or_path_exported", "matched_counterfactual_proven",
               "writer_causality_proven", "complete_audit_event_delivery",
               "shared_app_storage_isolation_verified", "clinical_edit_allowed")
    if any(document[x] is not True for x in truth) or any(document[x] is not False for x in falsity):
        raise InvalidD3E9("FORGED_SAFETY_OR_RESTORATION_CLAIM")
    return {
        "schema": "facad314_d3e9_arm_checked_v1",
        "arm": arm,
        "intervention": document["intervention"],
        "changed_size_count": document["changed_size_count"],
        "created_count": document["created_count"],
        "removed_count": document["removed_count"],
        "clinical_edit_allowed": False,
        "shared_app_storage_isolation_verified": False,
        "causality_proven": False,
        "verdict": "CONTROLLED_ARM_OBSERVED_NOT_CAUSALITY",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--arm", choices=sorted(ARMS), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        obj = json.loads(args.input.read_text(encoding="utf-8-sig"))
        safe = validate(obj, args.arm)
        args.output.write_text(json.dumps(safe, sort_keys=True, indent=2) + "\n", encoding="utf8")
        print("D3E9_ARM_VERDICT=" + safe["verdict"])
        print("D3E9_ARM=" + safe["arm"])
        print("D3E9_CHANGED_SIZE_COUNT=" + str(safe["changed_size_count"]))
        return 0
    except (ValueError, TypeError, KeyError, UnicodeError, OSError):
        print("D3E9_ARM_VERDICT=BLOCKED_INVALID_OR_INCOMPLETE_CONTROL_EVIDENCE")
        print("CLINICAL_EDIT_ALLOWED=false")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
