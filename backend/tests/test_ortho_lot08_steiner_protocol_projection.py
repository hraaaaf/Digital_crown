import json
from pathlib import Path

from backend.services.cephalo_protocol_projection import project_steiner_static_protocol

ROOT=Path(__file__).resolve().parents[2]

def _canonical(cid,value,unit="?",status="AVAILABLE"):
    return {"canonical_measurement_id":cid,"value":value if status=="AVAILABLE" else None,"unit":unit,"availability_status":status,"measurement_refs":[f"m:{cid}"],"value_authority_method_id":f"METHOD:{cid}"}

def test_projection_preserves_source_locked_composition_and_display_only_norms():
    rows=[
      _canonical("M_SNA_DEG_V1",83.5),
      _canonical("M_SNB_DEG_V1",80.0),
      _canonical("M_ANB_DEG_V1",3.5),
      _canonical("M_SN_GOGN_DEG_V1",34.0),
    ]
    out=project_steiner_static_protocol(rows)
    assert out["protocol_profile_id"]=="STEINER_STATIC_PROTOCOL_PROFILE_V1"
    assert out["source_lock_gate"]["status"]=="SATISFIED"
    assert out["final_gate"]["status"]=="OPEN"
    assert len(out["rows"])==15
    sna=next(x for x in out["rows"] if x["canonical_measurement_id"]=="M_SNA_DEG_V1")
    assert sna["value"]==83.5 and sna["historical_reference"]==82.0 and sna["reference_delta"]==1.5
    assert sna["reference_authority"]=="REFERENCE_DISPLAY_ONLY"
    assert sna["classification_authority"] is False
    assert sna["interpretation_status"]=="REFERENCE_DISPLAY_ONLY_NO_CLASSIFICATION"

def test_projection_fails_closed_when_canonical_measurement_missing():
    out=project_steiner_static_protocol([])
    assert all(x["availability_status"]=="NOT_COMPUTABLE" and x["value"] is None for x in out["rows"])

def test_profile_json_keeps_manual_identities_and_no_treatment_authority():
    profile=json.loads((ROOT/"docs/audits/schemas/ortho_lot08_steiner_protocol_profile_v1.json").read_text(encoding="utf-8"))
    assert profile["explicit_manual_or_constructed_identities"]["D_Steiner_1959"].startswith("manual_explicit_only")
    assert profile["scope_resolutions"]["AUTONOMOUS_TREATMENT"]=="FORBIDDEN"
