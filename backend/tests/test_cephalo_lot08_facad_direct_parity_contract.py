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
    assert evidence["scientific_authority"] is False
    assert evidence["compatibility_only"] is True
    assert evidence["evidence_records"] == []
    assert evidence["parity_rows"] == []

    expected = {
        "FACAD_RICKETTS_32F_COMPATIBILITY_TARGET",
        "FACAD_RICKETTS_13F_COMPATIBILITY_TARGET",
    }
    assert {item["target_id"] for item in targets["targets"]} == expected
    assert {item["target_id"] for item in evidence["profiles"]} == expected
    assert all(item["observation_status"] == "UNOBSERVED" for item in evidence["profiles"])


def test_facad_direct_parity_requires_all_three_export_families():
    evidence = _load(EVIDENCE)
    exports = {item["kind"]: item for item in evidence["required_direct_exports"]}

    assert set(exports) == {
        "ANALYSIS_VALUES",
        "ANALYSIS_PROPERTIES",
        "MARKER_POSITIONS",
    }
    assert all(item["status"] == "MISSING" for item in exports.values())

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

    rules = evidence["rules"]
    assert rules["direct_export_required"] is True
    assert rules["no_membership_inference_from_vendor_label"] is True
    assert rules["no_sign_inference_without_observation"] is True
    assert rules["no_norm_inference_without_observation"] is True
    assert rules["no_scientific_equivalence_claim"] is True
    assert rules["unobserved_fields_remain_unobserved"] is True
