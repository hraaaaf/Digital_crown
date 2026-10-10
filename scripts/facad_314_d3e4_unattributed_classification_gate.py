#!/usr/bin/env python3
"""Classify local Ilexis changed identities by native 4663 PID class.

No filenames, hashes, PID, SID, timestamps or session identifiers leave runner.
Classification is NOT a causal attribution, complete process tree, or D3 clearance.
"""
import argparse
import importlib.util
import json
import re
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("d3snapshot",HERE/"facad_314_d3_snapshot_diff_gate.py")
snapshot=importlib.util.module_from_spec(spec)
spec.loader.exec_module(snapshot)
SHA=re.compile(r"^[0-9a-f]{64}$")
SCOPE="facad_ilexis_roaming_settings"
FIELDS={"schema","source","session_id","selected_scope","root_pid_relative_key_hashes",
        "other_pid_relative_key_hashes","observed_descendant_pid_count",
        "clinical_edit_allowed","shared_app_storage_isolation_verified",
        "complete_descendant_process_coverage","event_delivery_complete"}
CATEGORIES=("added","modified","deleted")
BUCKETS=("facad_root_only","other_pid_only","both_pid_classes","no_4663_event")

class InvalidEvidence(ValueError): pass

def classify(before,after,events):
    try:
        snapshot.validate(before,"before")
        snapshot.validate(after,"after")
    except (ValueError,KeyError,TypeError) as e:
        raise InvalidEvidence("INVALID_SNAPSHOT") from e
    if before["session_id"]!=after["session_id"]:
        raise InvalidEvidence("MISMATCHED_SNAPSHOT_SESSIONS")
    if not isinstance(events,dict) or set(events)!=FIELDS:
        raise InvalidEvidence("INVALID_MANIFEST_FIELDS")
    if (events["schema"]!="facad314_d3e3_event_ids_v1" or
        events["source"]!="EPHEMERAL_FACAD_ROOT_PID_4663_KEYS_LOCAL_ONLY" or
        events["session_id"]!=before["session_id"] or
        events["selected_scope"]!=SCOPE):
        raise InvalidEvidence("BAD_SOURCE_OR_SESSION")
    for field in ("clinical_edit_allowed","shared_app_storage_isolation_verified",
                  "complete_descendant_process_coverage","event_delivery_complete"):
        if events[field] is not False:
            raise InvalidEvidence("FORGED_COVERAGE")
    descendants=events["observed_descendant_pid_count"]
    if type(descendants) is not int or not (0<=descendants<=4000):
        raise InvalidEvidence("BAD_DESCENDANT_COUNT")
    for field in ("root_pid_relative_key_hashes","other_pid_relative_key_hashes"):
        keys=events[field]
        if (not isinstance(keys,list) or len(keys)>4000 or
            not all(isinstance(k,str) and SHA.fullmatch(k) for k in keys) or
            len(set(keys))!=len(keys)):
            raise InvalidEvidence("BAD_IDENTITY_LIST")
    a=before["scopes"][SCOPE]
    b=after["scopes"][SCOPE]
    if not a["present"] or not b["present"] or a["root_fingerprint"]!=b["root_fingerprint"]:
        raise InvalidEvidence("ROOT_UNPROVEN")
    root=set(events["root_pid_relative_key_hashes"])
    other=set(events["other_pid_relative_key_hashes"])
    left=a["entries"];right=b["entries"]
    results={kind:{bucket:0 for bucket in BUCKETS} for kind in CATEGORIES}
    count=0
    # Snapshot non-official filetree fingerprints hash only size and UTC mtime.
    # A same-size fingerprint change is thus consistent with an mtime change.
    # Do not infer content mutation, causality, or event completeness.
    unexplained_modified_size_changed=0
    unexplained_modified_same_size_fingerprint_changed=0
    for key in set(left)|set(right):
        old=left.get(key);new=right.get(key)
        if old==new:continue
        kind="added" if old is None else ("deleted" if new is None else "modified")
        bucket=("both_pid_classes" if key in root and key in other else
                "facad_root_only" if key in root else
                "other_pid_only" if key in other else "no_4663_event")
        results[kind][bucket]+=1
        if kind=="modified" and bucket=="no_4663_event":
            if old["size"] != new["size"]:
                unexplained_modified_size_changed+=1
            else:
                unexplained_modified_same_size_fingerprint_changed+=1
        count+=1
    total_without_events=sum(results[k]["no_4663_event"] for k in CATEGORIES)
    out={
        "schema":"facad314_d3e4_unattributed_aggregate_v1",
        "source":"LOCAL_ILEXIS_SNAPSHOT_AND_4663_PID_CLASSIFICATION_ONLY",
        "selected_scope":SCOPE,
        "change_classification":results,
        "changed_identity_count":count,
        "changed_identity_without_any_observed_4663_count":total_without_events,
        "unexplained_modified_size_changed_count":unexplained_modified_size_changed,
        "unexplained_modified_same_size_fingerprint_changed_count":unexplained_modified_same_size_fingerprint_changed,
        "observed_descendant_pid_count_during_sampling":descendants,
        "non_root_events_are_proven_descendants":False,
        "complete_descendant_process_coverage":False,
        "event_delivery_complete":False,
        "specific_process_cause_proven":False,
        "all_storage_roots_verified":False,
        "filename_or_file_hash_exported":False,
        "shared_app_storage_isolation_verified":False,
        "clinical_edit_allowed":False,
        "verdict":("UNATTRIBUTED_CHANGE_REMAINS" if total_without_events
                   else "NO_UNATTRIBUTED_IDENTITY_IN_BOUNDED_SCOPE_NOT_ISOLATION"),
    }
    # No green clinical conclusion even when local classifies all identities.
    return out

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("before","after","event-keys","output"):
        p.add_argument("--"+key,required=True,type=Path)
    a=p.parse_args()
    try:
        before=json.loads(a.before.read_text(encoding="utf-8-sig"))
        after=json.loads(a.after.read_text(encoding="utf-8-sig"))
        events=json.loads(a.event_keys.read_text(encoding="utf-8-sig"))
        out=classify(before,after,events)
        a.output.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf8")
        code=0
        print("D3E4_CLASSIFICATION_VERDICT="+out["verdict"])
        print("D3E4_UNATTRIBUTED_CHANGED_FILE_COUNT="+str(out["changed_identity_without_any_observed_4663_count"]))
        print("D3E4_UNEXPLAINED_MODIFIED_SIZE_CHANGED_COUNT="+str(out["unexplained_modified_size_changed_count"]))
        print("D3E4_UNEXPLAINED_MODIFIED_SAME_SIZE_FINGERPRINT_CHANGED_COUNT="+str(out["unexplained_modified_same_size_fingerprint_changed_count"]))
    except (OSError,UnicodeError,ValueError,TypeError,KeyError):
        print("D3E4_CLASSIFICATION_VERDICT=BLOCKED_INVALID_OR_MISSING_EVIDENCE")
        code=2
    print("D3E4_RAW_FILENAME_HASH_OR_PID_EXPORTED=false")
    print("D3E4_CAUSALITY_PROVEN=false")
    print("D3_STORAGE_ISOLATION=UNVERIFIED")
    print("CLINICAL_EDIT_ALLOWED=false")
    return code

if __name__=="__main__":raise SystemExit(main())
