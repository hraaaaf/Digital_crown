from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "docs" / "audits" / "schemas" / "ortho_lot08_facad_ricketts_direct_parity_evidence_v1.json"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

_ALLOWED_KINDS = {"ANALYSIS_VALUES", "ANALYSIS_PROPERTIES", "MARKER_POSITIONS"}
_ALLOWED_TARGETS = {
    "FACAD_RICKETTS_32F_COMPATIBILITY_TARGET": 32,
    "FACAD_RICKETTS_13F_COMPATIBILITY_TARGET": 13,
}
_ALLOWED_PROFILE_STATUS = {"UNOBSERVED", "PARTIAL", "OBSERVED"}
_ALLOWED_MEMBERSHIP = {"OBSERVED_MATCH", "OBSERVED_FACAD_ONLY", "OBSERVED_DC_ONLY", "UNOBSERVED"}
_ALLOWED_SIGN = {"OBSERVED_MATCH", "OBSERVED_DIFFERENT", "UNOBSERVED", "NOT_APPLICABLE"}
_ALLOWED_NUMERIC = {"OBSERVED_MATCH", "OBSERVED_DIFFERENT", "UNOBSERVED", "NOT_COMPARABLE"}


def _error(errors: list[str], message: str) -> None:
    errors.append(message)


def _safe_repo_path(value: Any) -> PurePosixPath | None:
    if not isinstance(value, str) or not value:
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        return None
    return path


def _valid_observed_at(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def validate_manifest(manifest: dict[str, Any], root: Path = ROOT) -> list[str]:
    errors: list[str] = []

    if manifest.get("schema_version") != "ORTHO_LOT08_FACAD_RICKETTS_DIRECT_PARITY_EVIDENCE_V1":
        _error(errors, "schema_version mismatch")
    if manifest.get("scientific_authority") is not False:
        _error(errors, "scientific_authority must remain false")
    if manifest.get("compatibility_only") is not True:
        _error(errors, "compatibility_only must remain true")

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

        evidence_id = record.get("evidence_id")
        if not isinstance(evidence_id, str) or not evidence_id.strip():
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

        if not isinstance(record.get("facad_version"), str) or not record.get("facad_version", "").strip():
            _error(errors, f"{prefix}.facad_version is required")
        if not _valid_observed_at(record.get("observed_at")):
            _error(errors, f"{prefix}.observed_at must be ISO-8601")
        if not isinstance(record.get("same_trace_case_id"), str) or not record.get("same_trace_case_id", "").strip():
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
        target_id = row.get("profile_target_id")
        if target_id not in _ALLOWED_TARGETS:
            _error(errors, f"{prefix}.profile_target_id is invalid")
            continue
        rows_by_profile[target_id].append(row)

        membership = row.get("membership_status")
        sign_status = row.get("sign_status")
        numeric_status = row.get("numeric_status")
        if membership not in _ALLOWED_MEMBERSHIP:
            _error(errors, f"{prefix}.membership_status is invalid")
        if sign_status not in _ALLOWED_SIGN:
            _error(errors, f"{prefix}.sign_status is invalid")
        if numeric_status not in _ALLOWED_NUMERIC:
            _error(errors, f"{prefix}.numeric_status is invalid")

        refs = row.get("evidence_refs")
        if not isinstance(refs, list) or not refs:
            _error(errors, f"{prefix}.evidence_refs must contain at least one direct evidence reference")
            referenced: list[dict[str, Any]] = []
        else:
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
        if membership != "UNOBSERVED" and "ANALYSIS_VALUES" not in kinds:
            _error(errors, f"{prefix} observed membership requires ANALYSIS_VALUES evidence")
        if sign_status in {"OBSERVED_MATCH", "OBSERVED_DIFFERENT"} and "MARKER_POSITIONS" not in kinds:
            _error(errors, f"{prefix} observed sign requires MARKER_POSITIONS evidence")
        if numeric_status in {"OBSERVED_MATCH", "OBSERVED_DIFFERENT"}:
            if not {"ANALYSIS_VALUES", "MARKER_POSITIONS"} <= kinds:
                _error(errors, f"{prefix} observed numeric parity requires ANALYSIS_VALUES + MARKER_POSITIONS")
            trace_ids = {record.get("same_trace_case_id") for record in referenced}
            if len(trace_ids) != 1:
                _error(errors, f"{prefix} numeric parity evidence must share one same_trace_case_id")

        facad_included = membership in {"OBSERVED_MATCH", "OBSERVED_FACAD_ONLY"}
        order = row.get("facad_order")
        label = row.get("facad_export_label")
        if facad_included:
            if not isinstance(order, int) or order < 1:
                _error(errors, f"{prefix}.facad_order must be a positive integer for a Facad-observed row")
            else:
                if order in seen_orders[target_id]:
                    _error(errors, f"{prefix}.facad_order is duplicated for {target_id}: {order}")
                seen_orders[target_id].add(order)
            if not isinstance(label, str) or not label.strip():
                _error(errors, f"{prefix}.facad_export_label is required for a Facad-observed row")
        elif membership == "OBSERVED_DC_ONLY":
            if order is not None or label is not None:
                _error(errors, f"{prefix} DC-only rows must not invent Facad order or label")

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
            expected = _ALLOWED_TARGETS[target_id]
            observed_facad_rows = [
                row for row in profile_rows
                if row.get("membership_status") in {"OBSERVED_MATCH", "OBSERVED_FACAD_ONLY"}
            ]
            if len(observed_facad_rows) != expected:
                _error(errors, f"{target_id} OBSERVED requires exactly {expected} Facad rows")
            if seen_orders[target_id] != set(range(1, expected + 1)):
                _error(errors, f"{target_id} OBSERVED requires complete Facad order 1..{expected}")

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
