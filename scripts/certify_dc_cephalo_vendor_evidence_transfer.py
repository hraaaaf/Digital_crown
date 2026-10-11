#!/usr/bin/env python3
"""DC Céphalo: certify that existing vendor evidence cannot silently become clinical authority.

Read-only, source-only. No FACAD process, license, browser, network, patient, DB, or
production runtime access. This is not a scientific/numeric comparison test.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "docs/audits/DC_CEPHALO_FACAD_EVIDENCE_TRANSFER_V1.json"
ALLOWED_SOURCE_PATHS = {
    "dc_executable_measurements": "docs/audits/schemas/cephalo_vnext_lot06_executable_measurement_contract_v1.json",
    "facad_ricketts_direct_parity": "docs/audits/schemas/ortho_lot08_facad_ricketts_direct_parity_evidence_v1.json",
    "facad_compatibility_backlog": "docs/audits/schemas/ortho_lot08_facad_dc_unmapped_backlog_v1.json",
    "source_locked_protocol_mapping": "docs/audits/schemas/ortho_lot08_facad_dc_existing_protocol_mapping_v1.json",
    "ricketts32_closeout": "docs/handovers/2026-10-07-ricketts32-compatibility-closeout.md",
}
ORDER = ["DC-CEPH-01", "DC-CEPH-02", "DC-CEPH-03", "DC-CEPH-04", "DC-CEPH-05"]


class TransferGateError(ValueError):
    """A claimed FACAD-to-DC transfer fact conflicts with source or safety boundary."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise TransferGateError(code)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def verify(manifest: dict, measures: dict, parity: dict, backlog: dict, mapping: dict, closeout: str) -> dict:
    require(manifest.get("schema_version") == "DC_CEPHALO_VENDOR_EVIDENCE_TRANSFER_V1", "SCHEMA")
    require(manifest.get("decision") == "DC_FIRST__VENDOR_NEW_RUNS_PAUSED", "VENDOR_PAUSE")
    require(manifest.get("applies_to") == "DIGITAL_CROWN_CEPHALO", "SCOPE")
    require(manifest.get("evidence_only") is True, "EVIDENCE_ONLY")
    require(manifest.get("validation_status") == "PROVISIONAL_SOURCE_ONLY", "NO_SCIENTIFIC_APPROVAL")
    for key in (
        "facad_new_executions_allowed",
        "facad_trial_license_reuse_claimed",
        "clinical_parity_certified",
        "numeric_parity_certified",
        "vendor_norms_authoritative",
        "vendor_label_is_direct_alias",
        "clinical_activation_authorized_by_transfer",
        "patient_data_required_for_transfer",
        "production_data_access",
        "merge_authorized",
        "vercel_deployment_authorized",
    ):
        require(manifest.get(key) is False, "NO_VENDOR_OR_CLINICAL_PROMOTION_" + key.upper())
    require(manifest.get("gate_overrides_forbidden") is True, "GATES_FAIL_CLOSED")
    require(manifest.get("scientific_claims_source") ==
            "INDEPENDENT_DENTAL_SCIENTIFIC_SOURCES_AND_DC_CONTRACTS_ONLY", "SCIENTIFIC_AUTHORITY")
    source = manifest.get("data_sources", {})
    require(isinstance(source, dict) and set(source) == set(ALLOWED_SOURCE_PATHS), "EXACT_SOURCE_MANIFEST")
    for key, path in ALLOWED_SOURCE_PATHS.items():
        require(source.get(key, {}).get("path") == path, "SOURCE_PATH_" + key.upper())

    dc = source["dc_executable_measurements"]
    require(measures.get("schema_version") == "CEPHALO_LOT06_EXECUTABLE_MEASUREMENT_CONTRACT_V1", "DC_SCHEMA")
    require(measures.get("status") == "EXECUTABLE_38_CANONICAL_MEASUREMENTS", "DC_CONTRACT_STATUS")
    require(measures.get("clinical_interpretation") is False, "DC_NO_DIAGNOSIS")
    items = measures.get("measurements", [])
    require(isinstance(items, list) and len(items) == 38 and dc.get("declared_measurement_count") == 38,
            "DC_EXACT_MEASUREMENTS")
    ids = [m.get("measurement_id") for m in items]
    require(all(isinstance(i, str) and i.startswith("M_") for i in ids)
            and len(set(ids)) == 38, "DC_UNIQUE_CANONICAL_IDS")
    require(all(m.get("availability_gate") and m.get("required_landmarks") is not None
                and isinstance(m.get("source_contracts"), list)
                and m.get("source_contracts") for m in items), "DC_DEPENDENCY_SOURCE_GATES")
    require(dc.get("clinical_interpretation_expected") is False, "DC_MANIFEST_CLINICAL_GATE")

    facad = source["facad_ricketts_direct_parity"]
    require(parity.get("schema_version") == "ORTHO_LOT08_FACAD_RICKETTS_DIRECT_PARITY_EVIDENCE_V1",
            "PARITY_SCHEMA")
    require(parity.get("scientific_authority") is False
            and parity.get("compatibility_only") is True, "VENDOR_NOT_AUTHORITY")
    require(parity.get("status") == "DIRECT_DEFINITION_OBSERVED"
            and facad.get("status_expected") == "DIRECT_DEFINITION_OBSERVED", "VENDOR_DEFINITION_ONLY")
    require(parity.get("evidence_records") == []
            and facad.get("expected_evidence_records") == 0, "NO_DIRECT_EXPORTS")
    require(parity.get("parity_rows") == []
            and facad.get("expected_parity_rows") == 0, "NO_NUMERIC_PARITY")
    labels = [x.get("vendor_label") for x in parity.get("profiles", [])]
    expected = ["Ricketts (32 F)", "Ricketts (13 F)"]
    require(labels == expected and facad.get("profiles_expected_unobserved") == expected,
            "EXACT_VENDOR_TARGET_PROFILES")
    require(all(x.get("observation_status") == "UNOBSERVED" for x in parity["profiles"]),
            "VENDOR_SAME_TRACE_UNOBSERVED")

    gaps = source["facad_compatibility_backlog"]
    require(backlog.get("schema_version") == "FACAD_DC_UNMAPPED_BACKLOG_V1", "COMPAT_SCHEMA")
    require(backlog.get("totals", {}).get("profiles") == 5
            and gaps.get("expected_profiles") == 5, "FIVE_COMPAT_PROFILES")
    require(backlog.get("totals", {}).get("unmapped_items") == 0
            and gaps.get("expected_remaining_unmapped") == 0, "COMPAT_DISPOSITION_NOT_EMPTY")
    require(all(v.get("unmapped") == [] for v in backlog.get("profiles", {}).values())
            and len(backlog.get("profiles", {})) == 5, "COMPAT_SOURCE_UNMAPPED")
    require(len(backlog["profiles"]["Ricketts (32 F)"].get("resolved_items", [])) == 26,
            "COMPAT_RICKETTS_26_DECISIONS")
    require(gaps.get("decision_not_direct_alias") is True, "COMPAT_DISPOSITION_NOT_ALIAS")

    require(mapping.get("schema_version") == "FACAD_DC_PROTOCOL_MAPPING_V1", "MAPPING_SCHEMA")
    rules = mapping.get("rules", {})
    require(all(rules.get(k) is True for k in (
        "exact_label_match_is_not_sufficient_for_geometry_equivalence",
        "facad_norms_are_reference_only_not_runtime_authority",
        "direct_match_requires_existing_dc_canonical_id_and_same_declared_construction",
    )), "MAPPING_PROVENANCE_GATES")
    require(source["source_locked_protocol_mapping"].get("must_not_infer_equivalence_from_labels") is True,
            "LABEL_MATCH_NOT_EQUIVALENCE")

    c = source["ricketts32_closeout"]
    require(c.get("prior_unmapped") == 26 and c.get("dispositioned") == 26
            and c.get("scientific_parity_certified") is False, "RICKETTS_CLOSEOUT_SCOPE")
    require("26/26" in closeout
            and "It does **not** mean:" in closeout
            and "It does **not** mean:\n- 26 direct runtime aliases;\n- Facad norms are authoritative;" in closeout, "HANDOVER_EVIDENCE_BOUNDARY")
    flows = manifest.get("delivery_sequence", [])
    require(isinstance(flows, list) and [a.get("id") for a in flows] == ORDER, "DC_SEQUENCE")
    require(flows[0].get("status") == "IN_PROGRESS_EVIDENCE_GATE"
            and flows[0].get("runtime_change_allowed") is False, "DC_INITIAL_SOURCE_ONLY")
    require(flows[1].get("runtime_change_requires_scientific_review") is True, "DC_SCIENTIFIC_REVIEW")
    require(flows[2].get("visual_before_after_required") is True
            and flows[2].get("clinical_parity_claim_allowed") is False, "DC_VISUAL_PROOF")
    require(flows[3].get("patient_data_forbidden_in_tests") is True, "DC_REPORT_PRIVACY")
    require(flows[4].get("status") == "PARKED_EXTERNAL_VENDOR_DEPENDENCY"
            and flows[4].get("needs_same_trace_evidence") is True, "VENDOR_PARITY_PARKED")
    return {
        "schema": "DC_CEPH_TRANSFER_CERTIFICATION_V1",
        "status": "SOURCE_BOUNDARY_PASS_ONLY",
        "dc_measurement_contract_count": len(items),
        "facad_compatibility_dispositions_ricketts32": 26,
        "vendor_direct_evidence_records": 0,
        "vendor_direct_parity_rows": 0,
        "vendor_same_trace_observed": False,
        "scientific_authority_promoted": False,
        "facad_new_executions": 0,
        "clinical_activation": False,
        "patient_access": False,
        "next": ORDER[1],
    }


