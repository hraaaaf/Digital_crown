import copy
import hashlib
import json
from pathlib import Path

from audit.cephalo_lot08_facad_parity_validate import validate_manifest

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs" / "audits" / "schemas" / "ortho_lot08_facad_ricketts_direct_parity_evidence_v1.json"
TARGET_32 = "FACAD_RICKETTS_32F_COMPATIBILITY_TARGET"
TARGET_13 = "FACAD_RICKETTS_13F_COMPATIBILITY_TARGET"


def _base_manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _profile(manifest, target_id):
    return next(item for item in manifest["profiles"] if item["target_id"] == target_id)


def _artifact(tmp_path, name, content=b"facad-export"):
    path = tmp_path / "evidence" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def _record(tmp_path, evidence_id, kind, target_id=TARGET_32, trace_id="trace-1", content=None):
    payload = content if content is not None else f"{evidence_id}:{kind}".encode()
    path = _artifact(tmp_path, f"{evidence_id}.txt", payload)
    rel = path.relative_to(tmp_path).as_posix()
    return {
        "evidence_id": evidence_id,
        "artifact_kind": kind,
        "profile_target_id": target_id,
        "source_path": rel,
        "source_filename": path.name,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "facad_version": "TEST-3.12",
        "observed_at": "2026-10-06T22:00:00Z",
        "same_trace_case_id": trace_id,
    }


def test_repository_manifest_is_valid_while_direct_exports_are_absent():
    assert validate_manifest(_base_manifest(), ROOT) == []


def test_partial_direct_evidence_is_accepted_only_with_real_matching_artifact(tmp_path):
    manifest = _base_manifest()
    _profile(manifest, TARGET_32)["observation_status"] = "PARTIAL"
    manifest["evidence_records"] = [
        _record(tmp_path, "facad32-values", "ANALYSIS_VALUES"),
    ]

    assert validate_manifest(manifest, tmp_path) == []


def test_declared_sha256_must_match_exact_export_bytes(tmp_path):
    manifest = _base_manifest()
    _profile(manifest, TARGET_32)["observation_status"] = "PARTIAL"
    record = _record(tmp_path, "facad32-values", "ANALYSIS_VALUES")
    record["sha256"] = "0" * 64
    manifest["evidence_records"] = [record]

    errors = validate_manifest(manifest, tmp_path)

    assert any("sha256 does not match file bytes" in item for item in errors)


def test_source_path_rejects_parent_traversal(tmp_path):
    manifest = _base_manifest()
    _profile(manifest, TARGET_32)["observation_status"] = "PARTIAL"
    record = _record(tmp_path, "facad32-values", "ANALYSIS_VALUES")
    record["source_path"] = "../outside.txt"
    record["source_filename"] = "outside.txt"
    manifest["evidence_records"] = [record]

    errors = validate_manifest(manifest, tmp_path)

    assert any("repository-relative without parent traversal" in item for item in errors)


def test_observed_membership_requires_analysis_values_evidence(tmp_path):
    manifest = _base_manifest()
    _profile(manifest, TARGET_32)["observation_status"] = "PARTIAL"
    marker = _record(tmp_path, "facad32-markers", "MARKER_POSITIONS")
    manifest["evidence_records"] = [marker]
    manifest["parity_rows"] = [{
        "profile_target_id": TARGET_32,
        "facad_order": 1,
        "facad_export_label": "Test factor",
        "facad_unit": "deg",
        "digital_crown_measurement_id": "M_TEST",
        "membership_status": "OBSERVED_MATCH",
        "sign_status": "UNOBSERVED",
        "numeric_status": "UNOBSERVED",
        "evidence_refs": ["facad32-markers"],
    }]

    errors = validate_manifest(manifest, tmp_path)

    assert any("observed membership requires ANALYSIS_VALUES evidence" in item for item in errors)


def test_numeric_parity_rejects_cross_trace_evidence(tmp_path):
    manifest = _base_manifest()
    _profile(manifest, TARGET_32)["observation_status"] = "PARTIAL"
    values = _record(tmp_path, "facad32-values", "ANALYSIS_VALUES", trace_id="trace-A")
    markers = _record(tmp_path, "facad32-markers", "MARKER_POSITIONS", trace_id="trace-B")
    manifest["evidence_records"] = [values, markers]
    manifest["parity_rows"] = [{
        "profile_target_id": TARGET_32,
        "facad_order": 1,
        "facad_export_label": "Test factor",
        "facad_unit": "mm",
        "digital_crown_measurement_id": "M_TEST",
        "membership_status": "OBSERVED_MATCH",
        "sign_status": "OBSERVED_MATCH",
        "numeric_status": "OBSERVED_MATCH",
        "evidence_refs": ["facad32-values", "facad32-markers"],
    }]

    errors = validate_manifest(manifest, tmp_path)

    assert any("numeric parity evidence must share one same_trace_case_id" in item for item in errors)


def test_parity_row_rejects_unknown_evidence_reference(tmp_path):
    manifest = _base_manifest()
    _profile(manifest, TARGET_13)["observation_status"] = "PARTIAL"
    manifest["evidence_records"] = [
        _record(tmp_path, "facad13-values", "ANALYSIS_VALUES", target_id=TARGET_13),
    ]
    manifest["parity_rows"] = [{
        "profile_target_id": TARGET_13,
        "facad_order": 1,
        "facad_export_label": "Test factor",
        "facad_unit": "deg",
        "digital_crown_measurement_id": "M_TEST",
        "membership_status": "OBSERVED_MATCH",
        "sign_status": "UNOBSERVED",
        "numeric_status": "UNOBSERVED",
        "evidence_refs": ["missing-evidence-id"],
    }]

    errors = validate_manifest(manifest, tmp_path)

    assert any("unknown evidence_id" in item for item in errors)


def test_unobserved_profile_cannot_silently_hold_evidence(tmp_path):
    manifest = _base_manifest()
    manifest["evidence_records"] = [
        _record(tmp_path, "facad32-values", "ANALYSIS_VALUES"),
    ]

    errors = validate_manifest(manifest, tmp_path)

    assert any("cannot remain UNOBSERVED with evidence or parity rows" in item for item in errors)


def test_observed_profile_requires_all_exports_and_complete_vendor_order(tmp_path):
    manifest = copy.deepcopy(_base_manifest())
    _profile(manifest, TARGET_13)["observation_status"] = "OBSERVED"
    manifest["evidence_records"] = [
        _record(tmp_path, "facad13-values", "ANALYSIS_VALUES", target_id=TARGET_13),
        _record(tmp_path, "facad13-props", "ANALYSIS_PROPERTIES", target_id=TARGET_13),
        _record(tmp_path, "facad13-markers", "MARKER_POSITIONS", target_id=TARGET_13),
    ]

    errors = validate_manifest(manifest, tmp_path)

    assert any("requires exactly 13 Facad rows" in item for item in errors)
    assert any("requires complete Facad order 1..13" in item for item in errors)
