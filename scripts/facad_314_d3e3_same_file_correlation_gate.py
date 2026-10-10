#!/usr/bin/env python3
"""Correlate LOCAL pseudonymous path IDs to snapshot metadata drift, never D3 clearance.

Event key manifest must remain on an ephemeral Windows runner and be deleted after
the correlation. Only allowlisted aggregate metrics may be uploaded.
"""
import argparse
import importlib.util
import json
import re
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("d3_snapshot",HERE/"facad_314_d3_snapshot_diff_gate.py")
d3=importlib.util.module_from_spec(spec)
spec.loader.exec_module(d3)
SHA=re.compile(r"^[0-9a-f]{64}$")
SOURCE="EPHEMERAL_FACAD_ROOT_PID_4663_KEYS_LOCAL_ONLY"
FIELDS={"schema","source","session_id","selected_scope","root_pid_relative_key_hashes",
        "other_pid_relative_key_hashes","observed_descendant_pid_count",
        "clinical_edit_allowed","shared_app_storage_isolation_verified",
        "complete_descendant_process_coverage","event_delivery_complete"}
SCOPE="facad_ilexis_roaming_settings"
class InvalidCorrelation(ValueError):
    pass

def compute(before,after,events):
    try:
        d3.validate(before,"before")
        d3.validate(after,"after")
    except (ValueError,KeyError,TypeError) as e:
        raise InvalidCorrelation("INVALID_SNAPSHOT") from e
    if before["session_id"]!=after["session_id"]:
        raise InvalidCorrelation("MISMATCHED_SESSION")
    if not isinstance(events,dict) or set(events)!=FIELDS:
        raise InvalidCorrelation("INVALID_EVENT_KEY_MANIFEST")
    if (events["schema"]!="facad314_d3e3_event_ids_v1" or
        events["source"]!=SOURCE or events["selected_scope"]!=SCOPE or
        events["session_id"]!=before["session_id"]):
        raise InvalidCorrelation("WRONG_SOURCE_OR_SESSION")
    if any(events[k] is not False for k in ("clinical_edit_allowed",
            "shared_app_storage_isolation_verified","complete_descendant_process_coverage",
            "event_delivery_complete")):
        raise InvalidCorrelation("FORGED_COVERAGE")
    keys=events["root_pid_relative_key_hashes"]
    if not isinstance(keys,list) or len(keys)>4000 or not all(
            isinstance(v,str) and SHA.fullmatch(v) for v in keys):
        raise InvalidCorrelation("BAD_KEY_IDS")
    if len(set(keys))!=len(keys):
        raise InvalidCorrelation("DUPLICATED_KEY_IDS")
    extra=events["other_pid_relative_key_hashes"]
    if not isinstance(extra,list) or len(extra)>4000 or not all(
            isinstance(v,str) and SHA.fullmatch(v) for v in extra):
        raise InvalidCorrelation("BAD_OTHER_PID_KEY_IDS")
    if len(set(extra))!=len(extra):
        raise InvalidCorrelation("DUPLICATED_OTHER_PID_KEY_IDS")
    descendants=events["observed_descendant_pid_count"]
    if type(descendants) is not int or not 0<=descendants<=4000:
        raise InvalidCorrelation("BAD_SAMPLED_DESCENDANT_COUNT")
    a=before["scopes"][SCOPE];b=after["scopes"][SCOPE]
    if (not a["present"] or not b["present"] or
        a["root_fingerprint"].lower()!=b["root_fingerprint"].lower()):
        raise InvalidCorrelation("ROOT_ABSENT_OR_CHANGED")
    left=a["entries"];right=b["entries"]
    changed={k for k in set(left)|set(right) if left.get(k)!=right.get(k)}
    observed=set(keys)
    matched=changed&observed
    summary={
        "schema":"facad314_d3e3_same_file_aggregate_v1",
        "source":"LOCAL_SNAPSHOT_AND_NATIVE_4663_CORRELATION_ONLY",
        "selected_scope":SCOPE,
        "selected_scope_metadata_changed_count":len(changed),
        "facad_root_pid_unique_written_file_count":len(observed),
        "same_file_metadata_and_4663_count":len(matched),
        "changed_files_without_root_pid_event_count":len(changed-matched),
        "root_pid_event_files_without_metadata_change_count":len(observed-matched),
        "filename_or_file_hash_exported":False,
        "complete_descendant_process_coverage":False,
        "event_delivery_complete":False,
        "causal_metadata_change_proven":False,
        "all_storage_roots_verified":False,
        "shared_app_storage_isolation_verified":False,
        "clinical_edit_allowed":False,
        "verdict":("SAME_FILE_IDENTITY_OVERLAP_ONLY_NOT_CAUSALITY" if matched else
                   "BLOCKED_NO_SAME_FILE_IDENTITY_OVERLAP")
    }
    return summary, (0 if matched else 2)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--before",required=True,type=Path)
    p.add_argument("--after",required=True,type=Path)
    p.add_argument("--event-keys",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    try:
        before=json.loads(a.before.read_text(encoding="utf-8-sig"))
        after=json.loads(a.after.read_text(encoding="utf-8-sig"))
        events=json.loads(a.event_keys.read_text(encoding="utf-8-sig"))
        result,code=compute(before,after,events)
        a.output.write_text(json.dumps(result,sort_keys=True,indent=2),encoding="utf-8")
        print("D3E3_CORRELATION_VERDICT="+result["verdict"])
        print("D3E3_MATCHED_SAME_FILE_COUNT="+str(result["same_file_metadata_and_4663_count"]))
    except (OSError,UnicodeError,ValueError,TypeError,KeyError):
        print("D3E3_CORRELATION_VERDICT=BLOCKED_INVALID_OR_INCOMPLETE_LOCAL_EVIDENCE")
        code=2
    print("D3E3_FILE_IDENTITY_EXPORT=false")
    print("D3E3_CAUSALITY_PROVEN=false")
    print("SHARED_APP_STORAGE_ISOLATION=UNVERIFIED")
    print("CLINICAL_EDIT_ALLOWED=false")
    return code

if __name__=="__main__":
    raise SystemExit(main())
