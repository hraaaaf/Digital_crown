"""LOT06 typed-method -> canonical measurement identity bridge.

This module does not recompute geometry and does not mutate persisted evidence.
It only resolves already-versioned typed method IDs to canonical M_* identities.
Blocked/unmapped methods fail closed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

BridgeState = Literal["MAPPED", "BLOCKED", "UNMAPPED_CANONICAL_ID"]

@dataclass(frozen=True)
class CanonicalMethodBinding:
    method_id: str
    canonical_measurement_id: str | None
    state: BridgeState
    reason: str

def _b(method_id: str, canonical_id: str | None, state: BridgeState, reason: str) -> CanonicalMethodBinding:
    return CanonicalMethodBinding(method_id, canonical_id, state, reason)

_BINDINGS = (
    _b("CRANIOM_SITUATION_A_MM_V1","M_A_NPERP_MM_V1","MAPPED","EXACT_GEOMETRY_IDENTITY_BINDING"),
    _b("CRANIOM_SITUATION_B_MM_V1","M_B_NPERP_MM_V1","MAPPED","EXACT_GEOMETRY_IDENTITY_BINDING"),
    _b("CRANIOM_AB_PRIME_MM_V1","M_AB_PRIME_FH_MM_V1","MAPPED","EXACT_GEOMETRY_IDENTITY_BINDING"),
    _b("CRANIOM_FACIAL_DEPTH_MM_V1","M_COM_S_NPERP_DEPTH_MM_V1","MAPPED","EXACT_GEOMETRY_IDENTITY_BINDING"),
    _b("CRANIOM_U1_FRANKFORT_DEG_V1","M_U1_FH_DEG_V1","MAPPED","EXACT_GEOMETRY_IDENTITY_BINDING"),
    _b("CRANIOM_L1_DOWNS_DEG_V1","M_IMPA_GOME_DEG_V1","MAPPED","EXACT_GEOMETRY_IDENTITY_BINDING"),
    _b("CRANIOM_INTERINCISAL_DEG_V1","M_INTERINCISAL_DEG_V1","MAPPED","EXACT_GEOMETRY_IDENTITY_BINDING"),
    _b("STEINER_SNA_DEG_V1","M_SNA_DEG_V1","MAPPED","EXACT_GEOMETRY_IDENTITY_BINDING"),
    _b("STEINER_SNB_DEG_V1","M_SNB_DEG_V1","MAPPED","EXACT_GEOMETRY_IDENTITY_BINDING"),
    _b("STEINER_ANB_DEG_V1","M_ANB_DEG_V1","MAPPED","EXACT_GEOMETRY_IDENTITY_BINDING"),
    _b("STEINER_SN_MP_DEG_V1","M_SN_GOGN_DEG_V1","MAPPED","EXACT_GEOMETRY_IDENTITY_BINDING"),
    _b("STEINER_U1_NA_DEG_V1","M_U1_NA_DEG_V1","MAPPED","EXACT_GEOMETRY_IDENTITY_BINDING"),
    _b("STEINER_L1_NB_DEG_V1","M_L1_NB_DEG_V1","MAPPED","EXACT_GEOMETRY_IDENTITY_BINDING"),
    _b("TWEED_FMA_DEG_V1","M_FH_GOME_DEG_V1","MAPPED","EXACT_GEOMETRY_IDENTITY_BINDING"),
    _b("TWEED_IMPA_DEG_V1","M_IMPA_GOME_DEG_V1","MAPPED","EXACT_GEOMETRY_IDENTITY_BINDING"),
    _b("TWEED_FMIA_DEG_V1","M_FMIA_L1_FH_DEG_V1","MAPPED","EXACT_GEOMETRY_IDENTITY_BINDING"),
    _b("MERRIFIELD_Z_ANGLE_DEG_V1",None,"UNMAPPED_CANONICAL_ID","NO_CANONICAL_M_ID_SOURCE_LOCKED"),
    _b("DOWNS_FACIAL_ANGLE_DEG_V1",None,"BLOCKED","ANGLE_CONVENTION_COLLISION_45_VS_135"),
    _b("DOWNS_Y_AXIS_DEG_V1",None,"UNMAPPED_CANONICAL_ID","NO_CANONICAL_M_ID_SOURCE_LOCKED"),
    _b("MCNAMARA_CO_A_MM_V1","M_CO_A_MM_V1","MAPPED","EXACT_GEOMETRY_IDENTITY_BINDING"),
    _b("MCNAMARA_CO_GN_MM_V1","M_CO_GN_ANATOMIC_MM_V1","MAPPED","EXACT_GEOMETRY_IDENTITY_BINDING"),
    _b("MCNAMARA_ANS_ME_MM_V1","M_ANS_ME_MM_V1","MAPPED","EXACT_GEOMETRY_IDENTITY_BINDING"),
    _b("M_A_NPERP_MM_V1","M_A_NPERP_MM_V1","MAPPED","EXACT_GEOMETRY_IDENTITY_BINDING"),
    _b("M_POG_NPERP_MM_V1","M_POG_NPERP_MM_V1","MAPPED","EXACT_GEOMETRY_IDENTITY_BINDING"),
    _b("RICKETTS_FACIAL_DEPTH_DEG_V1",None,"BLOCKED","ANGLE_CONVENTION_COLLISION_45_VS_135"),
    _b("RICKETTS_CONVEXITY_A_NPOG_MM_V1",None,"BLOCKED","LEGACY_TYPED_IDENTITY_BRIDGE_REQUIRED"),
    _b("RICKETTS_E_LINE_LS_MM_V2",None,"BLOCKED","LEGACY_TYPED_IDENTITY_BRIDGE_REQUIRED"),
    _b("RICKETTS_E_LINE_LI_MM_V2",None,"BLOCKED","LEGACY_TYPED_IDENTITY_BRIDGE_REQUIRED"),
)

CANONICAL_METHOD_BINDINGS = {item.method_id: item for item in _BINDINGS}

def binding_for_method(method_id: str) -> CanonicalMethodBinding:
    try:
        return CANONICAL_METHOD_BINDINGS[method_id]
    except KeyError as exc:
        raise ValueError(f"Unknown typed cephalometric method_id: {method_id}") from exc

def canonical_measurement_id_for_method(method_id: str) -> str:
    binding = binding_for_method(method_id)
    if binding.state != "MAPPED" or binding.canonical_measurement_id is None:
        raise ValueError(
            f"Typed method {method_id} has no promotable canonical identity: "
            f"{binding.state}/{binding.reason}"
        )
    return binding.canonical_measurement_id


def project_canonical_measurements(measurements) -> dict[str, object]:
    """Collapse mapped typed methods onto canonical M_* identities.

    Multiple historical methods may map to one canonical geometry. They must
    agree exactly on unit, availability and value; divergence fails closed.
    Blocked/unmapped methods are reported but never promoted.
    """
    canonical: dict[str, dict[str, object]] = {}
    blocked: list[str] = []
    unmapped: list[str] = []
    for measurement in measurements:
        binding = binding_for_method(measurement.method_id)
        if binding.state == "BLOCKED":
            blocked.append(measurement.method_id)
            continue
        if binding.state == "UNMAPPED_CANONICAL_ID":
            unmapped.append(measurement.method_id)
            continue
        canonical_id = binding.canonical_measurement_id
        assert canonical_id is not None
        availability = getattr(
            measurement.availability_status,
            "value",
            str(measurement.availability_status),
        )
        candidate = {
            "canonical_measurement_id": canonical_id,
            "value": measurement.value,
            "unit": measurement.unit,
            "availability_status": availability,
            "method_ids": [measurement.method_id],
            "measurement_refs": [measurement.measurement_id],
        }
        existing = canonical.get(canonical_id)
        if existing is None:
            canonical[canonical_id] = candidate
            continue
        if (
            existing["unit"] != candidate["unit"]
            or existing["availability_status"] != candidate["availability_status"]
            or existing["value"] != candidate["value"]
        ):
            raise ValueError(
                f"Canonical measurement divergence for {canonical_id}: "
                f"{existing['method_ids']} vs {measurement.method_id}"
            )
        existing["method_ids"].append(measurement.method_id)
        existing["measurement_refs"].append(measurement.measurement_id)

    return {
        "measurements": [canonical[key] for key in sorted(canonical)],
        "blocked_method_ids": sorted(set(blocked)),
        "unmapped_method_ids": sorted(set(unmapped)),
    }
