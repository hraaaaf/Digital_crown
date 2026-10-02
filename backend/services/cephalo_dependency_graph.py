"""Canonical LOT06 measurement dependency graph and analysis-pack registry.

This module is intentionally geometry-free. It never recomputes a cephalometric
measurement and never owns landmark aliases. Scientific dependencies are loaded
from the executable LOT06 measurement contract; analysis packs merely compose
canonical measurement IDs.

Adding a new analysis pack therefore does not require a new frontend mapping or
new geometry code. It still requires source-locked measurement contracts before
a measurement can become executable, and exact pack membership must itself be
source-locked before the pack can become clinical authority.
"""
from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[2]
EXECUTABLE_CONTRACT_PATH = (
    ROOT / "docs" / "audits" / "schemas"
    / "cephalo_vnext_lot06_executable_measurement_contract_v1.json"
)
ANALYSIS_PACK_REGISTRY_PATH = (
    ROOT / "docs" / "audits" / "schemas"
    / "cephalo_vnext_lot06_analysis_pack_registry_v1.json"
)

GRAPH_VERSION = "CEPHALO_LOT06_DEPENDENCY_GRAPH_V1"
PACK_COMPOSITION_STATES = {
    "PROVISIONAL_MEMBERSHIP",
    "SOURCE_LOCKED_MEMBERSHIP",
}


class CephaloDependencyGraphError(ValueError):
    """Canonical analysis composition is invalid or scientifically unavailable."""