def self_test(args: tuple[dict, dict, dict, dict, dict, str]) -> int:
    # Every poison attempt must be rejected by the *same* validator.
    poisoned = [
        (0, lambda d: d.__setitem__("vendor_norms_authoritative", True)),
        (0, lambda d: d.__setitem__("numeric_parity_certified", True)),
        (0, lambda d: d.__setitem__("facad_new_executions_allowed", True)),
        (0, lambda d: d["data_sources"]["facad_ricketts_direct_parity"].__setitem__("expected_parity_rows", 1)),
        (0, lambda d: d["delivery_sequence"][4].__setitem__("status", "CLOSED")),
        (1, lambda d: d["measurements"][0].__setitem__("availability_gate", "")),
        (1, lambda d: d.__setitem__("clinical_interpretation", True)),
        (2, lambda d: d["profiles"][0].__setitem__("observation_status", "OBSERVED")),
        (2, lambda d: d["parity_rows"].append({"unverified": True})),
        (3, lambda d: d["totals"].__setitem__("unmapped_items", 1)),
        (4, lambda d: d["rules"].__setitem__("facad_norms_are_reference_only_not_runtime_authority", False)),
    ]
    for i, (which, mutate) in enumerate(poisoned):
        inputs = copy.deepcopy(args)
        mutate(inputs[which])
        try:
            verify(*inputs)
        except TransferGateError:
            continue
        raise TransferGateError("MUTATION_NOT_REJECTED_" + str(i))
    return len(poisoned)


def main() -> None:
    sources = {name: ROOT / path for name, path in ALLOWED_SOURCE_PATHS.items()}
    args = (
        read_json(ROOT / MANIFEST),
        read_json(sources["dc_executable_measurements"]),
        read_json(sources["facad_ricketts_direct_parity"]),
        read_json(sources["facad_compatibility_backlog"]),
        read_json(sources["source_locked_protocol_mapping"]),
        sources["ricketts32_closeout"].read_text(encoding="utf-8"),
    )
    result = verify(*args)
    result["mutation_negative_controls_passed"] = self_test(args)
    assert result["mutation_negative_controls_passed"] == 11
    # No untrusted content or per-patient data in output.
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
