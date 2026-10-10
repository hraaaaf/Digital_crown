#!/usr/bin/env python3
"""D3E6: constrain the early prelaunch/postlaunch size-change window.

Runner-private metadata only. The root process has not started at the prelaunch
sample. Neither the timing bracket nor missing 4663 proves the writer identity.
Only aggregate counts leave the runner; never file keys, names, sizes or PIDs.
"""
import argparse
import importlib.util
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "d3e5_early_window_dependency", HERE / "facad_314_d3e5_first_observed_timing_gate.py"
)
d3e5 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d3e5)

SCOPE = "facad_ilexis_roaming_settings"
SHA = re.compile(r"^[0-9a-f]{64}$")
PRELAUNCH_FIELDS = {
    "schema", "source", "session_id", "selected_scope", "capture_stage", "entries",
    "shared_app_storage_isolation_verified", "clinical_edit_allowed",
}
BUCKETS = (
    "already_divergent_before_root_launch",
    "first_observed_between_prelaunch_and_postlaunch",
    "not_yet_divergent_at_postlaunch",
    "missing_early_identity",
)


class InvalidEarlyWindow(ValueError):
    pass


def classify(before, after, events, timeline, d3e4_aggregate, d3e5_aggregate, prelaunch):
    try:
        independent = d3e5.classify(before, after, events, timeline, d3e4_aggregate)
    except (ValueError, TypeError, KeyError) as exc:
        raise InvalidEarlyWindow("INVALID_PRIOR_TIMING_EVIDENCE") from exc
    if not isinstance(d3e5_aggregate, dict) or d3e5_aggregate != independent:
        raise InvalidEarlyWindow("D3E5_AGGREGATE_MISMATCH")
    if not isinstance(prelaunch, dict) or set(prelaunch) != PRELAUNCH_FIELDS:
        raise InvalidEarlyWindow("BAD_PRELAUNCH_FIELDS")
    if (prelaunch["schema"] != "facad314_d3e6_prelaunch_local_v1"
            or prelaunch["source"] != "EPHEMERAL_ILEXIS_SIZE_ONLY_BEFORE_FACAD_START"
            or prelaunch["session_id"] != before["session_id"]
            or prelaunch["selected_scope"] != SCOPE
            or prelaunch["capture_stage"] != "immediately_before_start_process"
            or prelaunch["shared_app_storage_isolation_verified"] is not False
            or prelaunch["clinical_edit_allowed"] is not False):
        raise InvalidEarlyWindow("FORGED_OR_WRONG_PRELAUNCH_PROVENANCE")
    entries = prelaunch["entries"]
    if not isinstance(entries, dict) or len(entries) > 5000:
        raise InvalidEarlyWindow("BAD_PRELAUNCH_ENTRIES")
    for key, size in entries.items():
        if (not isinstance(key, str) or SHA.fullmatch(key) is None
                or type(size) is not int or size < 0):
            raise InvalidEarlyWindow("INVALID_PRIVATE_FILE_IDENTITY_OR_SIZE")
    start = before["scopes"][SCOPE]["entries"]
    end = after["scopes"][SCOPE]["entries"]
    attributed = set(events["root_pid_relative_key_hashes"]) | set(events["other_pid_relative_key_hashes"])
    targets = sorted(key for key in start.keys() & end.keys()
                     if key not in attributed and start[key]["size"] != end[key]["size"])
    if len(targets) != independent["unattributed_modified_size_changed_count"]:
        raise InvalidEarlyWindow("UNRECONCILED_TARGET_SET")
    postlaunch = timeline["checkpoints"][0]["entries"]
    counts = {bucket: 0 for bucket in BUCKETS}
    for key in targets:
        original = start[key]["size"]
        pre = entries.get(key)
        post = postlaunch.get(key)
        if pre is None or post is None:
            counts["missing_early_identity"] += 1
        elif pre != original:
            counts["already_divergent_before_root_launch"] += 1
        elif post != original:
            counts["first_observed_between_prelaunch_and_postlaunch"] += 1
        else:
            counts["not_yet_divergent_at_postlaunch"] += 1
    if sum(counts.values()) != len(targets):
        raise InvalidEarlyWindow("UNRECONCILED_EARLY_WINDOW_COUNT")
    return {
        "schema": "facad314_d3e6_early_window_aggregate_v1",
        "source": "BOUNDED_PRELAUNCH_AND_POSTLAUNCH_FILE_SIZE_METADATA_ONLY",
        "selected_scope": SCOPE,
        "unattributed_modified_size_changed_count": len(targets),
        "early_window_counts": counts,
        "continuous_change_tracking": False,
        "root_process_writer_proven": False,
        "other_process_writer_proven": False,
        "complete_event_delivery": False,
        "complete_descendant_process_coverage": False,
        "specific_process_causality_proven": False,
        "file_identity_or_metadata_exported": False,
        "shared_app_storage_isolation_verified": False,
        "clinical_edit_allowed": False,
        "verdict": ("BOUNDED_EARLY_WINDOW_NOT_CAUSALITY" if targets
                    else "NO_UNATTRIBUTED_SIZE_TARGET_NOT_ISOLATION"),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("before", "after", "event-keys", "timeline", "classification", "timing", "prelaunch", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args()
    try:
        data = [json.loads(getattr(args, name.replace("-", "_")).read_text(encoding="utf-8-sig"))
                for name in ("before", "after", "event-keys", "timeline", "classification", "timing", "prelaunch")]
        output = classify(*data)
        args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf8")
        print("D3E6_EARLY_WINDOW_VERDICT=" + output["verdict"])
        for bucket in BUCKETS:
            print("D3E6_" + bucket.upper() + "=" + str(output["early_window_counts"][bucket]))
        code = 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError):
        print("D3E6_EARLY_WINDOW_VERDICT=BLOCKED_INVALID_OR_INCOMPLETE_PRIVATE_EVIDENCE")
        code = 2
    print("D3E6_WRITER_CAUSALITY_PROVEN=false")
    print("D3E6_PRIVATE_FILE_IDENTITY_EXPORTED=false")
    print("SHARED_APP_STORAGE_ISOLATION=UNVERIFIED")
    print("CLINICAL_EDIT_ALLOWED=false")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
