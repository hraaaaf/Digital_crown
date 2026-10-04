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
