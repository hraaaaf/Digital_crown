#!/usr/bin/env python3
"""D3E.20 decision-record integrity ONLY. NO guest/Hyper-V/file collection."""
import argparse
import json
from pathlib import Path

REQUIRED_FIELDS = {
  "schema": "facad314_d3e20_internal_dual_review_v1",
  "phase": "SOURCE_ONLY_REVIEW",
  "review_target_sha": "9f01a3fb7dfe37344e34530fe20d6c6661325342",
  "reviewer_claim": "TWO_INTERNAL_ADVERSARIAL_LENSES_NO_EXTERNAL_INDEPENDENCE",
  "decision": "NO_GO_NATIVE_EXECUTION",
  "rationale": "OPEN_BLOCKERS_AND_ABSENT_NATIVE_OR_INDEPENDENT_EVIDENCE",
  "document_path": "docs/audits/FACAD_314_D3E20_SECURITY_SCIENCE_REVIEW_2026-10-10.md",
  "security_design_score_10": 6,
  "security_native_proof_score_10": 0,
  "science_design_score_10": 5,
  "science_native_proof_score_10": 0
}
FINDING_ORACLE = {
  "SEC-01": {
    "domain": "SECURITY",
    "severity": "BLOCKER",
    "issue": "OFFICIAL_PACKAGE_AND_NONCLINICAL_SAMPLE_PROVENANCE_UNVERIFIED"
  },
  "SEC-02": {
    "domain": "SECURITY",
    "severity": "BLOCKER",
    "issue": "HYPERV_HOST_GUEST_RUNTIME_BOUNDARIES_UNVERIFIED"
  },
  "SEC-03": {
    "domain": "SECURITY",
    "severity": "BLOCKER",
    "issue": "NO_APPROVED_MINIMIZED_EGRESS_OR_INDEPENDENT_PROOF"
  },
  "SEC-04": {
    "domain": "SECURITY",
    "severity": "MAJOR",
    "issue": "HOST_ADMIN_HYPERV_AND_ISO_TRUST_BASE_UNASSESSED"
  },
  "SEC-05": {
    "domain": "SECURITY",
    "severity": "MAJOR",
    "issue": "VHD_CHECKPOINT_MEDIA_AND_TRACE_DISPOSAL_UNPROVEN"
  },
  "SCI-01": {
    "domain": "SCIENCE",
    "severity": "BLOCKER",
    "issue": "REAL_ILEXIS_WRITER_AND_COMPLETION_UNPROVEN"
  },
  "SCI-02": {
    "domain": "SCIENCE",
    "severity": "BLOCKER",
    "issue": "GUEST_WIDE_ETW_COVERAGE_AND_LOSS_UNPROVEN"
  },
  "SCI-03": {
    "domain": "SCIENCE",
    "severity": "BLOCKER",
    "issue": "INDEPENDENT_HUMAN_REVIEWS_SAME_HEAD_MISSING"
  },
  "SCI-04": {
    "domain": "SCIENCE",
    "severity": "MAJOR",
    "issue": "NUMERIC_PARITY_ORACLE_AND_EDITOR_EQUIVALENCE_UNPROVEN"
  },
  "SCI-05": {
    "domain": "SCIENCE",
    "severity": "MAJOR",
    "issue": "CONTROL_ARMS_AND_SAMPLE_IDENTITY_UNVALIDATED"
  }
}
UNPROVEN = set([
  "external_privacy_reviewer_verified",
  "external_scientific_reviewer_verified",
  "same_exact_head_external_reviews_verified",
  "privacy_blockers_cleared",
  "science_blockers_cleared",
  "official_demo_and_license_verified",
  "host_guest_channel_confinement_verified",
  "approved_egress_protocol_verified",
  "source_scoped_attribution_verified",
  "event_completeness_verified",
  "native_experiment_separately_authorized",
  "native_vm_or_iso_operated",
  "facad_or_ilexis_executed",
  "raw_etw_captured_or_exported",
  "clinical_edit_allowed",
  "shared_app_storage_isolation_verified",
  "converged",
  "merge_or_deploy_authorized"
])
MAX_BYTES = 18000

class ReviewBlocked(ValueError):
    pass

def unique_pairs(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ReviewBlocked("DUPLICATE_JSON_KEY")
        obj[key] = value
    return obj

def evaluate(data):
    if not isinstance(data,dict) or set(data)!=set(REQUIRED_FIELDS)|UNPROVEN|{"findings"}:
        raise ReviewBlocked("REVIEW_SCHEMA_INVALID")
    for k,v in REQUIRED_FIELDS.items():
        if type(data[k]) is not type(v) or data[k]!=v:
            raise ReviewBlocked("REVIEW_BOUNDARY_FORGED")
    for k in UNPROVEN:
        if data[k] is not False:
            raise ReviewBlocked("REVIEW_UNVERIFIED_CLAIM")
    findings=data["findings"]
    if not isinstance(findings,list) or len(findings)!=len(FINDING_ORACLE):
        raise ReviewBlocked("FINDING_MATRIX_INVALID")
    seen=set()
    for f in findings:
        if not isinstance(f,dict) or set(f)!={"id","domain","severity","status","issue"}:
            raise ReviewBlocked("FINDING_STRUCTURE_INVALID")
        id=f["id"]
        if type(id) is not str or id in seen or id not in FINDING_ORACLE:
            raise ReviewBlocked("FINDING_ID_INVALID")
        seen.add(id)
        if (type(f["status"]) is not str or f["status"]!="OPEN"
                or any(type(f[k]) is not str or f[k]!=v
                       for k,v in FINDING_ORACLE[id].items())):
            raise ReviewBlocked("FINDING_CLAIM_INVALID")
    if seen!=set(FINDING_ORACLE):
        raise ReviewBlocked("FINDINGS_MISSING")
    return {"result":"D3E20_INTERNAL_REVIEW_RECORDED_NATIVE_NO_GO",
            "issues_open":len(FINDING_ORACLE),
            "blockers_open":sum(v["severity"]=="BLOCKER" for v in FINDING_ORACLE.values()),
            "actual_independent_reviewers":0,
            "native_execution":False,"clinical_edit":False}

def load(path):
    if not path.is_file() or path.stat().st_size>MAX_BYTES:
        raise ReviewBlocked("FILE_MISSING_OR_LARGE")
    raw=path.read_bytes()
    if raw.startswith(bytes([239,187,191])) or bytes([0]) in raw:
        raise ReviewBlocked("INVALID_ENCODING")
    return json.loads(raw.decode("utf-8"),object_pairs_hook=unique_pairs)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decision",required=True,type=Path)
    args=parser.parse_args()
    try:
        out=evaluate(load(args.decision))
        print("D3E20_VERDICT="+out["result"])
        print("D3E20_BLOCKERS_OPEN="+str(out["blockers_open"]))
        print("D3E20_MAJOR_OPEN="+str(out["issues_open"]-out["blockers_open"]))
        return 0
    except (ReviewBlocked,ValueError,TypeError,OSError,UnicodeError,KeyError):
        print("D3E20_VERDICT=BLOCKED_INVALID_OR_FORGED_REVIEW")
        return 2
    finally:
        print("D3E20_EXTERNAL_INDEPENDENT_REVIEWERS=0")
        print("D3E20_NATIVE_CAPTURE_AUTHORIZED=false")
        print("FAC03_D3=OPEN_RED")
        print("SHARED_APP_STORAGE_ISOLATION=UNVERIFIED")
        print("CLINICAL_EDIT_ALLOWED=false")
        print("CONVERGED=false")

if __name__=="__main__":
    raise SystemExit(main())
