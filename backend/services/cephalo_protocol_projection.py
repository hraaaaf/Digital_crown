"""Read-only protocol presentation projection from canonical LOT06 evidence.

No geometry, norms selection, diagnosis or treatment logic is created here.
The frozen protocol profile JSON is the source of composition/reference metadata.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

_PROFILE_PATH = Path(__file__).resolve().parents[1] / "data" / "cephalometry" / "steiner_protocol_profile_v1.json"
_TWEED_MERRIFIELD_PROFILE_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "cephalometry"
    / "tweed_merrifield_protocol_profile_v1.json"
)

_LABELS = {
    "M_SNA_DEG_V1":"SNA","M_SNB_DEG_V1":"SNB","M_ANB_DEG_V1":"ANB",
    "M_U1_NA_DEG_V1":"U1–NA angulaire","M_U1_NA_MM_V1":"U1–NA linéaire",
    "M_L1_NB_DEG_V1":"L1–NB angulaire","M_L1_NB_MM_V1":"L1–NB linéaire",
    "M_INTERINCISAL_DEG_V1":"Angle inter-incisif","M_OCCLUSAL_PLANE_SN_DEG_V1":"Plan occlusal–SN",
    "M_SN_GOGN_DEG_V1":"GoGn–SN","M_L1_GOGN_DEG_V1":"L1–GoGn",
    "M_SND_DEG_V1":"SND","M_POG_NB_MM_V1":"Pog–NB",
    "M_L1_DLINE_MM_V1":"L1–D line linéaire","M_L1_DLINE_DEG_V1":"L1–D line angulaire",
}


def _load_profile() -> dict[str, Any]:
    data=json.loads(_PROFILE_PATH.read_text(encoding="utf-8"))
    if data.get("status")!="SOURCE_LOCKED" or data.get("pre_code_gate",{}).get("status")!="SATISFIED":
        raise ValueError("Steiner protocol profile is not source-locked")
    return data


def _load_tweed_merrifield_profile() -> dict[str, Any]:
    data=json.loads(_TWEED_MERRIFIELD_PROFILE_PATH.read_text(encoding="utf-8"))
    if data.get("status")!="SOURCE_LOCKED" or data.get("pre_code_gate",{}).get("status")!="SATISFIED":
        raise ValueError("Tweed-Merrifield protocol profile is not source-locked")
    return data


def project_steiner_static_protocol(canonical_measurements: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    profile=_load_profile()
    by_id={str(x.get("canonical_measurement_id")):dict(x) for x in canonical_measurements}
    ref_set=profile["norm_sets"][0]
    references=dict(ref_set.get("values") or {})
    base=profile["layers"]["STEINER_1953_BASE"]["required_measurement_ids"]
    extension=profile["layers"]["STEINER_1959_EXTENSION"]["required_measurement_ids"]
    rows=[]
    for layer,ids in (("STEINER_1953_BASE",base),("STEINER_1959_EXTENSION",extension)):
        for cid in ids:
            projected=by_id.get(cid,{})
            status=str(projected.get("availability_status") or "NOT_COMPUTABLE")
            value=projected.get("value") if status=="AVAILABLE" else None
            reference=references.get(cid)
            delta=(float(value)-float(reference)) if value is not None and reference is not None else None
            rows.append({
                "canonical_measurement_id":cid,
                "label":_LABELS.get(cid,cid),
                "layer":layer,
                "value":value,
                "unit":projected.get("unit"),
                "availability_status":status,
                "measurement_refs":list(projected.get("measurement_refs") or []),
                "value_authority_method_id":projected.get("value_authority_method_id"),
                "historical_reference":reference,
                "reference_delta":delta,
                "reference_authority":ref_set["authority"],
                "classification_authority":bool(ref_set["classification_authority"]),
                "interpretation_status":"REFERENCE_DISPLAY_ONLY_NO_CLASSIFICATION",
            })
    return {
        "protocol_profile_id":profile["protocol_profile_id"],
        "source_lock_gate":dict(profile["pre_code_gate"]),
        "final_gate":dict(profile["final_gate"]),
        "norm_set":{
            "norm_set_id":ref_set["norm_set_id"],
            "authority":ref_set["authority"],
            "population":ref_set["population"],
            "applicability":ref_set["applicability"],
            "out_of_domain_behavior":ref_set["out_of_domain_behavior"],
        },
        "rows":rows,
        "required_manual_identities":dict(profile["explicit_manual_or_constructed_identities"]),
        "scope_resolutions":dict(profile["scope_resolutions"]),
    }


_TWEED_MERRIFIELD_LABELS = {
    "M_FH_GOME_DEG_V1": "FMA",
    "M_IMPA_GOME_DEG_V1": "IMPA",
    "M_FMIA_L1_FH_DEG_V1": "FMIA",
    "M_MERRIFIELD_Z_FH_DEG_V1": "Angle Z de Merrifield",
}


def project_tweed_merrifield_protocol(
    canonical_measurements: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    profile = _load_tweed_merrifield_profile()
    by_id = {
        str(item.get("canonical_measurement_id")): dict(item)
        for item in canonical_measurements
    }
    rows: list[dict[str, Any]] = []
    for section_id, section in profile["profiles"].items():
        for canonical_id in section.get("required_measurement_ids", []):
            projected = by_id.get(canonical_id, {})
            status = str(projected.get("availability_status") or "NOT_COMPUTABLE")
            rows.append(
                {
                    "canonical_measurement_id": canonical_id,
                    "label": _TWEED_MERRIFIELD_LABELS.get(canonical_id, canonical_id),
                    "profile_section": section_id,
                    "value": projected.get("value") if status == "AVAILABLE" else None,
                    "unit": projected.get("unit"),
                    "availability_status": status,
                    "measurement_refs": list(projected.get("measurement_refs") or []),
                    "value_authority_method_id": projected.get("value_authority_method_id"),
                    "reference_authority": "CONTEXT_ONLY_NO_RUNTIME_DELTA",
                    "classification_authority": False,
                    "interpretation_status": "RAW_MEASUREMENT_WITH_SOURCE_CONTEXT_ONLY",
                }
            )
    return {
        "protocol_profile_id": profile["protocol_profile_id"],
        "source_lock_gate": dict(profile["pre_code_gate"]),
        "final_gate": dict(profile["final_gate"]),
        "rows": rows,
        "reference_contexts": list(profile["reference_contexts"]),
        "historical_geometry_resolution": dict(profile["historical_geometry_resolution"]),
        "scope_resolutions": dict(profile["scope_resolutions"]),
    }


# R23-G2: presentation-only projections. Canonical measurements remain the sole
# numeric authority; a protocol membership is never itself evidence of a value.
_R23G2_ASSET_ROOT = Path(__file__).resolve().parents[1] / "data" / "cephalometry"
_R23G2_RICKETTS_ATLAS = _R23G2_ASSET_ROOT / "ricketts_atlas2009_complete33_protocol_profile_v1.json"
_R23G2_RICKETTS_GREGORET = _R23G2_ASSET_ROOT / "ricketts_gregoret13_protocol_profile_v1.json"
_R23G2_REFERENCE_LEDGER = _R23G2_ASSET_ROOT / "clinical_reference_profiles_v1.json"
_R23G2_AVAILABILITY = {"AVAILABLE", "MISSING", "INVALID", "NOT_APPLICABLE", "NOT_COMPUTABLE"}
_R23G2_BLOCKED_CONTRACT_MARKERS = (
    "BLOCKED", "PENDING_EQUIVALENCE", "IMPLEMENTATION_MISSING",
    "LEGACY_TO_AUDIT", "SOURCE_LOCK_REQUIRED",
)


def _r23g2_frozen_profile(path: Path, expected_id: str, expected_size: int, expected_status: str) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("measurements")
    if (data.get("protocol_id") != expected_id
            or data.get("status") != expected_status
            or not isinstance(rows, list) or len(rows) != expected_size
            or [row.get("order") for row in rows] != list(range(1, expected_size + 1))
            or len({row.get("measurement_id") for row in rows}) != expected_size
            or any(row.get("state") not in {"EXECUTABLE", "CONDITIONAL_EXECUTABLE"} for row in rows)
            or data.get("normative_state", {}).get("universal_classification") is not False):
        raise ValueError("R23-G2 source-locked protocol composition/gate is invalid")
    return data


def _r23g2_historical_ledger() -> dict[str, Any]:
    data = json.loads(_R23G2_REFERENCE_LEDGER.read_text(encoding="utf-8"))
    profiles = data.get("profiles") or {}
    if (data.get("status") != "WORKING_V1__DISPLAY_ONLY__NO_CLINICAL_APPROVAL"
            or data.get("rules", {}).get("formula_authority") is not False
            or data.get("rules", {}).get("normative_classification") is not False):
        raise ValueError("R23-G2 historical display ledger lacks fail-closed safeguards")
    for key, count, protocol in (
        ("mcnamara", 13, "MCNAMARA_1984_SINGLE_FILM_V1"),
        ("com", 10, "COM_DC_LEGACY_V1"),
    ):
        item = profiles.get(key) or {}
        rows = item.get("rows")
        if (item.get("protocol_profile_id") != protocol
                or not isinstance(rows, list) or len(rows) != count
                or [row.get("order") for row in rows] != list(range(1, count + 1))
                or len({row.get("measurement_id") for row in rows}) != count):
            raise ValueError("R23-G2 historical display ledger composition mismatch")
    return data


def _r23g2_rows(
    definitions: Sequence[Mapping[str, Any]],
    canonical_measurements: Sequence[Mapping[str, Any]],
    *,
    contract_key: str,
    profile_id: str,
) -> list[dict[str, Any]]:
    # Backend canonical projection has already passed active-chain and canonical
    # convergence checks. Do not read the parallel legacy metric payload here.
    by_id = {str(item.get("canonical_measurement_id")): item for item in canonical_measurements}
    rows = []
    for source in definitions:
        cid = str(source["measurement_id"])
        state = str(source[contract_key])
        projected = by_id.get(cid) or {}
        supplied_status = projected.get("availability_status")
        status = str(supplied_status) if supplied_status in _R23G2_AVAILABILITY else "NOT_COMPUTABLE"
        hold = any(marker in state for marker in _R23G2_BLOCKED_CONTRACT_MARKERS)
        raw_value = projected.get("value")
        # "AVAILABLE" only comes from verified typed backend evidence.
        # A missing, held or malformed measurement can never become numeric.
        import math
        valid = (not hold and status == "AVAILABLE"
                 and isinstance(raw_value, (int, float))
                 and not isinstance(raw_value, bool)
                 and math.isfinite(raw_value)
                 and bool(projected.get("measurement_refs"))
                 and bool(projected.get("value_authority_method_id")))
        if not valid and status == "AVAILABLE":
            status = "NOT_COMPUTABLE"
        if hold:
            status = "NOT_COMPUTABLE"
        rows.append({
            "order": int(source["order"]),
            "canonical_measurement_id": cid,
            "label": source.get("label") or cid,
            "unit": projected.get("unit") or ("deg" if "_DEG_" in cid else "mm" if "_MM_" in cid else None),
            "contract_state": state,
            "contract_gate": source.get("gate"),
            "source_contract": profile_id,
            "source_contracts": [profile_id],
            "availability_status": status,
            "value": raw_value if valid else None,
            "measurement_refs": list(projected.get("measurement_refs") or []) if valid else [],
            "value_authority_method_id": projected.get("value_authority_method_id") if valid else None,
            "classification_authority": False,
            "interpretation_status": "REFERENCE_DISPLAY_ONLY_NO_CLASSIFICATION",
        })
    return rows


def _r23g2_source_locked_protocol(
    path: Path,
    protocol: str,
    count: int,
    status: str,
    canonical_measurements: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    data = _r23g2_frozen_profile(path, protocol, count, status)
    rows = _r23g2_rows(
        data["measurements"], canonical_measurements,
        contract_key="state", profile_id=protocol,
    )
    return {
        "protocol_profile_id": protocol,
        "profile_status": data["status"],
        "source_lock_gate": "COMPOSITION_AND_EXECUTION_CONTRACTS_SOURCE_LOCKED",
        "classification_authority": False,
        "rows": rows,
    }


def project_ricketts_atlas2009_protocol(
    canonical_measurements: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return _r23g2_source_locked_protocol(
        _R23G2_RICKETTS_ATLAS,
        "RICKETTS_ATLAS_2009_COMPLETE_33_PROTOCOL_V1",
        33,
        "COMPOSITION_AND_EXECUTION_CONTRACTS_SOURCE_LOCKED__ALL_33_EXECUTABLE_OR_CONDITIONAL",
        canonical_measurements,
    )


def project_ricketts_gregoret13_protocol(
    canonical_measurements: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return _r23g2_source_locked_protocol(
        _R23G2_RICKETTS_GREGORET,
        "RICKETTS_GREGORET_1997_SUMMARIZED_13_PROTOCOL_V1",
        13,
        "COMPOSITION_AND_EXECUTION_CONTRACTS_SOURCE_LOCKED__FAIL_CLOSED",
        canonical_measurements,
    )


def _r23g2_reference_protocol(
    name: str, canonical_measurements: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    ledger = _r23g2_historical_ledger()
    data = ledger["profiles"][name]
    return {
        "protocol_profile_id": data["protocol_profile_id"],
        "profile_status": ledger["status"],
        "source_lock_gate": "HISTORICAL_WORKING_REFERENCE_ONLY",
        "classification_authority": False,
        "rows": _r23g2_rows(
            data["rows"], canonical_measurements,
            contract_key="contract_state", profile_id=data["protocol_profile_id"],
        ),
    }


def project_mcnamara_reference_protocol(
    canonical_measurements: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return _r23g2_reference_protocol("mcnamara", canonical_measurements)


def project_com_reference_protocol(
    canonical_measurements: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return _r23g2_reference_protocol("com", canonical_measurements)
