"""B9 — Source-locked, section-specific cephalometric requiredness (read only).

This registry deliberately does not choose the active clinical protocol, certify
FACAD equivalence, or authorize PDF COMPLETE. The caller must bind the exact
protocol + section from a trusted backend authority before using this result.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from backend.services.cephalo_measure_registry import CANONICAL_MEASUREMENTS

_ASSET_ROOT = Path(__file__).resolve().parents[1] / "data" / "cephalometry"
_PROFILE_SOURCES: dict[str, tuple[Path, str]] = {
    "STEINER_STATIC_PROTOCOL_PROFILE_V1": (
        _ASSET_ROOT / "steiner_protocol_profile_v1.json", "layers",
    ),
    "TWEED_MERRIFIELD_DC_PROTOCOL_PROFILE_V1": (
        _ASSET_ROOT / "tweed_merrifield_protocol_profile_v1.json", "profiles",
    ),
}
CONTRACT_VERSION = "CEPHALO_PROTOCOL_REQUIREDNESS_V1"
_BLOCK_UNAVAILABLE = "protocol_requiredness_contract_unavailable"


def _finite_typed_number(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def read_required_measurement_contract(
    protocol_profile_id: str | None,
    section_id: str | None,
) -> dict[str, Any]:
    """Return authoritative required IDs for one explicit versioned section.

    A missing, malformed or unapproved source must never yield an empty
    successful contract. An OPEN final gate is reported, not disguised.
    """
    result: dict[str, Any] = {
        "contract_version": CONTRACT_VERSION,
        "protocol_profile_id": protocol_profile_id,
        "section_id": section_id,
        "required_measurement_ids": [],
        "source_sha256": None,
        "source_locked": False,
        "protocol_final_gate_satisfied": False,
        "blocking_gates": [],
    }
    source = _PROFILE_SOURCES.get(protocol_profile_id or "")
    if source is None or not section_id:
        result["blocking_gates"] = [_BLOCK_UNAVAILABLE]
        return result

    path, section_key = source
    try:
        source_bytes = path.read_bytes()
        profile = json.loads(source_bytes.decode("utf-8"))
        gate = profile.get("pre_code_gate") or {}
        sections = profile.get(section_key) or {}
        section = sections.get(section_id) if isinstance(sections, dict) else None
        required = section.get("required_measurement_ids") if isinstance(section, dict) else None
        if (
            profile.get("protocol_profile_id") != protocol_profile_id
            or profile.get("status") != "SOURCE_LOCKED"
            or gate.get("status") != "SATISFIED"
            or gate.get("scope") != protocol_profile_id
            or not isinstance(required, list)
            or not required
            or any(not isinstance(cid, str) or cid not in CANONICAL_MEASUREMENTS for cid in required)
            or len(set(required)) != len(required)
        ):
            raise ValueError("Invalid source-locked profile section")
        result["required_measurement_ids"] = list(required)
        result["source_sha256"] = hashlib.sha256(source_bytes).hexdigest()
        result["source_locked"] = True
        result["protocol_final_gate_satisfied"] = (
            (profile.get("final_gate") or {}).get("status") == "SATISFIED"
        )
        if not result["protocol_final_gate_satisfied"]:
            result["blocking_gates"].append("protocol_final_gate_not_satisfied")
    except (OSError, UnicodeError, ValueError, TypeError, AttributeError):
        result["blocking_gates"] = [_BLOCK_UNAVAILABLE]
    return result


def evaluate_required_measurements(
    protocol_profile_id: str | None,
    section_id: str | None,
    canonical_measurements: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Check required typed measurements; never imply PDF/clinical certification."""
    contract = read_required_measurement_contract(protocol_profile_id, section_id)
    blockers = list(contract["blocking_gates"])
    by_id: dict[str, Mapping[str, Any]] = {}
    duplicate_ids: set[str] = set()
    for row in canonical_measurements:
        if not isinstance(row, Mapping):
            blockers.append("canonical_measurement_row_malformed")
            continue
        cid = row.get("canonical_measurement_id")
        if not isinstance(cid, str) or not cid:
            blockers.append("canonical_measurement_id_malformed")
        elif cid in by_id:
            duplicate_ids.add(cid)
        else:
            by_id[cid] = row

    for cid in contract["required_measurement_ids"]:
        if cid in duplicate_ids:
            blockers.append(f"required_measurement_duplicate:{cid}")
            continue
        row = by_id.get(cid)
        if row is None:
            blockers.append(f"required_measurement_missing:{cid}")
            continue
        value = row.get("value")
        if (
            row.get("availability_status") != "AVAILABLE"
            or not isinstance(value, (float, int))
            or isinstance(value, bool)
            or not _finite_typed_number(value)
            or not isinstance(row.get("measurement_refs"), (list, tuple))
            or not row.get("measurement_refs")
            or not all(isinstance(ref, str) and bool(ref) for ref in row["measurement_refs"])
            or not isinstance(row.get("value_authority_method_id"), str)
            or not row.get("value_authority_method_id")
        ):
            blockers.append(f"required_measurement_invalid:{cid}")

    contract["blocking_gates"] = sorted(set(blockers))
    contract["required_measurements_satisfied"] = bool(
        contract["required_measurement_ids"]
    ) and not contract["blocking_gates"]
    return contract
