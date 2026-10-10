#!/usr/bin/env python3
"""FAC-03 D3E8: compare a no-SACL idle control against the SACL application interval.

Four bounded checkpoints in one ephemeral Windows observation bracket the passive
idle control and Set-Acl. No individual identity, path, size, PID or time is exported.
Observational differences do not prove that Set-Acl caused a content write.
"""
import argparse
import importlib.util
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "d3e7_control_dependency", HERE / "facad_314_d3e7_preflight_gate.py"
)
d3e7 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d3e7)

SCOPE = "facad_ilexis_roaming_settings"
SHA = re.compile(r"^[0-9a-f]{64}$")
CONTROL_STAGES = ("passive_control_after", "post_sacl_rest")
CONTROL_FIELDS = {
    "schema", "source", "session_id", "selected_scope", "checkpoints",
    "passive_control_seconds", "post_sacl_rest_seconds",
    "shared_app_storage_isolation_verified", "clinical_edit_allowed",
}
BUCKETS = (
    "already_divergent_before_passive_control",
    "first_observed_during_passive_no_sacl_control",
    "first_observed_between_control_and_post_sacl",
    "first_observed_during_post_sacl_rest",
    "first_observed_after_post_sacl_rest_before_launch",
    "not_divergent_before_launch",
    "missing_intermediate_identity",
)


class InvalidControl(ValueError):
    pass


def classify(before, after, events, timeline, d3e4_aggregate, d3e5_aggregate,
             prelaunch, d3e6_aggregate, preflight, d3e7_aggregate, control):
    try:
        independently = d3e7.classify(
            before, after, events, timeline, d3e4_aggregate, d3e5_aggregate,
            prelaunch, d3e6_aggregate, preflight
        )
    except (ValueError, TypeError, KeyError) as exc:
        raise InvalidControl("PRIOR_EVIDENCE_INVALID") from exc
    if not isinstance(d3e7_aggregate, dict) or independently != d3e7_aggregate:
        raise InvalidControl("D3E7_AGGREGATE_MISMATCH")
    if not isinstance(control, dict) or set(control) != CONTROL_FIELDS:
        raise InvalidControl("INVALID_CONTROL_FIELDS")
    if (control["schema"] != "facad314_d3e8_passive_control_local_v1"
            or control["source"] != "EPHEMERAL_SIZE_ONLY_PASSIVE_SACL_CONTROL"
            or control["session_id"] != before["session_id"]
            or control["selected_scope"] != SCOPE
            or control["passive_control_seconds"] != 2
            or type(control["passive_control_seconds"]) is not int
            or control["post_sacl_rest_seconds"] != 2
            or type(control["post_sacl_rest_seconds"]) is not int
            or control["shared_app_storage_isolation_verified"] is not False
            or control["clinical_edit_allowed"] is not False):
        raise InvalidControl("WRONG_CONTROL_PROVENANCE")
    samples = control["checkpoints"]
    if not isinstance(samples, list) or len(samples) != len(CONTROL_STAGES):
        raise InvalidControl("BAD_CONTROL_STAGES")
    for sample, stage in zip(samples, CONTROL_STAGES):
        if (not isinstance(sample, dict) or set(sample) != {"stage", "entries"}
                or sample["stage"] != stage):
            raise InvalidControl("MISORDERED_CONTROL_CHECKPOINTS")
        entries = sample["entries"]
        if not isinstance(entries, dict) or len(entries) > 5000:
            raise InvalidControl("INVALID_CONTROL_ENTRIES")
        for identity, size in entries.items():
            if (not isinstance(identity, str) or SHA.fullmatch(identity) is None
                    or type(size) is not int or size < 0):
                raise InvalidControl("PRIVATE_CONTROL_IDENTITY_OR_SIZE_INVALID")

    start = before["scopes"][SCOPE]["entries"]
    end = after["scopes"][SCOPE]["entries"]
    attributed = set(events["root_pid_relative_key_hashes"]) | set(events["other_pid_relative_key_hashes"])
    targets = sorted(k for k in start.keys() & end.keys()
                     if k not in attributed and start[k]["size"] != end[k]["size"])
    if len(targets) != independently["unattributed_modified_size_changed_count"]:
        raise InvalidControl("UNRECONCILED_TARGETS")
    checkpoints = preflight["checkpoints"]
    before_sacl = checkpoints[1]["entries"]
    after_sacl = checkpoints[2]["entries"]
    counts = {name: 0 for name in BUCKETS}
    for identity in targets:
        original = start[identity]["size"]
        series = (
            before_sacl.get(identity),
            samples[0]["entries"].get(identity),
            after_sacl.get(identity),
            samples[1]["entries"].get(identity),
            prelaunch["entries"].get(identity),
        )
        if any(x is None for x in series):
            counts["missing_intermediate_identity"] += 1
        elif series[0] != original:
            counts["already_divergent_before_passive_control"] += 1
        elif series[1] != original:
            counts["first_observed_during_passive_no_sacl_control"] += 1
        elif series[2] != original:
            counts["first_observed_between_control_and_post_sacl"] += 1
        elif series[3] != original:
            counts["first_observed_during_post_sacl_rest"] += 1
        elif series[4] != original:
            counts["first_observed_after_post_sacl_rest_before_launch"] += 1
        else:
            counts["not_divergent_before_launch"] += 1
    if sum(counts.values()) != len(targets):
        raise InvalidControl("UNRECONCILED_CONTROL_BUCKETS")
    return {
        "schema": "facad314_d3e8_passive_control_aggregate_v1",
        "source": "BOUNDED_TWO_SECOND_PASSIVE_CONTROL_AND_SACL_BRACKET",
        "selected_scope": SCOPE,
        "unattributed_modified_size_changed_count": len(targets),
        "control_interval_counts": counts,
        "control_stages_in_order": list(CONTROL_STAGES),
        "matched_counterfactual_experiment": False,
        "controlled_randomization": False,
        "continuous_monitoring": False,
        "specific_process_writer_proven": False,
        "sacl_caused_content_write_proven": False,
        "complete_event_delivery": False,
        "private_file_identifiers_exported": False,
        "shared_app_storage_isolation_verified": False,
        "clinical_edit_allowed": False,
        "verdict": ("PASSIVE_CONTROL_COMPARISON_NOT_CAUSALITY"
                    if targets else "NO_UNATTRIBUTED_TARGET_NOT_ISOLATION"),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    names = ("before", "after", "event-keys", "timeline", "classification",
             "timing", "prelaunch", "early-window", "preflight", "preflight-aggregate",
             "control", "output")
    for name in names:
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    try:
        values = [
            json.loads(getattr(args, name.replace("-", "_")).read_text(encoding="utf-8-sig"))
            for name in names[:-1]
        ]
        result = classify(*values)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf8")
        print("D3E8_CONTROL_VERDICT=" + result["verdict"])
        for bucket in BUCKETS:
            print("D3E8_" + bucket.upper() + "=" + str(result["control_interval_counts"][bucket]))
        code = 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError):
        print("D3E8_CONTROL_VERDICT=BLOCKED_INVALID_OR_INCOMPLETE_LOCAL_EVIDENCE")
        code = 2
    print("D3E8_CAUSALITY_PROVEN=false")
    print("D3E8_PRIVATE_IDENTITIES_EXPORTED=false")
    print("SHARED_APP_STORAGE_ISOLATION=UNVERIFIED")
    print("CLINICAL_EDIT_ALLOWED=false")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
