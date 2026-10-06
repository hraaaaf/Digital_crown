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


def _mark_partial(manifest, target_id):
    _profile(manifest, target_id)["observation_status"] = "PARTIAL"
    manifest["status"] = "DIRECT_EVIDENCE_PARTIAL"


def _artifact(tmp_path, name, content=b"facad-export"):
    path = tmp_path / "docs" / "audits" / "evidence" / "facad" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def _record(tmp_path, evidence_id, kind, target_id=TARGET_32, trace_id="trace-1", version="TEST-3.12", content=None):
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
        "facad_version": version,
        "observed_at": "2026-10-06T22:00:00Z",
        "same_trace_case_id": trace_id,
    }


def test_repository_manifest_is_valid_while_direct_exports_are_absent():
    assert validate_manifest(_base_manifest(), ROOT) == []


def test_partial_direct_evidence_is_accepted_only_with_real_matching_artifact(tmp_path):
    manifest = _base_manifest()
    _mark_partial(manifest, TARGET_32)
    manifest["evidence_records"] = [
        _record(tmp_path, "facad32-values", "ANALYSIS_VALUES"),
    ]

    assert validate_manifest(manifest, tmp_path) == []


def test_declared_sha256_must_match_exact_export_bytes(tmp_path):
    manifest = _base_manifest()
    _mark_partial(manifest, TARGET_32)
    record = _record(tmp_path, "facad32-values", "ANALYSIS_VALUES")
    record["sha256"] = "0" * 64
    manifest["evidence_records"] = [record]

    errors = validate_manifest(manifest, tmp_path)

    assert any("sha256 does not match file bytes" in item for item in errors)


def test_source_path_rejects_parent_traversal(tmp_path):
    manifest = _base_manifest()
    _mark_partial(manifest, TARGET_32)
    record = _record(tmp_path, "facad32-values", "ANALYSIS_VALUES")
    record["source_path"] = "../outside.txt"
    record["source_filename"] = "outside.txt"
    manifest["evidence_records"] = [record]

    errors = validate_manifest(manifest, tmp_path)

    assert any("repository-relative without parent traversal" in item for item in errors)


def test_source_path_must_live_under_dedicated_facad_evidence_root(tmp_path):
    manifest = _base_manifest()
    _mark_partial(manifest, TARGET_32)
    payload = b"not-in-evidence-root"
    outside = tmp_path / "docs" / "random.txt"
    outside.parent.mkdir(parents=True, exist_ok=True)
    outside.write_bytes(payload)
    record = _record(tmp_path, "facad32-values", "ANALYSIS_VALUES")
    record["source_path"] = "docs/random.txt"
    record["source_filename"] = "random.txt"
    record["sha256"] = hashlib.sha256(payload).hexdigest()
    manifest["evidence_records"] = [record]

    errors = validate_manifest(manifest, tmp_path)

    assert any("must live under docs/audits/evidence/facad" in item for item in errors)


def test_observed_membership_requires_values_and_profile_properties(tmp_path):
    manifest = _base_manifest()
    _mark_partial(manifest, TARGET_32)
    values = _record(tmp_path, "facad32-values", "ANALYSIS_VALUES")
    manifest["evidence_records"] = [values]
    manifest["parity_rows"] = [{
        "profile_target_id": TARGET_32,
        "facad_order": 1,
        "facad_export_label": "Test factor",
        "facad_unit": "deg",
        "digital_crown_measurement_id": "M_TEST",
        "membership_status": "OBSERVED_MATCH",
        "sign_status": "UNOBSERVED",
        "numeric_status": "UNOBSERVED",
        "evidence_refs": ["facad32-values"],
    }]

    errors = validate_manifest(manifest, tmp_path)

    assert any("observed membership requires ANALYSIS_VALUES + ANALYSIS_PROPERTIES evidence" in item for item in errors)


def test_numeric_parity_rejects_cross_trace_or_cross_version_evidence(tmp_path):
    manifest = _base_manifest()
    _mark_partial(manifest, TARGET_32)
    values = _record(tmp_path, "facad32-values", "ANALYSIS_VALUES", trace_id="trace-A", version="3.12")
    props = _record(tmp_path, "facad32-props", "ANALYSIS_PROPERTIES", trace_id="trace-A", version="3.12")
    markers = _record(tmp_path, "facad32-markers", "MARKER_POSITIONS", trace_id="trace-B", version="3.13")
    manifest["evidence_records"] = [values, props, markers]
    manifest["parity_rows"] = [{
        "profile_target_id": TARGET_32,
        "facad_order": 1,
        "facad_export_label": "Test factor",
        "facad_unit": "mm",
        "digital_crown_measurement_id": "M_TEST",
        "membership_status": "OBSERVED_MATCH",
        "sign_status": "OBSERVED_MATCH",
        "numeric_status": "OBSERVED_MATCH",
        "evidence_refs": ["facad32-values", "facad32-props", "facad32-markers"],
    }]

    errors = validate_manifest(manifest, tmp_path)

    assert any("numeric parity evidence must share one same_trace_case_id and facad_version" in item for item in errors)


