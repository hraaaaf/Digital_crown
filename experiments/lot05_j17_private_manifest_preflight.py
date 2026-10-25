#!/usr/bin/env python3
"""J17 owner-private J16 manifest preflight: read-only, fail closed, no staging.

Never invoke this with a private manifest on public GitHub Actions.
Prints aggregate-only output. No original images, TXT labels or patient data read.
"""
from __future__ import annotations
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import sys
from lot05_j14_mixed_dentition_ontology_gate import gate_decision, classify_fdi

SCHEMA="digital-crown-lot05-j16-owner-private-migration-v1"
PIN="92e2cc3ae5eebc9de509311a3edefb7106fca7dd"
PERMANENT_KEYS=("active_permanent","primary_out_of_ontology","held_permanent",
                "superseded_permanent","pending_collision_adjudications",
                "resolved_collision_adjudications","exact_duplicate_deletions_pending_review",
                "unresolved","adjudication_history")
GATES=("geometry_verified","all_collisions_closed","primary_ontology_integrated",
       "patient_independence_proven","commercial_rights_cleared","staging_authorized",
       "training_authorized","clinical_use_authorized")

class PrivatePreflightError(ValueError): pass

def check(data:dict, original_bytes:bytes|None=None)->dict:
    if type(data) is not dict or data.get("schema")!=SCHEMA or data.get("source_commit")!=PIN:
        raise PrivatePreflightError("schema_or_source_pin")
    if data.get("source_reviewed_cases")!=28 or data.get("source_reviewed_pairs")!=6:
        raise PrivatePreflightError("review_census")
    if type(data.get("source_manifest_sha256")) is not str or len(data["source_manifest_sha256"])!=64:
        raise PrivatePreflightError("source_hash_missing")
    try: int(data["source_manifest_sha256"],16)
    except ValueError as exc: raise PrivatePreflightError("invalid_source_hash") from exc
    if original_bytes is not None and hashlib.sha256(original_bytes).hexdigest()!=data["source_manifest_sha256"]:
        raise PrivatePreflightError("source_manifest_integrity_mismatch")
    for k in PERMANENT_KEYS:
        if type(data.get(k)) is not list: raise PrivatePreflightError("missing_review_list")
    gates=data.get("release_gates")
    if type(gates) is not dict or set(gates)!=set(GATES) or any(type(v) is not bool for v in gates.values()):
        raise PrivatePreflightError("invalid_release_gates")
    if any(gates.values()): raise PrivatePreflightError("unapproved_release_gate")
    if data.get("staging_status")!="BLOCKED_NO_SOURCE_OR_LABEL_WRITES":
        raise PrivatePreflightError("staging_not_blocked")
    seen=set()
    for row in data["active_permanent"]:
        if type(row) is not dict or row.get("dentition")!="permanent" or row.get("clinical_status")!="confirmed" or row.get("staging_status")!="PENDING_PRIVATE_GEOMETRY_AND_COLLISION_QA":
            raise PrivatePreflightError("unsafe_active_record")
        d=row.get("decision")
        if type(d) is not dict or not {"case","split","stem","from_fdi","to_fdi","expected_bbox"}<=set(d):
            raise PrivatePreflightError("missing_permanent_witness")
        if classify_fdi(d["from_fdi"])!="permanent" or classify_fdi(d["to_fdi"])!="permanent" or d["from_fdi"]==d["to_fdi"]:
            raise PrivatePreflightError("invalid_permanent_relabel")
        if gate_decision({"fdi":d["to_fdi"],"clinical_status":"confirmed"})!="ELIGIBLE_FOR_LATER_PRIVATE_GEOMETRY_AND_COLLISION_QA":
            raise PrivatePreflightError("ontology_rejected")
        if d["split"] not in ("train","val","test") or type(d["stem"]) is not str or not d["stem"].isascii() or not d["stem"].isdecimal():
            raise PrivatePreflightError("invalid_source_identity")
        bbox=d["expected_bbox"]
        if type(bbox) is not list or len(bbox)!=4 or any(type(v) not in (int,float) or not 0<v<=1 for v in bbox):
            raise PrivatePreflightError("invalid_bbox")
        key=(d["split"],d["stem"],d["from_fdi"],tuple(bbox))
        if key in seen: raise PrivatePreflightError("duplicate_active_witness")
        seen.add(key)
    for row in data["primary_out_of_ontology"]:
        if type(row) is not dict or row.get("dentition")!="primary" or row.get("clinical_status") not in ("confirmed","tentative"):
            raise PrivatePreflightError("invalid_primary_review")
        d=row.get("decision")
        if type(d) is not dict or classify_fdi(d.get("clinician_fdi"))!="primary":
            raise PrivatePreflightError("invalid_primary_fdi")
        if gate_decision({"fdi":d["clinician_fdi"],"clinical_status":row["clinical_status"]})=="ELIGIBLE_FOR_LATER_PRIVATE_GEOMETRY_AND_COLLISION_QA":
            raise PrivatePreflightError("primary_coercion")
    return {"schema":"digital-crown-lot05-j17-private-manifest-preflight-v1",
            "status":"READ_ONLY_SCHEMA_AND_ONTOLOGY_PASS_STAGING_BLOCKED",
            "active_permanent_count":len(data["active_permanent"]),
            "primary_blocked_count":len(data["primary_out_of_ontology"]),
            "pending_collision_count":len(data["pending_collision_adjudications"]),
            "pending_dedupe_count":len(data["exact_duplicate_deletions_pending_review"]),
            "source_hash_verified":original_bytes is not None,
            "source_labels_read":False,"source_labels_modified":False,
            "private_geometry_verified":False,"staging_performed":False,
            "training_authorized":False,"clinical_use_authorized":False}

def main()->int:
    if os.environ.get("GITHUB_ACTIONS","").lower()=="true":
        print('{"status":"FAIL_CLOSED_PRIVATE_INPUT_FORBIDDEN_ON_PUBLIC_CI"}');return 1
    if len(sys.argv) not in (2,3):
        print('{"status":"FAIL_CLOSED_ARGUMENTS"}');return 1
    try:
        p=Path(sys.argv[1])
        if p.is_symlink() or not p.is_file() or p.stat().st_size>500000: raise PrivatePreflightError("unsafe_manifest")
        source=None
        if len(sys.argv)==3:
            src=Path(sys.argv[2])
            if src.is_symlink() or not src.is_file() or src.stat().st_size>500000: raise PrivatePreflightError("unsafe_source")
            source=src.read_bytes()
        report=check(json.loads(p.read_text(encoding="utf-8")),source)
        print(json.dumps(report,sort_keys=True));return 0
    except (ValueError,OSError,TypeError,KeyError):
        print('{"status":"FAIL_CLOSED_PRIVATE_VALIDATION"}');return 1

if __name__=="__main__":raise SystemExit(main())