@lru_cache(maxsize=1)
def _load_executable_contract() -> dict[str, Any]:
    return json.loads(EXECUTABLE_CONTRACT_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _load_analysis_registry() -> dict[str, Any]:
    payload = json.loads(ANALYSIS_PACK_REGISTRY_PATH.read_text(encoding="utf-8"))
    validate_analysis_pack_registry(payload)
    return payload


def _measurement_contract_index() -> dict[str, Mapping[str, Any]]:
    return {
        item["measurement_id"]: item
        for item in _load_executable_contract()["measurements"]
    }


def _blocked_measurement_index() -> dict[str, Mapping[str, Any]]:
    return {
        item["measurement_id"]: item
        for item in _load_executable_contract().get("non_promoted_geometry_covered", [])
    }


def validate_analysis_pack_registry(payload: Mapping[str, Any]) -> None:
    """Validate data-driven analysis packs without hardcoding pack identities."""
    if payload.get("schema_version") != "CEPHALO_LOT06_ANALYSIS_PACK_REGISTRY_V1":
        raise CephaloDependencyGraphError("Unsupported analysis-pack registry version")

    executable = _measurement_contract_index()
    blocked = _blocked_measurement_index()

    catalog = payload.get("scientific_contract_catalog")
    if not isinstance(catalog, list):
        raise CephaloDependencyGraphError("scientific_contract_catalog must be a list")
    known_contracts: set[str] = set()
    for contract in catalog:
        if not isinstance(contract, Mapping):
            raise CephaloDependencyGraphError("scientific contract catalog entry must be an object")
        contract_id = contract.get("contract_id")
        source_document = contract.get("source_document")
        if (
            not isinstance(contract_id, str)
            or not contract_id.strip()
            or contract_id in known_contracts
        ):
            raise CephaloDependencyGraphError("contract_id must be unique and non-empty")
        if not isinstance(source_document, str) or not source_document.strip():
            raise CephaloDependencyGraphError(
                f"{contract_id}: source_document must be non-empty"
            )
        known_contracts.add(contract_id)

    packs = payload.get("analysis_packs")
    if not isinstance(packs, list):
        raise CephaloDependencyGraphError("analysis_packs must be a list")

    seen_pack_ids: set[str] = set()
    for pack in packs:
        if not isinstance(pack, Mapping):
            raise CephaloDependencyGraphError("analysis pack must be an object")
        pack_id = pack.get("analysis_id")
        if not isinstance(pack_id, str) or not pack_id.strip() or pack_id in seen_pack_ids:
            raise CephaloDependencyGraphError("analysis_id must be unique and non-empty")
        seen_pack_ids.add(pack_id)

        display_name = pack.get("display_name")
        version = pack.get("version")
        composition_state = pack.get("composition_state")
        scientific_contract_refs = pack.get("scientific_contract_refs")
        membership_evidence_refs = pack.get("membership_evidence_refs")
        if not isinstance(display_name, str) or not display_name.strip():
            raise CephaloDependencyGraphError(f"{pack_id}: display_name must be non-empty")
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            raise CephaloDependencyGraphError(f"{pack_id}: version must be a positive integer")
        if composition_state not in PACK_COMPOSITION_STATES:
            raise CephaloDependencyGraphError(
                f"{pack_id}: unsupported composition_state {composition_state!r}"
            )
        if (
            not isinstance(scientific_contract_refs, list)
            or not scientific_contract_refs
            or any(not isinstance(ref, str) or not ref.strip() for ref in scientific_contract_refs)
            or len(scientific_contract_refs) != len(set(scientific_contract_refs))
        ):
            raise CephaloDependencyGraphError(
                f"{pack_id}: scientific_contract_refs must be unique non-empty strings"
            )
        unknown_contract_refs = sorted(set(scientific_contract_refs) - known_contracts)
        if unknown_contract_refs:
            raise CephaloDependencyGraphError(
                f"{pack_id}: unknown scientific contract refs: "
                + ", ".join(unknown_contract_refs)
            )
        if (
            not isinstance(membership_evidence_refs, list)
            or any(not isinstance(ref, str) or not ref.strip() for ref in membership_evidence_refs)
            or len(membership_evidence_refs) != len(set(membership_evidence_refs))
        ):
            raise CephaloDependencyGraphError(
                f"{pack_id}: membership_evidence_refs must be unique strings"
            )
        if (
            composition_state == "SOURCE_LOCKED_MEMBERSHIP"
            and not membership_evidence_refs
        ):
            raise CephaloDependencyGraphError(
                f"{pack_id}: source-locked membership requires evidence refs"
            )

        measurements = pack.get("measurement_ids")
        blocked_measurements = pack.get("blocked_measurement_ids")
        if not isinstance(measurements, list) or not isinstance(blocked_measurements, list):
            raise CephaloDependencyGraphError(
                f"{pack_id}: measurement lists must be explicit arrays"
            )
        if any(not isinstance(item, str) or not item.strip() for item in measurements):
            raise CephaloDependencyGraphError(f"{pack_id}: invalid executable measurement id")
        if any(not isinstance(item, str) or not item.strip() for item in blocked_measurements):
            raise CephaloDependencyGraphError(f"{pack_id}: invalid blocked measurement id")
        if len(measurements) != len(set(measurements)):
            raise CephaloDependencyGraphError(f"{pack_id}: duplicate executable measurement")
        if len(blocked_measurements) != len(set(blocked_measurements)):
            raise CephaloDependencyGraphError(f"{pack_id}: duplicate blocked measurement")
        if set(measurements) & set(blocked_measurements):
            raise CephaloDependencyGraphError(
                f"{pack_id}: a measurement cannot be executable and blocked"
            )

        unknown_executable = sorted(set(measurements) - set(executable))
        if unknown_executable:
            raise CephaloDependencyGraphError(
                f"{pack_id}: non-executable canonical measurements: "
                + ", ".join(unknown_executable)
            )
        unknown_blocked = sorted(set(blocked_measurements) - set(blocked))
        if unknown_blocked:
            raise CephaloDependencyGraphError(
                f"{pack_id}: blocked measurements are not registered as non-promoted: "
                + ", ".join(unknown_blocked)
            )

    presets = payload.get("display_presets", [])
    if not isinstance(presets, list):
        raise CephaloDependencyGraphError("display_presets must be a list")
    seen_preset_ids: set[str] = set()
    for preset in presets:
        if not isinstance(preset, Mapping):
            raise CephaloDependencyGraphError("display preset must be an object")
        preset_id = preset.get("preset_id")
        display_name = preset.get("display_name")
        analysis_ids = preset.get("analysis_ids")
        if (
            not isinstance(preset_id, str)
            or not preset_id.strip()
            or preset_id in seen_preset_ids
        ):
            raise CephaloDependencyGraphError("preset_id must be unique and non-empty")
        seen_preset_ids.add(preset_id)
        if not isinstance(display_name, str) or not display_name.strip():
            raise CephaloDependencyGraphError(f"{preset_id}: display_name must be non-empty")
        if not isinstance(analysis_ids, list):
            raise CephaloDependencyGraphError(f"{preset_id}: analysis_ids must be a list")
        if len(analysis_ids) != len(set(analysis_ids)):
            raise CephaloDependencyGraphError(f"{preset_id}: duplicate analysis_id")
        unknown = sorted(set(analysis_ids) - seen_pack_ids)
        if unknown:
            raise CephaloDependencyGraphError(
                f"display preset references unknown analyses: {', '.join(unknown)}"
            )


def compose_measurement_dependency_graph(
    measurement_ids: Iterable[str],
) -> dict[str, Any]:
    """Build one canonical graph for any data-driven selection of measurements."""
    executable = _measurement_contract_index()
    requested = list(dict.fromkeys(measurement_ids))

    unknown = [measurement_id for measurement_id in requested if measurement_id not in executable]
    if unknown:
        raise CephaloDependencyGraphError(
            "Requested measurements are not executable LOT06 contracts: "
            + ", ".join(sorted(unknown))
        )

    landmarks: set[str] = set()
    constructions: set[str] = set()
    edges: list[dict[str, str]] = []
    measurements: list[dict[str, Any]] = []

    for measurement_id in requested:
        contract = executable[measurement_id]
        required_landmarks = list(contract["required_landmarks"])
        required_constructions = list(contract["required_constructions"])
        landmarks.update(required_landmarks)
        constructions.update(required_constructions)

        for landmark_id in required_landmarks:
            edges.append(
                {
                    "from_type": "measurement",
                    "from_id": measurement_id,
                    "to_type": "landmark",
                    "to_id": landmark_id,
                    "relation": "REQUIRES",
                }
            )
        for construction_id in required_constructions:
            edges.append(
                {
                    "from_type": "measurement",
                    "from_id": measurement_id,
                    "to_type": "construction",
                    "to_id": construction_id,
                    "relation": "REQUIRES",
                }
            )

        measurements.append(
            {
                "measurement_id": measurement_id,
                "unit": contract["unit"],
                "requires_calibration": bool(contract["requires_calibration"]),
                "required_landmarks": required_landmarks,
                "required_constructions": required_constructions,
                "implementation": contract["implementation"],
                "availability_gate": contract["availability_gate"],
                "source_contracts": list(contract["source_contracts"]),
            }
        )

    return {
        "graph_version": GRAPH_VERSION,
        "measurement_ids": requested,
        "measurements": measurements,
        "landmark_ids": sorted(landmarks),
        "construction_ids": sorted(constructions),
        "edges": edges,
    }


def build_analysis_pack_dependency_graph(analysis_id: str) -> dict[str, Any]:
    """Resolve an analysis pack exclusively through canonical measurement contracts."""
    registry = _load_analysis_registry()
    pack = next(
        (item for item in registry["analysis_packs"] if item["analysis_id"] == analysis_id),
        None,
    )
    if pack is None:
        raise CephaloDependencyGraphError(f"Unknown analysis pack: {analysis_id}")

    graph = compose_measurement_dependency_graph(pack["measurement_ids"])
    has_blocked = bool(pack["blocked_measurement_ids"])
    composition_state = pack["composition_state"]
    if composition_state != "SOURCE_LOCKED_MEMBERSHIP":
        scientific_state = "PROVISIONAL_MEMBERSHIP_FAIL_CLOSED"
    elif has_blocked:
        scientific_state = "SOURCE_LOCKED_PARTIAL_FAIL_CLOSED"
    else:
        scientific_state = "SOURCE_LOCKED_EXECUTABLE_SUBSET"

    return {
        **graph,
        "analysis_id": analysis_id,
        "analysis_version": pack["version"],
        "display_name": pack["display_name"],
        "composition_state": composition_state,
        "scientific_contract_refs": list(pack["scientific_contract_refs"]),
        "membership_evidence_refs": list(pack["membership_evidence_refs"]),
        "blocked_measurement_ids": list(pack["blocked_measurement_ids"]),
        "scientific_state": scientific_state,
    }


def list_analysis_packs() -> list[dict[str, Any]]:
    """Return data-driven pack metadata; no scientific dependencies are duplicated."""
    registry = _load_analysis_registry()
    return [
        {
            "analysis_id": item["analysis_id"],
            "display_name": item["display_name"],
            "version": item["version"],
            "composition_state": item["composition_state"],
            "scientific_contract_refs": list(item["scientific_contract_refs"]),
            "membership_evidence_refs": list(item["membership_evidence_refs"]),
            "measurement_ids": list(item["measurement_ids"]),
            "blocked_measurement_ids": list(item["blocked_measurement_ids"]),
        }
        for item in registry["analysis_packs"]
    ]