def test_timezone_is_required_for_observation_timestamp(tmp_path):
    manifest = _base_manifest()
    _mark_partial(manifest, TARGET_32)
    record = _record(tmp_path, "facad32-values", "ANALYSIS_VALUES")
    record["observed_at"] = "2026-10-06T22:00:00"
    manifest["evidence_records"] = [record]

    errors = validate_manifest(manifest, tmp_path)

    assert any("timezone-aware ISO-8601" in item for item in errors)


def test_parity_row_rejects_unknown_evidence_reference(tmp_path):
    manifest = _base_manifest()
    _mark_partial(manifest, TARGET_13)
    manifest["evidence_records"] = [
        _record(tmp_path, "facad13-values", "ANALYSIS_VALUES", target_id=TARGET_13),
        _record(tmp_path, "facad13-props", "ANALYSIS_PROPERTIES", target_id=TARGET_13),
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
    manifest["status"] = "DIRECT_EVIDENCE_PARTIAL"
    manifest["evidence_records"] = [
        _record(tmp_path, "facad32-values", "ANALYSIS_VALUES"),
    ]

    errors = validate_manifest(manifest, tmp_path)

    assert any("cannot remain UNOBSERVED with evidence or parity rows" in item for item in errors)


def test_manifest_status_is_derived_and_cannot_stay_stale(tmp_path):
    manifest = _base_manifest()
    _profile(manifest, TARGET_32)["observation_status"] = "PARTIAL"
    manifest["evidence_records"] = [
        _record(tmp_path, "facad32-values", "ANALYSIS_VALUES"),
    ]

    errors = validate_manifest(manifest, tmp_path)

    assert any("status must be derived as DIRECT_EVIDENCE_PARTIAL" in item for item in errors)


def test_speculative_unobserved_parity_rows_are_rejected(tmp_path):
    manifest = _base_manifest()
    _mark_partial(manifest, TARGET_32)
    values = _record(tmp_path, "facad32-values", "ANALYSIS_VALUES")
    props = _record(tmp_path, "facad32-props", "ANALYSIS_PROPERTIES")
    manifest["evidence_records"] = [values, props]
    manifest["parity_rows"] = [{
        "profile_target_id": TARGET_32,
        "facad_order": 1,
        "facad_export_label": "Speculative factor",
        "facad_unit": "deg",
        "digital_crown_measurement_id": "M_TEST",
        "membership_status": "UNOBSERVED",
        "sign_status": "UNOBSERVED",
        "numeric_status": "UNOBSERVED",
        "evidence_refs": ["facad32-values", "facad32-props"],
    }]

    errors = validate_manifest(manifest, tmp_path)

    assert any("membership_status is invalid or speculative" in item for item in errors)


def test_observed_profile_requires_same_trace_same_version_triplet_and_complete_vendor_order(tmp_path):
    manifest = copy.deepcopy(_base_manifest())
    _profile(manifest, TARGET_13)["observation_status"] = "OBSERVED"
    manifest["status"] = "DIRECT_EVIDENCE_PARTIAL"
    manifest["evidence_records"] = [
        _record(tmp_path, "facad13-values", "ANALYSIS_VALUES", target_id=TARGET_13, trace_id="trace-A", version="3.12"),
        _record(tmp_path, "facad13-props", "ANALYSIS_PROPERTIES", target_id=TARGET_13, trace_id="trace-A", version="3.12"),
        _record(tmp_path, "facad13-markers", "MARKER_POSITIONS", target_id=TARGET_13, trace_id="trace-A", version="3.13"),
    ]

    errors = validate_manifest(manifest, tmp_path)

    assert any("same-trace same-version triplet" in item for item in errors)
    assert any("requires exactly 13 Facad rows" in item for item in errors)
    assert any("requires complete Facad order 1..13" in item for item in errors)


def test_facad_only_row_cannot_claim_numeric_or_sign_comparison(tmp_path):
    manifest = _base_manifest()
    _mark_partial(manifest, TARGET_32)
    values = _record(tmp_path, "facad32-values", "ANALYSIS_VALUES")
    props = _record(tmp_path, "facad32-props", "ANALYSIS_PROPERTIES")
    markers = _record(tmp_path, "facad32-markers", "MARKER_POSITIONS")
    manifest["evidence_records"] = [values, props, markers]
    manifest["parity_rows"] = [{
        "profile_target_id": TARGET_32,
        "facad_order": 1,
        "facad_export_label": "Vendor-only factor",
        "facad_unit": "mm",
        "digital_crown_measurement_id": None,
        "membership_status": "OBSERVED_FACAD_ONLY",
        "sign_status": "OBSERVED_DIFFERENT",
        "numeric_status": "OBSERVED_DIFFERENT",
        "evidence_refs": ["facad32-values", "facad32-props", "facad32-markers"],
    }]

    errors = validate_manifest(manifest, tmp_path)

    assert any("Facad-only rows require NOT_APPLICABLE sign and NOT_COMPARABLE numeric status" in item for item in errors)
    assert any("numeric comparison is only valid for OBSERVED_MATCH rows" in item for item in errors)
