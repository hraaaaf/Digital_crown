#!/usr/bin/env python3
"""D3E5: aggregate FIRST OBSERVED size divergence of un-attributed Ilexis files.

Three runner-private checkpoints bound intervals but are not continuous monitoring.
Neither timing nor 4663 identity overlap proves causality or storage isolation.
No name, path, pseudonymous file key, size, PID, timestamp, or session ID exported.
"""
import argparse
import importlib.util
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("d3e4_timing_dependency", HERE / "facad_314_d3e4_unattributed_classification_gate.py")
d3e4 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d3e4)

SCOPE = "facad_ilexis_roaming_settings"
STAGES = ("after_launch", "pre_stop", "post_stop")
BUCKETS = (
    "first_observed_by_post_launch",
    "first_observed_while_root_running",
    "first_observed_during_stop_interval",
    "first_observed_after_post_stop",
    "intermediate_identity_missing",
)
SHA = re.compile(r"^[0-9a-f]{64}$")
TIMELINE_FIELDS = {"schema", "source", "session_id", "selected_scope",
                   "checkpoints", "shared_app_storage_isolation_verified", "clinical_edit_allowed"}


class InvalidTiming(ValueError):
    pass


def classify(before, after, events, timeline, d3e4_aggregate):
    try:
        independent = d3e4.classify(before, after, events)
    except (ValueError, TypeError, KeyError) as exc:
        raise InvalidTiming("INVALID_D3E4_EVIDENCE") from exc
    if (not isinstance(d3e4_aggregate, dict)
            or d3e4_aggregate != independent):
        raise InvalidTiming("D3E4_CLASSIFICATION_MISMATCH")
    if not isinstance(timeline, dict) or set(timeline) != TIMELINE_FIELDS:
        raise InvalidTiming("BAD_TIMELINE_FIELDS")
    if (timeline["schema"] != "facad314_d3e5_timeline_local_v1"
            or timeline["source"] != "EPHEMERAL_ILEXIS_METADATA_ONLY"
            or timeline["session_id"] != before["session_id"]
            or timeline["selected_scope"] != SCOPE
            or timeline["shared_app_storage_isolation_verified"] is not False
            or timeline["clinical_edit_allowed"] is not False):
        raise InvalidTiming("WRONG_TIMELINE_SOURCE_OR_FORGED_CLEARANCE")
    samples = timeline["checkpoints"]
    if not isinstance(samples, list) or len(samples) != len(STAGES):
        raise InvalidTiming("INVALID_CHECKPOINT_COUNT")
    for sample, stage in zip(samples, STAGES):
        if (not isinstance(sample, dict)
                or set(sample) != {"stage", "entries"}
                or sample["stage"] != stage):
            raise InvalidTiming("WRONG_CHECKPOINT_ORDER")
        entries = sample["entries"]
        if not isinstance(entries, dict) or len(entries) > 5000:
            raise InvalidTiming("INVALID_CHECKPOINT_ENTRIES")
        for name, size in entries.items():
            if (not isinstance(name, str) or SHA.fullmatch(name) is None
                    or type(size) is not int or size < 0):
                raise InvalidTiming("INVALID_CHECKPOINT_IDENTITY_OR_SIZE")
    start = before["scopes"][SCOPE]["entries"]
    end = after["scopes"][SCOPE]["entries"]
    attributed = set(events["root_pid_relative_key_hashes"]) | set(events["other_pid_relative_key_hashes"])
    candidates = sorted(k for k in start.keys() & end.keys()
                        if k not in attributed and start[k]["size"] != end[k]["size"])
    if len(candidates) != independent["unexplained_modified_size_changed_count"]:
        raise InvalidTiming("TARGET_COUNT_MISMATCH")
    counts = {bucket: 0 for bucket in BUCKETS}
    for key in candidates:
        old_size = start[key]["size"]
        series = [sample["entries"].get(key) for sample in samples]
        if any(size is None for size in series):
            counts["intermediate_identity_missing"] += 1
        elif series[0] != old_size:
            counts["first_observed_by_post_launch"] += 1
        elif series[1] != old_size:
            counts["first_observed_while_root_running"] += 1
        elif series[2] != old_size:
            counts["first_observed_during_stop_interval"] += 1
        else:
            counts["first_observed_after_post_stop"] += 1
    if sum(counts.values()) != len(candidates):
        raise InvalidTiming("NON_RECONCILED_TIMING_COUNT")
    return {
        "schema": "facad314_d3e5_first_observed_timing_aggregate_v1",
        "source": "BOUNDED_RUNNER_PRIVATE_METADATA_CHECKPOINTS_ONLY",
        "selected_scope": SCOPE,
        "unattributed_modified_size_changed_count": len(candidates),
        "first_observed_size_divergence": counts,
        "checkpoints_in_order": list(STAGES),
        "continuous_change_tracking": False,
        "complete_descendant_process_coverage": False,
        "complete_event_delivery": False,
        "causality_proven": False,
        "file_identity_or_metadata_exported": False,
        "shared_app_storage_isolation_verified": False,
        "clinical_edit_allowed": False,
        "verdict": ("BOUNDED_FIRST_OBSERVED_DIVERGENCE_NOT_CAUSALITY"
                    if candidates else "NO_UNATTRIBUTED_SIZE_TARGET_NOT_ISOLATION"),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("before", "after", "event-keys", "timeline", "classification", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    a = parser.parse_args()
    try:
        data = [json.loads(getattr(a, name.replace("-", "_")).read_text(encoding="utf-8-sig"))
                for name in ("before", "after", "event-keys", "timeline", "classification")]
        result = classify(*data)
        a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf8")
        print("D3E5_TIMING_VERDICT=" + result["verdict"])
        for bucket in BUCKETS:
            print("D3E5_" + bucket.upper() + "=" + str(result["first_observed_size_divergence"][bucket]))
        code = 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError):
        print("D3E5_TIMING_VERDICT=BLOCKED_INVALID_OR_INCOMPLETE_PRIVATE_TIMELINE")
        code = 2
    print("D3E5_CONTINUOUS_MONITORING=false")
    print("D3E5_CAUSALITY_PROVEN=false")
    print("SHARED_APP_STORAGE_ISOLATION=UNVERIFIED")
    print("CLINICAL_EDIT_ALLOWED=false")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
