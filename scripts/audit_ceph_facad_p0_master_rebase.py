#!/usr/bin/env python3
"""CEPH-FAC-PARITY-P0: static SOURCE-ONLY rebase, not desktop/vendor parity.

Reads the frozen #934 matrix and exactly pinned MASTER commit Git blobs.
No vendor startup, patient content, network calls, inference, clinical actions,
checkbox updates, or repository mutations (apart from output artifacts).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "docs/audits/data/CEPH_FACAD_PARITY_P0_DESKTOP_EVIDENCE_MATRIX_2026-10-17.json"
MATRIX_BLOB = "47627d155edf05cea941a9e847a9a76460b281bc"
OLD_MASTER = "d36a921e4b910a84cbce305bd501a3d046cfbb62"
PINNED_MASTER = "372c236610b3b621c708be9bc0a0141dfe66c494"
SCHEMA = "CEPH_FAC_P0_EXACT_MASTER_STATIC_REBASE_V1"
SOURCE_BLOBS = {
    "frontend/src/features/ortho/components/Step1CephaloBase.tsx": "141ff985c500f2dbefffac1106feb55f96a856e1",
    "frontend/src/features/ortho/components/Step1Cephalo.tsx": "d70bf18ede01789b1068c63795951a218b9f0618",
    "frontend/src/features/ortho/CephaloTracingLayerBase.tsx": "3786e95b27d0992a76d0cc62bf4a6481ca6a7884",
    "frontend/src/features/ortho/CephaloWorkspace.tsx": "54aa6aa1500734608f2f95a2b4ea42b530553026",
    "frontend/src/features/ortho/orthoLandmarkEditHistory.ts": "0c33ad6090449178a6322d7285be522caecc9d0d",
    "frontend/src/features/ortho/CephaloHistory.tsx": "9689dc2336b0f3a46c368f265e0cf0507704617f",
    "frontend/src/features/ortho/components/CephaloAnalysisWorkbenchPanel.tsx": "1047151ca8a31f671f1b05206859e02d6e6ae75b",
    "frontend/src/features/ortho/orthoLayerRegistry.ts": "0597b006bb8c0a093a0563e12c1ad1fe676720a8",
    "frontend/src/features/ortho/components/Step4Documents.tsx": "3e357387fa3b67a972a4ab3a9863ee3ff8667cfc",
    "backend/services/cephalo_runtime_chain.py": "2d35d68173e0b3571e88a045ce3722b4cdd98a5a",
}
REQUIRED_EVIDENCE = {
    "FACAD_BEFORE_AFTER_AUTHORIZED",
    "DC_AUTHENTICATED_BEFORE_AFTER",
    "COMMON_NONPATIENT_FIXTURE",
    "RESTORE_PROOF_WHERE_MUTABLE",
}

class AuditError(ValueError):
    pass

def _git(*args: str) -> str:
    p = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False)
    if p.returncode:
        raise AuditError(f"git command failed {args[0]}: {p.stderr[:200]}")
    return p.stdout.strip() if args[0] == "rev-parse" else p.stdout

def get_frozen_source_blobs(master_sha: str = PINNED_MASTER) -> dict[str, str]:
    if master_sha != PINNED_MASTER:
        raise AuditError("master SHA is not the independently pinned baseline")
    actual = _git("rev-parse", f"{master_sha}^{{commit}}")
    if actual != master_sha:
        raise AuditError("missing pinned master Git commit")
    sources: dict[str, str] = {}
    for path, expected in SOURCE_BLOBS.items():
        if not re.fullmatch(r"[a-zA-Z0-9_./-]+", path) or ".." in Path(path).parts:
            raise AuditError("unsafe path")
        blob = _git("rev-parse", f"{master_sha}:{path}")
        if blob != expected:
            raise AuditError(f"pinned master source drift: {path}")
        sources[path] = _git("show", f"{master_sha}:{path}")
    return sources

def examine(matrix: dict, sources: dict[str, str]) -> dict:
    if matrix.get("schema") != "CEPH_FACAD_PARITY_P0_DESKTOP_EVIDENCE_MATRIX_V1":
        raise AuditError("unknown parent matrix schema")
    if matrix.get("digital_crown_base_sha") != OLD_MASTER:
        raise AuditError("wrong 2026-10-17 master baseline")
    if len(matrix.get("menus", [])) != 9 or len(matrix.get("toolbar", [])) != 30 or len(matrix.get("workflows", [])) != 7:
        raise AuditError("9/30/7 cardinality drift")
    if len({x["id"] for x in matrix["menus"]}) != 9:
        raise AuditError("duplicate menu ID")
    if len({x["id"] for x in matrix["toolbar"]}) != 30:
        raise AuditError("duplicate toolbar ID")
    if len({x["id"] for x in matrix["workflows"]}) != 7:
        raise AuditError("duplicate workflow ID")
    if not sources or set(sources) != set(SOURCE_BLOBS):
        raise AuditError("incomplete original-source baseline")
    if any(v is False for v in [
        not matrix["gates"]["clinical_go"],
        not matrix["gates"]["facad_dc_action_parity_verified"] if "facad_dc_action_parity_verified" in matrix["gates"] else True,
        not matrix["gates"]["deployment_authorized"],
        not matrix["gates"]["merge_authorized"],
        not matrix["gates"]["vendor_numeric_parity_verified"],
        not matrix["gates"]["shared_vendor_storage_isolation_verified"],
    ]):
        raise AuditError("source parent matrix safety state changed")

    commands = []
    for entry in matrix["toolbar"]:
        id_ = entry["id"]
        path = entry["digital_crown_code_path"]
        needle = entry["digital_crown_source_needle"]
        if entry["vendor_action_verdict"] != "NOT_YET_TESTED" or entry["facad_to_dc_equivalence_verified"] is not False:
            raise AuditError("vendor action/parity unverified contract mutated: " + id_)
        if entry["clinical_release"] is not False or entry["numeric_parity_verified"] is not False:
            raise AuditError("clinical/numeric false promotion: " + id_)
        has_previous_pointer = (path is not None or needle is not None)
        if (path is None) != (needle is None):
            raise AuditError("orphan path/needle evidence")
        if has_previous_pointer:
            if path not in sources:
                raise AuditError("code path not included in pinned snapshot: " + str(path))
            static_match = needle in sources[path]
            # If previously matched parent source disappears, do not label as PASS.
            status = "PARTIAL" if static_match else "NOT_PROVEN"
            observation = "MATCHED_CODE_STRING_ONLY" if static_match else "SOURCE_NEEDLE_MISSING"
        else:
            status, observation = "NOT_PROVEN", "NOT_TESTED_IN_ORIGINAL_SOURCE_SLICE"
        commands.append({
            "vendor_toolbar_id": id_,
            "group": entry["group"],
            "priority": entry["priority"],
            "source_status": status,
            "parity_status": "NOT_PROVEN",
            "master_evidence": {
                "path": path, "needle": needle,
                "git_blob_sha1": SOURCE_BLOBS[path] if path else None,
                "inspection": observation,
            },
            "vendor_action_tested": False,
            "vendor_mutation_gate": ("BLOCKED" if entry["vendor_side_effect_gate"] == "D3_AND_RIGHTS_REQUIRED_FOR_MUTATION" else "NOT_TESTED"),
            "clinical_go": False,
        })

    valid_controls = {x["id"] for x in matrix["toolbar"]}
    workflows = []
    for wf in matrix["workflows"]:
        path_list = wf.get("dc_code_paths", [])
        if not path_list or len(set(path_list)) != len(path_list):
            raise AuditError("invalid workflow paths: " + wf["id"])
        if any(path not in sources for path in path_list):
            raise AuditError("workflow references unpinned source: " + wf["id"])
        if set(wf["required_evidence"]) != REQUIRED_EVIDENCE:
            raise AuditError("required same-case desktop/user evidence changed")
        if not set(wf["facad_controls"]).issubset(valid_controls):
            raise AuditError("unknown vendor control")
        if wf["facad_to_dc_action_parity_verified"] is not False or wf["clinical_release"] is not False:
            raise AuditError("unsupported workflow promotion")
        workflows.append({
            "workflow_id": wf["id"], "title": wf["title"], "priority": wf["priority"],
            "source_status": "PARTIAL",
            "parity_status": "NOT_PROVEN",
            "source_path_count": len(path_list),
            "master_paths_with_blobs": [{"path": p, "git_blob_sha1": SOURCE_BLOBS[p]} for p in path_list],
            "historical_assessment": wf["state"],
            "missing_required_evidence": sorted(REQUIRED_EVIDENCE),
            "clinical_go": False,
        })

    runtime = sources["backend/services/cephalo_runtime_chain.py"]
    named_profiles = {
        "steiner": '"steiner": project_steiner_static_protocol(' in runtime,
        "tweed_merrifield": '"tweed_merrifield": project_tweed_merrifield_protocol(' in runtime,
    }
    if not all(named_profiles.values()):
        raise AuditError("active master projection no longer matches explicit source")
    return {
        "schema": SCHEMA,
        "parent_matrix_blob_sha1": MATRIX_BLOB,
        "parent_pr": 934,
        "source_parent_master_sha": OLD_MASTER,
        "reconciled_master_sha": PINNED_MASTER,
        "counts": {
            "vendor_menus_documented": len(matrix["menus"]),
            "vendor_menu_action_parity_verified": 0,
            "toolbar_total": len(commands),
            "toolbar_code_string_matched_only": sum(x["source_status"] == "PARTIAL" for x in commands),
            "toolbar_not_proven": sum(x["source_status"] == "NOT_PROVEN" for x in commands),
            "toolbar_vendor_actions_verified": 0,
            "workflow_total": len(workflows),
            "workflow_source_paths_present": len(workflows),
            "workflow_e2e_parity_verified": 0,
        },
        "menus": [{"id": m["id"], "name": m["name"], "parity_status": "NOT_PROVEN"} for m in matrix["menus"]],
        "toolbar": commands,
        "workflows": workflows,
        "master_protocol_profiles_confirmed_in_runtime_chain": named_profiles,
        "evidence_class": "STATIC_SOURCE_POINTER_REBASE_ONLY",
        "source_presence_not_vendor_equivalence": True,
        "clinical_measurements_compared": 0,
        "facad_storage_isolation": "UNVERIFIED",
        "clinical_go": False,
        "merge_authorized": False,
        "deployment_authorized": False,
        "roadmap_before": "41/99",
        "roadmap_after": "41/99",
        "required_for_42": "ACTUAL_CANONICAL_ITEM_CLOSEOUT_WITH_FULL_GATES",
        "next": "DC_AUTHENTICATED_SYNTHETIC_E2E_THEN_AUTHORIZED_FACAD_SAME_CASE_AND_VENDOR_D3",
    }

def render_md(report: dict) -> str:
    c = report["counts"]
    return "\n".join([
        "# CEPH-FAC-PARITY-P0 — master snapshot static rebase",
        "",
        "**No vendor runtime and no patient data. Source-only, CLINICAL NO-GO.**",
        f"Master pinned: `{report['reconciled_master_sha']}`",
        f"Parent #934 baseline: `{report['source_parent_master_sha']}`",
        f"Menus recorded: {c['vendor_menus_documented']}, with ZERO tested vendor menu actions.",
        f"Toolbar: {c['toolbar_code_string_matched_only']}/{c['toolbar_total']} earlier code needles still present;",
        f"{c['toolbar_not_proven']} NOT_PROVEN (absence of pointer is NOT proof of missing functionality).",
        f"Workflows: {c['workflow_source_paths_present']}/{c['workflow_total']} related source paths present;",
        "zero Facad/DC comparable same-case executions proven.",
        "Active master source contains Steiner and Tweed-Merrifield runtime projection keys;",
        "other protocol completeness is NOT PROVEN by these observations.",
        "FACAD D3 source writes and license remain blocked, as do numeric/clinical parity.",
        "**Roadmap stays 41/99 (CEPH 20/60 + FAC 21/39): no top-level checkbox promoted.**",
        "",
        "## Decisive follow-on",
        "1. Authorize/use isolated synthetic account E2E for DC workflow input → calibration",
        "   → editor correction → analysis row completeness → layer → PDF with source provenance.",
        "2. Require authorized non-patient SAME-case vendor desktop evidence, comparable UI states,",
        "   restore checks and D3/rights before claiming Facad parity.",
        "3. Review exact-head CI and independent science/security/QA findings before canonical",
        "   checklist closeout. Never promote SRPose38 detector clinical quality.",
        "",
    ])

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--output-dir", type=Path, default=ROOT / "artifacts/ceph-fac-p0-master-rebase")
    args = p.parse_args()
    if _git("rev-parse", f"HEAD:{MATRIX.relative_to(ROOT)}") != MATRIX_BLOB:
        raise AuditError("parent matrix blob silently changed")
    m = json.loads(MATRIX.read_text(encoding="utf-8"))
    report = examine(m, get_frozen_source_blobs())
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (args.output_dir / "README.md").write_text(render_md(report), encoding="utf-8")
    c = report["counts"]
    print(json.dumps({"result": "P0_MASTER_STATIC_REBASE_ONLY__NO_CLINICAL_GO", "menu": c["vendor_menus_documented"], "code_needle": c["toolbar_code_string_matched_only"], "code_not_proven": c["toolbar_not_proven"], "workflows_source_only": c["workflow_source_paths_present"], "e2e_vendor_parity": 0, "roadmap": "41/99"}, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
