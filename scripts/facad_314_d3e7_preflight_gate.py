#!/usr/bin/env python3
"""D3E7: aggregate before-launch Ilexis size drift around audit/SACL preparation.

The D3 before snapshot is AFTER Facad installation. This evidence separates
observer entry, audit setup, SACL application and remaining prelaunch operations.
A bounded size difference is NOT writer attribution, causality or isolation.
Local SHA-256 identities are never included in the aggregate or stdout.
"""
import argparse
import importlib.util
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "d3e6_preflight_dependency", HERE / "facad_314_d3e6_early_window_gate.py")
d3e6 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d3e6)

SCOPE = "facad_ilexis_roaming_settings"
STAGES = ("observer_entry", "before_sacl_apply", "after_sacl_apply")
BUCKETS = (
    "already_divergent_at_observer_entry",
    "first_observed_during_audit_preparation",
    "first_observed_during_sacl_application",
    "first_observed_after_sacl_before_process_launch",
    "not_yet_divergent_before_process_launch",
    "missing_preflight_identity",
)
SHA = re.compile(r"^[0-9a-f]{64}$")
PREFLIGHT_FIELDS = {"schema", "source", "selected_scope", "session_id",
                    "checkpoints", "shared_app_storage_isolation_verified",
                    "clinical_edit_allowed"}


class InvalidPreflight(ValueError):
    pass


def classify(before, after, events, timeline, d3e4_aggregate,
             d3e5_aggregate, prelaunch, d3e6_aggregate, preflight):
    try:
        independently = d3e6.classify(
            before, after, events, timeline, d3e4_aggregate, d3e5_aggregate, prelaunch)
    except (ValueError, TypeError, KeyError) as exc:
        raise InvalidPreflight("INVALID_D3E6_EVIDENCE") from exc
    if not isinstance(d3e6_aggregate, dict) or independently != d3e6_aggregate:
        raise InvalidPreflight("D3E6_AGGREGATE_MISMATCH")
    if not isinstance(preflight, dict) or set(preflight) != PREFLIGHT_FIELDS:
        raise InvalidPreflight("INVALID_PREFLIGHT_SCHEMA")
    if (preflight["schema"] != "facad314_d3e7_preflight_local_v1"
            or preflight["source"] != "EPHEMERAL_SIZE_ONLY_OBSERVER_AUDIT_SACL_STAGES"
            or preflight["session_id"] != before["session_id"]
            or preflight["selected_scope"] != SCOPE
            or preflight["shared_app_storage_isolation_verified"] is not False
            or preflight["clinical_edit_allowed"] is not False):
        raise InvalidPreflight("WRONG_PREFLIGHT_PROVENANCE")
    checkpoints = preflight["checkpoints"]
    if not isinstance(checkpoints, list) or len(checkpoints) != len(STAGES):
        raise InvalidPreflight("WRONG_PREFLIGHT_CHECKPOINT_COUNT")
    for entry, stage in zip(checkpoints, STAGES):
        if (not isinstance(entry, dict) or set(entry) != {"stage", "entries"}
                or entry["stage"] != stage):
            raise InvalidPreflight("WRONG_PREFLIGHT_ORDER")
        entries = entry["entries"]
        if not isinstance(entries, dict) or len(entries) > 5000:
            raise InvalidPreflight("INVALID_PREFLIGHT_ENTRIES")
        for key, size in entries.items():
            if (not isinstance(key, str) or SHA.fullmatch(key) is None
                    or type(size) is not int or size < 0):
                raise InvalidPreflight("INVALID_PRIVATE_ENTRY")
    start = before["scopes"][SCOPE]["entries"]
    end = after["scopes"][SCOPE]["entries"]
    attributed = set(events["root_pid_relative_key_hashes"]) | set(events["other_pid_relative_key_hashes"])
    targets = sorted(k for k in start.keys() & end.keys()
                     if k not in attributed and start[k]["size"] != end[k]["size"])
    if len(targets) != independently["unattributed_modified_size_changed_count"]:
        raise InvalidPreflight("UNRECONCILED_SIZE_TARGETS")
    counts = {bucket: 0 for bucket in BUCKETS}
    for key in targets:
        original = start[key]["size"]
        values = [point["entries"].get(key) for point in checkpoints]
        values.append(prelaunch["entries"].get(key))
        if any(size is None for size in values):
            counts["missing_preflight_identity"] += 1
        elif values[0] != original:
            counts["already_divergent_at_observer_entry"] += 1
        elif values[1] != original:
            counts["first_observed_during_audit_preparation"] += 1
        elif values[2] != original:
            counts["first_observed_during_sacl_application"] += 1
        elif values[3] != original:
            counts["first_observed_after_sacl_before_process_launch"] += 1
        else:
            counts["not_yet_divergent_before_process_launch"] += 1
    if sum(counts.values()) != len(targets):
        raise InvalidPreflight("UNRECONCILED_BUCKETS")
    return {
        "schema": "facad314_d3e7_preflight_aggregate_v1",
        "source": "BOUNDED_BEFORE_LAUNCH_SIZE_ONLY_AUDIT_PREPARATION",
        "selected_scope": SCOPE,
        "unattributed_modified_size_changed_count": len(targets),
        "preflight_counts": counts,
        "checkpoints_in_order": list(STAGES) + ["immediately_before_start_process"],
        "change_continuously_monitored": False,
        "installation_observed_by_this_gate": False,
        "audit_policy_or_sacl_causality_proven": False,
        "facad_root_process_causality_proven": False,
        "complete_event_delivery": False,
        "complete_descendant_coverage": False,
        "file_identity_or_metadata_exported": False,
        "shared_app_storage_isolation_verified": False,
        "clinical_edit_allowed": False,
        "verdict": ("BOUNDED_PREFLIGHT_DIVERGENCE_NOT_CAUSALITY"
                    if targets else "NO_UNATTRIBUTED_TARGET_NOT_ISOLATION"),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("before", "after", "event-keys", "timeline", "classification",
                 "timing", "prelaunch", "early-window", "preflight", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    try:
        inputs = [json.loads(getattr(args, name.replace("-", "_")).read_text(encoding="utf-8-sig"))
                  for name in ("before", "after", "event-keys", "timeline",
                               "classification", "timing", "prelaunch",
                               "early-window", "preflight")]
        result = classify(*inputs)
        args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print("D3E7_PREFLIGHT_VERDICT=" + result["verdict"])
        for bucket in BUCKETS:
            print("D3E7_" + bucket.upper() + "=" + str(result["preflight_counts"][bucket]))
        code = 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError):
        print("D3E7_PREFLIGHT_VERDICT=BLOCKED_INVALID_OR_INCOMPLETE_LOCAL_EVIDENCE")
        code = 2
    print("D3E7_WRITER_ATTRIBUTION_PROVEN=false")
    print("D3E7_PRIVATE_FILE_IDENTITY_EXPORTED=false")
    print("SHARED_APP_STORAGE_ISOLATION=UNVERIFIED")
    print("CLINICAL_EDIT_ALLOWED=false")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
