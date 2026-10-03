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
    _b("CRANIOM_SITUATION_A_MM_V1",None,"BLOCKED","LEGACY_LANDMARK_IDENTITY_BRIDGE_REQUIRED"),
    _b("CRANIOM_SITUATION_B_MM_V1",None,"BLOCKED","LEGACY_LANDMARK_IDENTITY_BRIDGE_REQUIRED"),
    _b("CRANIOM_AB_PRIME_MM_V1",None,"BLOCKED","LEGACY_LANDMARK_IDENTITY_BRIDGE_REQUIRED"),
    _b("CRANIOM_FACIAL_DEPTH_MM_V1",None,"BLOCKED","LEGACY_LANDMARK_IDENTITY_BRIDGE_REQUIRED"),
    _b("CRANIOM_U1_FRANKFORT_DEG_V1",None,"BLOCKED","LEGACY_LANDMARK_IDENTITY_BRIDGE_REQUIRED"),
    _b("CRANIOM_L1_DOWNS_DEG_V1",None,"BLOCKED","LEGACY_LANDMARK_IDENTITY_BRIDGE_REQUIRED"),
    _b("CRANIOM_INTERINCISAL_DEG_V1","M_INTERINCISAL_DEG_V1","MAPPED","EXACT_GEOMETRY_IDENTITY_BINDING"),
    _b("STEINER_SNA_DEG_V1","M_SNA_DEG_V1","MAPPED","EXACT_GEOMETRY_IDENTITY_BINDING"),
    _b("STEINER_SNB_DEG_V1","M_SNB_DEG_V1","MAPPED","EXACT_GEOMETRY_IDENTITY_BINDING"),
    _b("STEINER_ANB_DEG_V1","M_ANB_DEG_V1","MAPPED","EXACT_GEOMETRY_IDENTITY_BINDING"),
    _b("STEINER_SN_MP_DEG_V1",None,"BLOCKED","LEGACY_LANDMARK_IDENTITY_BRIDGE_REQUIRED"),
    _b("STEINER_U1_NA_DEG_V1","M_U1_NA_DEG_V1","MAPPED","EXACT_GEOMETRY_IDENTITY_BINDING"),
    _b("STEINER_L1_NB_DEG_V1","M_L1_NB_DEG_V1","MAPPED","EXACT_GEOMETRY_IDENTITY_BINDING"),
    _b("TWEED_FMA_DEG_V1",None,"BLOCKED","LEGACY_LANDMARK_IDENTITY_BRIDGE_REQUIRED"),
    _b("TWEED_IMPA_DEG_V1","M_IMPA_GOME_DEG_V1","MAPPED","EXACT_L1_APEX_INCISAL_GO_ME_IDENTITY_BINDING"),
    _b("TWEED_FMIA_DEG_V1",None,"BLOCKED","LEGACY_LANDMARK_IDENTITY_BRIDGE_REQUIRED"),
    _b("MERRIFIELD_Z_ANGLE_DEG_V1",None,"UNMAPPED_CANONICAL_ID","NO_CANONICAL_M_ID_SOURCE_LOCKED"),
    _b("TWEED_FMA_CANONICAL_DEG_V2","M_FH_GOME_DEG_V1","MAPPED","CANONICAL_V2_EXPLICIT_IDENTITIES"),
    _b("TWEED_FMIA_CANONICAL_DEG_V2","M_FMIA_L1_FH_DEG_V1","MAPPED","CANONICAL_V2_EXPLICIT_IDENTITIES"),
    _b("MCNAMARA_CO_A_CANONICAL_MM_V2","M_CO_A_MM_V1","MAPPED","CANONICAL_V2_EXPLICIT_IDENTITIES"),
    _b("MCNAMARA_CO_GN_CANONICAL_MM_V2","M_CO_GN_ANATOMIC_MM_V1","MAPPED","CANONICAL_V2_EXPLICIT_IDENTITIES"),
    _b("MCNAMARA_A_NPERP_CANONICAL_MM_V2","M_A_NPERP_MM_V1","MAPPED","CANONICAL_V2_EXPLICIT_IDENTITIES"),
    _b("MCNAMARA_POG_NPERP_CANONICAL_MM_V2","M_POG_NPERP_MM_V1","MAPPED","CANONICAL_V2_EXPLICIT_IDENTITIES"),
    _b("DOWNS_FACIAL_ANGLE_CANONICAL_DEG_V2","M_DOWNS_FACIAL_ANGLE_NPOG_FH_ACUTE_DEG_V1","MAPPED","CANONICAL_V2_SPLIT_ANGLE_CONVENTION"),
    _b("DOWNS_Y_AXIS_CANONICAL_DEG_V2","M_DOWNS_Y_AXIS_SGN_FH_DEG_V1","MAPPED","CANONICAL_V2_EXPLICIT_IDENTITIES"),
    _b("RICKETTS_FACIAL_DEPTH_CANONICAL_DEG_V2","M_RICKETTS_FACIAL_DEPTH_NPOG_FH_POSTERIOR_DEG_V1","MAPPED","CANONICAL_V2_SPLIT_ANGLE_CONVENTION"),
    _b("RICKETTS_FACIAL_AXIS_CANONICAL_DEG_V2","M_FACIAL_AXIS_RICKETTS_DEG_V1","MAPPED","CANONICAL_V2_EXPLICIT_PT_RICKETTS_AND_CONSTRUCTED_GN"),
    _b("RICKETTS_CONVEXITY_CANONICAL_MM_V2","M_MAXILLARY_CONVEXITY_A_NPOG_MM_V1","MAPPED","CANONICAL_V2_EXPLICIT_IDENTITIES"),
    _b("RICKETTS_E_LINE_LS_CANONICAL_MM_V3","M_LS_EPLANE_MM_V1","MAPPED","CANONICAL_V2_EXPLICIT_IDENTITIES"),
    _b("RICKETTS_E_LINE_LI_CANONICAL_MM_V3","M_LI_EPLANE_MM_V1","MAPPED","CANONICAL_V2_EXPLICIT_IDENTITIES"),
    _b("MERRIFIELD_Z_CANONICAL_DEG_V2","M_MERRIFIELD_Z_FH_DEG_V1","MAPPED","CANONICAL_V2_EXPLICIT_IDENTITIES"),
    _b("DOWNS_FACIAL_ANGLE_DEG_V1",None,"BLOCKED","ANGLE_CONVENTION_COLLISION_45_VS_135"),
    _b("DOWNS_Y_AXIS_DEG_V1",None,"UNMAPPED_CANONICAL_ID","NO_CANONICAL_M_ID_SOURCE_LOCKED"),
    _b("MCNAMARA_CO_A_MM_V1",None,"BLOCKED","LEGACY_LANDMARK_IDENTITY_BRIDGE_REQUIRED"),
    _b("MCNAMARA_CO_GN_MM_V1",None,"BLOCKED","LEGACY_LANDMARK_IDENTITY_BRIDGE_REQUIRED"),
    _b("MCNAMARA_ANS_ME_MM_V1","M_ANS_ME_MM_V1","MAPPED","EXACT_GEOMETRY_IDENTITY_BINDING"),
    _b("M_A_NPERP_MM_V1",None,"BLOCKED","LEGACY_LANDMARK_IDENTITY_BRIDGE_REQUIRED"),
    _b("M_POG_NPERP_MM_V1",None,"BLOCKED","LEGACY_LANDMARK_IDENTITY_BRIDGE_REQUIRED"),
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



