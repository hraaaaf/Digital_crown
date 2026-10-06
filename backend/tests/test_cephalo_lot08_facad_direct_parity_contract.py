import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGETS = ROOT / "docs" / "audits" / "schemas" / "ortho_lot08_facad_ricketts_compatibility_targets_v1.json"
EVIDENCE = ROOT / "docs" / "audits" / "schemas" / "ortho_lot08_facad_ricketts_direct_parity_evidence_v1.json"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_facad_parity_remains_unobserved_without_direct_exports():
    targets = _load(TARGETS)
    evidence = _load(EVIDENCE)

    assert targets["status"] == "PARITY_TARGETS_ONLY__MEMBERSHIP_NOT_DIRECTLY_OBSERVED"
    assert evidence["status"] == "AWAITING_DIRECT_FACAD_EXPORTS"
    assert evidence["evidence_root"] == "docs/audits/evidence/facad"
    assert set(evidence["allowed_manifest_status"]) == {
        "AWAITING_DIRECT_FACAD_EXPORTS",
        "DIRECT_EVIDENCE_PARTIAL",
        "DIRECT_PARITY_OBSERVED",
    }
    assert evidence["scientific_authority"] is False
    assert evidence["compatibility_only"] is True
    assert evidence["evidence_records"] == []
    assert evidence["parity_rows"] == []

    expected = {
        "FACAD_RICKETTS_32F_COMPATIBILITY_TARGET": 32,
        "FACAD_RICKETTS_13F_COMPATIBILITY_TARGET": 13,
    }
    assert {item["target_id"] for item in targets["targets"]} == set(expected)
    assert {item["target_id"] for item in evidence["profiles"]} == set(expected)
    assert {
        item["target_id"]: item["expected_facad_factor_count"]
        for item in evidence["profiles"]
    } == expected
    assert all(item["observation_status"] == "UNOBSERVED" for item in evidence["profiles"])


def test_facad_direct_parity_requires_all_three_export_families_without_stored_availability():
    evidence = _load(EVIDENCE)
    exports = {item["kind"]: item for item in evidence["required_direct_exports"]}

    assert set(exports) == {
        "ANALYSIS_VALUES",
        "ANALYSIS_PROPERTIES",
        "MARKER_POSITIONS",
    }
    assert all("status" not in item for item in exports.values())

    required_dimensions = {
        "membership",
        "order",
        "export_labels",
        "units",
        "landmarks_and_constructions",
        "sign_convention",
        "same_trace_numeric_values",
        "norms_if_exported",
        "rounding",
        "facad_without_digital_crown_equivalent",
        "digital_crown_without_facad_equivalent",
        "atlas_vs_facad_divergence",
    }
    assert set(evidence["comparison_dimensions"]) == required_dimensions


def test_facad_evidence_records_are_bound_to_immutable_same_trace_artifacts():
    evidence = _load(EVIDENCE)
    contract = evidence["evidence_record_contract"]

    assert set(contract["required_fields"]) == {
        "evidence_id",
        "artifact_kind",
        "profile_target_id",
        "source_path",
        "source_filename",
        "sha256",
        "facad_version",
        "observed_at",
        "same_trace_case_id",
    }
    assert set(contract["allowed_artifact_kinds"]) == {
        "ANALYSIS_VALUES",
        "ANALYSIS_PROPERTIES",
        "MARKER_POSITIONS",
    }
    assert set(contract["allowed_profile_target_ids"]) == {
        "FACAD_RICKETTS_32F_COMPATIBILITY_TARGET",
        "FACAD_RICKETTS_13F_COMPATIBILITY_TARGET",
    }
    assert contract["sha256_format"] == "64 lowercase hexadecimal characters"
    assert "docs/audits/evidence/facad" in contract["source_path_rule"]
    assert "same_trace_case_id" in contract["same_trace_rule"]
    assert "facad_version" in contract["same_trace_rule"]

    row_contract = evidence["parity_row_contract"]
    assert set(row_contract["required_fields"]) == {
        "profile_target_id",
        "facad_order",
        "facad_export_label",
        "facad_unit",
        "digital_crown_measurement_id",
        "membership_status",
        "sign_status",
        "numeric_status",
        "evidence_refs",
    }
    assert set(row_contract["allowed_membership_status"]) == {
        "OBSERVED_MATCH",
        "OBSERVED_FACAD_ONLY",
        "OBSERVED_DC_ONLY",
    }

    rules = evidence["rules"]
    assert rules["direct_export_required"] is True
    assert rules["observed_membership_requires_analysis_values_and_properties"] is True
    assert rules["observed_profile_requires_same_trace_triplet"] is True
    assert rules["same_trace_triplet_requires_same_facad_version"] is True
    assert rules["observed_at_requires_timezone"] is True
    assert rules["no_membership_inference_from_vendor_label"] is True
    assert rules["no_speculative_parity_rows"] is True
    assert rules["no_sign_inference_without_observation"] is True
    assert rules["no_norm_inference_without_observation"] is True
    assert rules["no_scientific_equivalence_claim"] is True
    assert rules["unobserved_fields_remain_unobserved"] is True
    assert rules["evidence_hash_required"] is True
    assert rules["evidence_file_presence_required"] is True
    assert rules["facad_version_required"] is True
