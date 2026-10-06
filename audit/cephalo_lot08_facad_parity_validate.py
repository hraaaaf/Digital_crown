from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "docs" / "audits" / "schemas" / "ortho_lot08_facad_ricketts_direct_parity_evidence_v1.json"
_EVIDENCE_ROOT = PurePosixPath("docs/audits/evidence/facad")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

_ALLOWED_KINDS = {"ANALYSIS_VALUES", "ANALYSIS_PROPERTIES", "MARKER_POSITIONS"}
_ALLOWED_TARGETS = {
    "FACAD_RICKETTS_32F_COMPATIBILITY_TARGET": 32,
    "FACAD_RICKETTS_13F_COMPATIBILITY_TARGET": 13,
}
_ALLOWED_PROFILE_STATUS = {"UNOBSERVED", "PARTIAL", "OBSERVED"}
_ALLOWED_MANIFEST_STATUS = {
    "AWAITING_DIRECT_FACAD_EXPORTS",
    "DIRECT_EVIDENCE_PARTIAL",
    "DIRECT_PARITY_OBSERVED",
}
_ALLOWED_MEMBERSHIP = {"OBSERVED_MATCH", "OBSERVED_FACAD_ONLY", "OBSERVED_DC_ONLY"}
_ALLOWED_SIGN = {"OBSERVED_MATCH", "OBSERVED_DIFFERENT", "UNOBSERVED", "NOT_APPLICABLE"}
_ALLOWED_NUMERIC = {"OBSERVED_MATCH", "OBSERVED_DIFFERENT", "UNOBSERVED", "NOT_COMPARABLE"}
_ALLOWED_DIMENSION_STATUS = {"OBSERVED_MATCH", "OBSERVED_DIFFERENT", "UNOBSERVED", "NOT_APPLICABLE"}
_ALLOWED_NORM_STATUS = {"OBSERVED_MATCH", "OBSERVED_DIFFERENT", "UNOBSERVED", "NOT_EXPORTED", "NOT_APPLICABLE"}
_EVIDENCE_REQUIRED_FIELDS = {
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
_PARITY_REQUIRED_FIELDS = {
    "profile_target_id",
    "facad_order",
    "facad_export_label",
    "facad_unit",
    "digital_crown_measurement_id",
    "membership_status",
    "sign_status",
    "numeric_status",
    "comparison_details",
    "evidence_refs",
}
_COMPARISON_DETAIL_FIELDS = {
    "digital_crown_label",
    "label_status",
    "digital_crown_unit",
    "unit_status",
    "facad_landmarks_constructions",
    "digital_crown_landmarks_constructions",
    "construction_status",
    "facad_value",
    "digital_crown_value",
    "numeric_delta",
    "facad_norm",
    "digital_crown_norm",
    "norm_status",
    "facad_display_value",
    "digital_crown_display_value",
    "rounding_status",
    "atlas_divergence_status",
    "atlas_divergence_note",
}


def _error(errors: list[str], message: str) -> None:
    errors.append(message)


def _safe_repo_path(value: Any) -> PurePosixPath | None:
    if not isinstance(value, str) or not value:
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        return None
    return path


def _under_evidence_root(path: PurePosixPath) -> bool:
    return path.parts[: len(_EVIDENCE_ROOT.parts)] == _EVIDENCE_ROOT.parts


def _valid_observed_at(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_manifest(manifest: dict[str, Any], root: Path = ROOT) -> list[str]:
    errors: list[str] = []

    if manifest.get("schema_version") != "ORTHO_LOT08_FACAD_RICKETTS_DIRECT_PARITY_EVIDENCE_V1":
        _error(errors, "schema_version mismatch")
    if manifest.get("scientific_authority") is not False:
        _error(errors, "scientific_authority must remain false")
    if manifest.get("compatibility_only") is not True:
        _error(errors, "compatibility_only must remain true")
    if manifest.get("evidence_root") != _EVIDENCE_ROOT.as_posix():
        _error(errors, "evidence_root contract mismatch")
    if set(manifest.get("allowed_manifest_status") or []) != _ALLOWED_MANIFEST_STATUS:
        _error(errors, "allowed_manifest_status contract mismatch")
    if set(manifest.get("allowed_profile_observation_status") or []) != _ALLOWED_PROFILE_STATUS:
        _error(errors, "allowed_profile_observation_status contract mismatch")

    exports = manifest.get("required_direct_exports")
    if not isinstance(exports, list):
        _error(errors, "required_direct_exports must be a list")
    else:
        export_kinds = {item.get("kind") for item in exports if isinstance(item, dict)}
        if export_kinds != _ALLOWED_KINDS:
            _error(errors, "required_direct_exports must define exactly the three direct export families")
        if any(isinstance(item, dict) and "status" in item for item in exports):
            _error(errors, "required_direct_exports status must be derived from evidence, not stored")

    evidence_contract = manifest.get("evidence_record_contract")
    if not isinstance(evidence_contract, dict):
        _error(errors, "evidence_record_contract must be an object")
    else:
        if set(evidence_contract.get("required_fields") or []) != _EVIDENCE_REQUIRED_FIELDS:
            _error(errors, "evidence_record_contract.required_fields mismatch")
        if set(evidence_contract.get("allowed_artifact_kinds") or []) != _ALLOWED_KINDS:
            _error(errors, "evidence_record_contract.allowed_artifact_kinds mismatch")
        if set(evidence_contract.get("allowed_profile_target_ids") or []) != set(_ALLOWED_TARGETS):
            _error(errors, "evidence_record_contract.allowed_profile_target_ids mismatch")

    row_contract = manifest.get("parity_row_contract")
    if not isinstance(row_contract, dict):
        _error(errors, "parity_row_contract must be an object")
    else:
        if set(row_contract.get("required_fields") or []) != _PARITY_REQUIRED_FIELDS:
            _error(errors, "parity_row_contract.required_fields mismatch")
        if set(row_contract.get("comparison_details_required_fields") or []) != _COMPARISON_DETAIL_FIELDS:
            _error(errors, "parity_row_contract.comparison_details_required_fields mismatch")
        if set(row_contract.get("allowed_dimension_status") or []) != _ALLOWED_DIMENSION_STATUS:
            _error(errors, "parity_row_contract.allowed_dimension_status mismatch")
        if set(row_contract.get("allowed_norm_status") or []) != _ALLOWED_NORM_STATUS:
            _error(errors, "parity_row_contract.allowed_norm_status mismatch")
        if set(row_contract.get("allowed_membership_status") or []) != _ALLOWED_MEMBERSHIP:
            _error(errors, "parity_row_contract.allowed_membership_status mismatch")
        if set(row_contract.get("allowed_sign_status") or []) != _ALLOWED_SIGN:
            _error(errors, "parity_row_contract.allowed_sign_status mismatch")
        if set(row_contract.get("allowed_numeric_status") or []) != _ALLOWED_NUMERIC:
            _error(errors, "parity_row_contract.allowed_numeric_status mismatch")

    profiles = manifest.get("profiles")
    if not isinstance(profiles, list):
        return errors + ["profiles must be a list"]

    profile_by_id: dict[str, dict[str, Any]] = {}
    for index, profile in enumerate(profiles):
        if not isinstance(profile, dict):
            _error(errors, f"profiles[{index}] must be an object")
            continue
        target_id = profile.get("target_id")
        if target_id not in _ALLOWED_TARGETS:
            _error(errors, f"profiles[{index}] has unknown target_id")
            continue
        if target_id in profile_by_id:
            _error(errors, f"duplicate profile target_id: {target_id}")
            continue
        profile_by_id[target_id] = profile
        if profile.get("expected_facad_factor_count") != _ALLOWED_TARGETS[target_id]:
            _error(errors, f"{target_id} expected_facad_factor_count mismatch")
        if profile.get("observation_status") not in _ALLOWED_PROFILE_STATUS:
            _error(errors, f"{target_id} has invalid observation_status")

    if set(profile_by_id) != set(_ALLOWED_TARGETS):
        _error(errors, "both Facad 32F and 13F profiles are required")

    records = manifest.get("evidence_records")
    if not isinstance(records, list):
        return errors + ["evidence_records must be a list"]

    evidence_by_id: dict[str, dict[str, Any]] = {}
    records_by_profile: dict[str, list[dict[str, Any]]] = {target: [] for target in _ALLOWED_TARGETS}
    for index, record in enumerate(records):
        prefix = f"evidence_records[{index}]"
        if not isinstance(record, dict):
            _error(errors, f"{prefix} must be an object")
            continue

        missing = _EVIDENCE_REQUIRED_FIELDS - set(record)
        if missing:
            _error(errors, f"{prefix} missing required fields: {sorted(missing)}")

        evidence_id = record.get("evidence_id")
        if not _nonempty_string(evidence_id):
            _error(errors, f"{prefix}.evidence_id is required")
        elif evidence_id in evidence_by_id:
            _error(errors, f"duplicate evidence_id: {evidence_id}")
        else:
            evidence_by_id[evidence_id] = record

        kind = record.get("artifact_kind")
        if kind not in _ALLOWED_KINDS:
            _error(errors, f"{prefix}.artifact_kind is invalid")

        target_id = record.get("profile_target_id")
        if target_id not in _ALLOWED_TARGETS:
            _error(errors, f"{prefix}.profile_target_id is invalid")
        else:
            records_by_profile[target_id].append(record)

        source_path = _safe_repo_path(record.get("source_path"))
        if source_path is None:
            _error(errors, f"{prefix}.source_path must be repository-relative without parent traversal")
        else:
            if not _under_evidence_root(source_path):
                _error(errors, f"{prefix}.source_path must live under {_EVIDENCE_ROOT.as_posix()}")
            source_filename = record.get("source_filename")
            if source_filename != source_path.name:
                _error(errors, f"{prefix}.source_filename must match source_path basename")
            disk_path = root.joinpath(*source_path.parts)
            if not disk_path.is_file():
                _error(errors, f"{prefix}.source_path does not exist: {source_path}")
            else:
                declared_hash = record.get("sha256")
                actual_hash = hashlib.sha256(disk_path.read_bytes()).hexdigest()
                if declared_hash != actual_hash:
                    _error(errors, f"{prefix}.sha256 does not match file bytes")

        declared_hash = record.get("sha256")
        if not isinstance(declared_hash, str) or not _SHA256_RE.fullmatch(declared_hash):
            _error(errors, f"{prefix}.sha256 must be 64 lowercase hexadecimal characters")

        if not _nonempty_string(record.get("facad_version")):
            _error(errors, f"{prefix}.facad_version is required")
        if not _valid_observed_at(record.get("observed_at")):
            _error(errors, f"{prefix}.observed_at must be timezone-aware ISO-8601")
        if not _nonempty_string(record.get("same_trace_case_id")):
            _error(errors, f"{prefix}.same_trace_case_id is required")

    rows = manifest.get("parity_rows")
    if not isinstance(rows, list):
        return errors + ["parity_rows must be a list"]

    rows_by_profile: dict[str, list[dict[str, Any]]] = {target: [] for target in _ALLOWED_TARGETS}
    seen_orders: dict[str, set[int]] = {target: set() for target in _ALLOWED_TARGETS}

    for index, row in enumerate(rows):
        prefix = f"parity_rows[{index}]"
        if not isinstance(row, dict):
            _error(errors, f"{prefix} must be an object")
            continue

        missing = _PARITY_REQUIRED_FIELDS - set(row)
        if missing:
            _error(errors, f"{prefix} missing required fields: {sorted(missing)}")

        target_id = row.get("profile_target_id")
        if target_id not in _ALLOWED_TARGETS:
            _error(errors, f"{prefix}.profile_target_id is invalid")
            continue
        rows_by_profile[target_id].append(row)

        membership = row.get("membership_status")
        sign_status = row.get("sign_status")
        numeric_status = row.get("numeric_status")
        if membership not in _ALLOWED_MEMBERSHIP:
            _error(errors, f"{prefix}.membership_status is invalid or speculative")
        if sign_status not in _ALLOWED_SIGN:
            _error(errors, f"{prefix}.sign_status is invalid")
        if numeric_status not in _ALLOWED_NUMERIC:
            _error(errors, f"{prefix}.numeric_status is invalid")

        details = row.get("comparison_details")
        if not isinstance(details, dict):
            _error(errors, f"{prefix}.comparison_details must be an object")
            details = {}
        else:
            detail_missing = _COMPARISON_DETAIL_FIELDS - set(details)
            if detail_missing:
                _error(errors, f"{prefix}.comparison_details missing required fields: {sorted(detail_missing)}")
            for key in ("label_status", "unit_status", "construction_status", "rounding_status", "atlas_divergence_status"):
                if details.get(key) not in _ALLOWED_DIMENSION_STATUS:
                    _error(errors, f"{prefix}.comparison_details.{key} is invalid")
            if details.get("norm_status") not in _ALLOWED_NORM_STATUS:
                _error(errors, f"{prefix}.comparison_details.norm_status is invalid")

            if details.get("label_status") in {"OBSERVED_MATCH", "OBSERVED_DIFFERENT"} and not _nonempty_string(details.get("digital_crown_label")):
                _error(errors, f"{prefix} observed label comparison requires Digital Crown label")
            if details.get("unit_status") in {"OBSERVED_MATCH", "OBSERVED_DIFFERENT"}:
                if not _nonempty_string(row.get("facad_unit")) or not _nonempty_string(details.get("digital_crown_unit")):
                    _error(errors, f"{prefix} observed unit comparison requires both Facad and Digital Crown units")
            if details.get("construction_status") in {"OBSERVED_MATCH", "OBSERVED_DIFFERENT"}:
                if not details.get("facad_landmarks_constructions") or not details.get("digital_crown_landmarks_constructions"):
                    _error(errors, f"{prefix} observed construction comparison requires both construction definitions")
            if numeric_status in {"OBSERVED_MATCH", "OBSERVED_DIFFERENT"}:
                if details.get("facad_value") is None or details.get("digital_crown_value") is None:
                    _error(errors, f"{prefix} observed numeric parity requires both numeric values")
                if details.get("numeric_delta") is None:
                    _error(errors, f"{prefix} observed numeric parity requires numeric_delta")
            if details.get("norm_status") in {"OBSERVED_MATCH", "OBSERVED_DIFFERENT"}:
                if details.get("facad_norm") is None or details.get("digital_crown_norm") is None:
                    _error(errors, f"{prefix} observed norm comparison requires both norms")
            if details.get("rounding_status") in {"OBSERVED_MATCH", "OBSERVED_DIFFERENT"}:
                if details.get("facad_display_value") is None or details.get("digital_crown_display_value") is None:
                    _error(errors, f"{prefix} observed rounding comparison requires both display values")
            if details.get("atlas_divergence_status") == "OBSERVED_DIFFERENT" and not _nonempty_string(details.get("atlas_divergence_note")):
                _error(errors, f"{prefix} Atlas divergence requires an explanatory note")

        refs = row.get("evidence_refs")
        if not isinstance(refs, list) or not refs:
            _error(errors, f"{prefix}.evidence_refs must contain at least one direct evidence reference")
            referenced: list[dict[str, Any]] = []
        else:
            if len(refs) != len(set(refs)):
                _error(errors, f"{prefix}.evidence_refs contains duplicates")
            referenced = []
            for ref in refs:
                record = evidence_by_id.get(ref)
                if record is None:
                    _error(errors, f"{prefix}.evidence_refs contains unknown evidence_id: {ref}")
                    continue
                if record.get("profile_target_id") != target_id:
                    _error(errors, f"{prefix}.evidence_refs crosses profile boundary: {ref}")
                referenced.append(record)

        kinds = {record.get("artifact_kind") for record in referenced}
        if not {"ANALYSIS_VALUES", "ANALYSIS_PROPERTIES"} <= kinds:
            _error(errors, f"{prefix} observed membership requires ANALYSIS_VALUES + ANALYSIS_PROPERTIES evidence")
        if details.get("construction_status") in {"OBSERVED_MATCH", "OBSERVED_DIFFERENT"} and "MARKER_POSITIONS" not in kinds:
            _error(errors, f"{prefix} observed construction comparison requires MARKER_POSITIONS evidence")

        if sign_status in {"OBSERVED_MATCH", "OBSERVED_DIFFERENT"} and "MARKER_POSITIONS" not in kinds:
            _error(errors, f"{prefix} observed sign requires MARKER_POSITIONS evidence")
        if numeric_status in {"OBSERVED_MATCH", "OBSERVED_DIFFERENT"}:
            if membership != "OBSERVED_MATCH":
                _error(errors, f"{prefix} numeric comparison is only valid for OBSERVED_MATCH rows")
            if not _ALLOWED_KINDS <= kinds:
                _error(errors, f"{prefix} observed numeric parity requires all three direct export families")
            trace_versions = {
                (record.get("same_trace_case_id"), record.get("facad_version"))
                for record in referenced
            }
            if len(trace_versions) != 1:
                _error(errors, f"{prefix} numeric parity evidence must share one same_trace_case_id and facad_version")

        facad_included = membership in {"OBSERVED_MATCH", "OBSERVED_FACAD_ONLY"}
        order = row.get("facad_order")
        label = row.get("facad_export_label")
        dc_id = row.get("digital_crown_measurement_id")

        if facad_included:
            if not isinstance(order, int) or order < 1:
                _error(errors, f"{prefix}.facad_order must be a positive integer for a Facad-observed row")
            else:
                if order in seen_orders[target_id]:
                    _error(errors, f"{prefix}.facad_order is duplicated for {target_id}: {order}")
                seen_orders[target_id].add(order)
            if not _nonempty_string(label):
                _error(errors, f"{prefix}.facad_export_label is required for a Facad-observed row")

        if membership == "OBSERVED_MATCH" and not _nonempty_string(dc_id):
            _error(errors, f"{prefix} matched rows require digital_crown_measurement_id")
        elif membership == "OBSERVED_FACAD_ONLY":
            if dc_id is not None:
                _error(errors, f"{prefix} Facad-only rows must not invent digital_crown_measurement_id")
            if sign_status != "NOT_APPLICABLE" or numeric_status != "NOT_COMPARABLE":
                _error(errors, f"{prefix} Facad-only rows require NOT_APPLICABLE sign and NOT_COMPARABLE numeric status")
        elif membership == "OBSERVED_DC_ONLY":
            if not _nonempty_string(dc_id):
                _error(errors, f"{prefix} DC-only rows require digital_crown_measurement_id")
            if order is not None or label is not None:
                _error(errors, f"{prefix} DC-only rows must not invent Facad order or label")
            if sign_status != "NOT_APPLICABLE" or numeric_status != "NOT_COMPARABLE":
                _error(errors, f"{prefix} DC-only rows require NOT_APPLICABLE sign and NOT_COMPARABLE numeric status")

    for target_id, profile in profile_by_id.items():
        status = profile.get("observation_status")
        profile_records = records_by_profile[target_id]
        profile_rows = rows_by_profile[target_id]
        kinds = {record.get("artifact_kind") for record in profile_records}

        if status == "UNOBSERVED":
            if profile_records or profile_rows:
                _error(errors, f"{target_id} cannot remain UNOBSERVED with evidence or parity rows")
        elif status == "PARTIAL":
            if not profile_records:
                _error(errors, f"{target_id} PARTIAL requires at least one evidence record")
        elif status == "OBSERVED":
            if kinds != _ALLOWED_KINDS:
                _error(errors, f"{target_id} OBSERVED requires all three direct export families")

            trace_versions_by_kind = {
                kind: {
                    (record.get("same_trace_case_id"), record.get("facad_version"))
                    for record in profile_records
                    if record.get("artifact_kind") == kind
                    and _nonempty_string(record.get("same_trace_case_id"))
                    and _nonempty_string(record.get("facad_version"))
                }
                for kind in _ALLOWED_KINDS
            }
            common_trace_versions = set.intersection(
                *(trace_versions_by_kind[kind] for kind in _ALLOWED_KINDS)
            )
            if not common_trace_versions:
                _error(
                    errors,
                    f"{target_id} OBSERVED requires a same-trace same-version triplet across all three export families",
                )

            expected = _ALLOWED_TARGETS[target_id]
            observed_facad_rows = [
                row for row in profile_rows
                if row.get("membership_status") in {"OBSERVED_MATCH", "OBSERVED_FACAD_ONLY"}
            ]
            if len(observed_facad_rows) != expected:
                _error(errors, f"{target_id} OBSERVED requires exactly {expected} Facad rows")
            if seen_orders[target_id] != set(range(1, expected + 1)):
                _error(errors, f"{target_id} OBSERVED requires complete Facad order 1..{expected}")

            for row_index, row in enumerate(profile_rows):
                details = row.get("comparison_details") if isinstance(row.get("comparison_details"), dict) else {}
                unresolved = []
                if row.get("sign_status") == "UNOBSERVED":
                    unresolved.append("sign_status")
                if row.get("numeric_status") == "UNOBSERVED":
                    unresolved.append("numeric_status")
                for key in ("label_status", "unit_status", "construction_status", "norm_status", "rounding_status", "atlas_divergence_status"):
                    if details.get(key) == "UNOBSERVED":
                        unresolved.append(key)
                if unresolved:
                    _error(errors, f"{target_id} OBSERVED row {row_index} has unresolved dimensions: {sorted(unresolved)}")

    profile_statuses = {
        profile.get("observation_status")
        for profile in profile_by_id.values()
        if profile.get("observation_status") in _ALLOWED_PROFILE_STATUS
    }
    if not records and not rows and profile_statuses == {"UNOBSERVED"}:
        expected_manifest_status = "AWAITING_DIRECT_FACAD_EXPORTS"
    elif len(profile_by_id) == len(_ALLOWED_TARGETS) and all(
        profile.get("observation_status") == "OBSERVED" for profile in profile_by_id.values()
    ):
        expected_manifest_status = "DIRECT_PARITY_OBSERVED"
    else:
        expected_manifest_status = "DIRECT_EVIDENCE_PARTIAL"

    if manifest.get("status") != expected_manifest_status:
        _error(errors, f"status must be derived as {expected_manifest_status}")

    return errors


def main() -> int:
    manifest = json.loads(DEFAULT_MANIFEST.read_text(encoding="utf-8"))
    errors = validate_manifest(manifest)
    if errors:
        for item in errors:
            print(f"FACAD_PARITY_EVIDENCE_ERROR: {item}")
        return 1
    print("FACAD_PARITY_EVIDENCE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