CANONICAL_CONVERGENCE_RULES = {}



def _availability_value(measurement) -> str:
    return getattr(
        measurement.availability_status,
        "value",
        str(measurement.availability_status),
    )


def _assert_common_state(canonical_id: str, measurements: list) -> None:
    first = measurements[0]
    first_status = _availability_value(first)
    for item in measurements[1:]:
        if item.unit != first.unit or _availability_value(item) != first_status:
            raise ValueError(
                f"Canonical measurement divergence for {canonical_id}: "
                "unit/availability mismatch"
            )


def _resolve_converged_group(canonical_id: str, measurements: list) -> dict[str, object]:
    _assert_common_state(canonical_id, measurements)
    rule = CANONICAL_CONVERGENCE_RULES.get(canonical_id)
    by_method = {item.method_id: item for item in measurements}
    authority = measurements[0]

    if rule is not None:
        authority = by_method.get(rule["authoritative_method_id"], authority)
        mode = rule["equivalence"]
        for item in measurements:
            if item is authority:
                continue
            if authority.value is None or item.value is None:
                if authority.value != item.value:
                    raise ValueError(
                        f"Canonical measurement divergence for {canonical_id}: missing value mismatch"
                    )
                continue
            if mode == "EXACT_VALUE_UNIT_STATUS":
                equivalent = authority.value == item.value
            elif mode == "AUTHORITATIVE_VALUE_ROUNDED_TO_1DP_EQUALS_LEGACY_VALUE":
                equivalent = round(float(authority.value), 1) == float(item.value)
            else:
                raise ValueError(f"Unsupported canonical convergence mode: {mode}")
            if not equivalent:
                raise ValueError(
                    f"Canonical measurement divergence for {canonical_id}: "
                    f"{authority.method_id} vs {item.method_id}"
                )
    else:
        for item in measurements[1:]:
            if item.value != authority.value:
                raise ValueError(
                    f"Canonical measurement divergence for {canonical_id}: "
                    f"{authority.method_id} vs {item.method_id}"
                )

    return {
        "canonical_measurement_id": canonical_id,
        "value": authority.value,
        "unit": authority.unit,
        "availability_status": _availability_value(authority),
        "value_authority_method_id": authority.method_id,
        "method_ids": sorted(item.method_id for item in measurements),
        "measurement_refs": sorted(item.measurement_id for item in measurements),
    }


def project_canonical_measurements(measurements) -> dict[str, object]:
    """Collapse mapped typed methods onto canonical M_* identities.

    Historical methods may share one canonical geometry only when their
    preregistered convergence rule is satisfied. Blocked/unmapped methods are
    reported but never promoted. Persisted measurement objects are not mutated.
    """
    grouped: dict[str, list] = {}
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
        grouped.setdefault(canonical_id, []).append(measurement)

    return {
        "measurements": [
            _resolve_converged_group(canonical_id, grouped[canonical_id])
            for canonical_id in sorted(grouped)
        ],
        "blocked_method_ids": sorted(set(blocked)),
        "unmapped_method_ids": sorted(set(unmapped)),
    }
