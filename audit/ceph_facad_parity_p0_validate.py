"""Fail-closed provenance checks for documentary Facad-to-Digital-Crown P0.

Does not run vendor software or certify clinical, numerical, or UX parity.
"""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "docs/audits/data/CEPH_FACAD_PARITY_P0_DESKTOP_EVIDENCE_MATRIX_2026-10-17.json"
MENU_NAMES = ("File", "Edit", "Tracing", "View", "Cephalometry", "Image", "Tools", "Window", "Help")
GROUPS = {"calibration_measure": 5, "planning_transform": 7, "tracing_construction": 6, "display": 4, "patient_session_document": 8}
BASE = "d36a921e4b910a84cbce305bd501a3d046cfbb62"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(data):
    require(data.get("schema") == "CEPH_FACAD_PARITY_P0_DESKTOP_EVIDENCE_MATRIX_V1", "schema drift")
    require(data.get("digital_crown_base_sha") == BASE, "baseline drift")
    require(data.get("vendor_product") == "Facad Quick Demo 3.14.1.1111", "vendor version drift")
    counts = data.get("count_claims", {})
    require([counts.get(x) for x in ("top_level_vendor_menus", "toolbar_ids", "desktop_workflows")] == [9, 30, 7], "inventory claim")
    menu = data.get("menus", [])
    require([x.get("name") for x in menu] == list(MENU_NAMES), "menu census")
    require([x.get("id") for x in menu] == ["FAC_MENU_%02d" % n for n in range(1, 10)], "menu ids")
    require(all(x.get("menu_leaf_functional_parity") == "NOT_PROVEN" and x.get("clinical_release") is False for x in menu), "menu false parity")
    bars = data.get("toolbar", [])
    require(len(bars) == 30 and len({x.get("id") for x in bars}) == 30, "toolbar census")
    require({k: sum(x.get("group") == k for x in bars) for k in GROUPS} == GROUPS, "toolbar groups")
    for x in bars:
        require(x.get("id", "").startswith("FCD_"), "vendor control identity")
        require(x.get("vendor_action_verdict") == "NOT_YET_TESTED", "vendor action not observed")
        require(x.get("facad_to_dc_equivalence_verified") is False and x.get("numeric_parity_verified") is False and x.get("clinical_release") is False, "false parity")
        path = x.get("digital_crown_code_path")
        if path:
            require(x.get("digital_crown_status") == "CODE_SURFACE_IDENTIFIED_NOT_PARITY", "mislabelled code surface")
            require(path.startswith("frontend/src/features/ortho/") and ".." not in path, "invalid path")
            file = ROOT / path
            require(file.is_file(), "missing code file")
            needle = x.get("digital_crown_source_needle")
            require(isinstance(needle, str) and needle in file.read_text(encoding="utf-8"), "missing code symbol")
            require(x.get("digital_crown_code_url") == "https://github.com/hraaaaf/Digital_crown/blob/" + BASE + "/" + path, "code URL drift")
        else:
            require(x.get("digital_crown_status") == "NOT_PROVEN" and x.get("digital_crown_source_needle") is None, "unsupported mapping")
    require(sum(bool(x.get("digital_crown_code_path")) for x in bars) == 9, "mapped code count")
    flows = data.get("workflows", [])
    require([x.get("id") for x in flows] == ["WF_%02d" % n for n in range(1, 8)], "workflow census")
    for x in flows:
        require(x.get("facad_to_dc_action_parity_verified") is False and x.get("clinical_release") is False, "workflow false parity")
        require(x.get("comparison_viewports") == ["1280x900", "1600x1000"], "desktop scope drift")
        require(x.get("required_evidence") == ["FACAD_BEFORE_AFTER_AUTHORIZED", "DC_AUTHENTICATED_BEFORE_AFTER", "COMMON_NONPATIENT_FIXTURE", "RESTORE_PROOF_WHERE_MUTABLE"], "evidence standard")
        require(x.get("dc_code_paths") and all((ROOT / path).is_file() for path in x["dc_code_paths"]), "workflow code paths")
    require(flows[3].get("state") == "PROVEN_DC_UI_COMPLETENESS_GAP" and flows[3].get("priority") == "P0", "WF04 blocker lost")
    gates = data.get("gates", {})
    require(all(gates.get(k) is False for k in ("shared_vendor_storage_isolation_verified", "vendor_numeric_parity_verified", "dc_runtime_action_parity_verified", "clinical_go", "merge_authorized", "deployment_authorized", "cephalo_mobile_this_release")), "unsafe gate")
    require(gates.get("vendor_patient_calculations_compared") == 0, "vendor clinical oracle falsely claimed")
    return {"menus": 9, "toolbar": 30, "workflows": 7, "code_candidates": 9, "clinical_release": False}


def negative_checks(data):
    edits = [
        lambda d: d["menus"].pop(),
        lambda d: d["toolbar"].pop(),
        lambda d: d["toolbar"][0].update({"facad_to_dc_equivalence_verified": True}),
        lambda d: d["toolbar"][0].update({"vendor_action_verdict": "TESTED"}),
        lambda d: d["toolbar"][0].update({"digital_crown_source_needle": "NOT_A_CODE_SYMBOL"}),
        lambda d: d["workflows"][3].update({"state": "DC_CODE_SURFACE_ONLY"}),
        lambda d: d["gates"].update({"clinical_go": True}),
        lambda d: d["gates"].update({"shared_vendor_storage_isolation_verified": True}),
        lambda d: d["gates"].update({"vendor_patient_calculations_compared": 1}),
        lambda d: d["workflows"][0].update({"comparison_viewports": ["390x844"]}),
        lambda d: d.update({"digital_crown_base_sha": "bad"}),
    ]
    for index, mutate in enumerate(edits, 1):
        corrupted = copy.deepcopy(data)
        mutate(corrupted)
        try:
            validate(corrupted)
        except ValueError:
            continue
        raise AssertionError("Negative mutant %d passed" % index)
    return len(edits)


if __name__ == "__main__":
    payload = json.loads(MATRIX.read_text(encoding="utf-8"))
    print(json.dumps({"validation": validate(payload), "negative_mutants_rejected": negative_checks(payload)}, sort_keys=True))
