"""Isolated LOT05 V1<->V2 migration proof harness. Not product runtime."""
from __future__ import annotations
import copy, hashlib, json, math
from datetime import datetime
from typing import Any, Mapping

class Lot05MigrationError(ValueError): pass

def canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
def sha256(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()
def context_sha(patient_id:int,width:int,height:int)->str:
    return hashlib.sha256(json.dumps({"patient_id":patient_id,"source_width_px":width,"source_height_px":height},sort_keys=True,separators=(",",":")).encode()).hexdigest()

_SOFT={"Ls_soft","Li_soft","Sn_soft","Pog_soft","Prn","Cm","Ls2","Li2","Gn_soft","Me_soft","G_soft","N_soft","C_point"}
_DENTAL={"L1_incisal","U1_incisal","U1_apex","L1_apex","U6","L6"}
_ANCHORS={"Occ_Ant","Occ_Post"}
def _domain(cid:str)->str:
    if cid in _SOFT:return "SOFT"
    if cid in _DENTAL:return "DENTAL"
    if cid in _ANCHORS:return "CONSTRUCTION_ANCHOR"
    return "HARD"
def _aware(value:Any,label:str)->None:
    try: dt=datetime.fromisoformat(value)
    except (TypeError,ValueError) as exc: raise Lot05MigrationError(f"Invalid {label}") from exc
    if dt.tzinfo is None or dt.utcoffset() is None: raise Lot05MigrationError(f"{label} must be timezone-aware")
def _finite(value:Any)->bool:
    return not isinstance(value,bool) and isinstance(value,(int,float)) and math.isfinite(value)

def migrate_v1_to_v2(v1:Mapping[str,Any],*,patient_id:int,width:int,height:int,migrated_at:str)->dict[str,Any]:
    if isinstance(patient_id,bool) or not isinstance(patient_id,int) or patient_id<1: raise Lot05MigrationError("Invalid patient identity")
    if any(isinstance(v,bool) or not isinstance(v,int) or v<1 for v in (width,height)): raise Lot05MigrationError("Invalid source image dimensions")
    _aware(migrated_at,"migration timestamp")
    source=copy.deepcopy(dict(v1))
    if source.get("schema_version")!="CEPHALO_EVIDENCE_V1": raise Lot05MigrationError("Unsupported V1 evidence schema")
    rev=source.get("revision")
    if isinstance(rev,bool) or not isinstance(rev,int) or rev<1: raise Lot05MigrationError("Invalid V1 revision")
    case_id=source.get("case_id"); landmarks=source.get("landmarks"); refs=source.get("current_landmark_refs")
    if not isinstance(case_id,str) or not case_id or not isinstance(landmarks,list) or not landmarks or not isinstance(refs,list): raise Lot05MigrationError("V1 identity incomplete")
    by_ref={}
    for item in landmarks:
        if not isinstance(item,dict) or not isinstance(item.get("evidence_id"),str) or not item["evidence_id"] or not isinstance(item.get("landmark_id"),str) or not item["landmark_id"]: raise Lot05MigrationError("Malformed landmark evidence")
        if item["evidence_id"] in by_ref: raise Lot05MigrationError("Duplicate landmark evidence_id")
        if not _finite(item.get("x")) or not _finite(item.get("y")): raise Lot05MigrationError("Landmark coordinates must be finite")
        origin=item.get("origin")
        if origin=="SRPOSE38_AUTO":
            if not all(isinstance(item.get(k),str) and item[k] for k in ("model_id","model_sha256","pipeline_version")): raise Lot05MigrationError("Automatic landmark lacks model provenance")
        elif origin=="MANUAL_CORRECTED":
            if not _finite(item.get("original_auto_x")) or not _finite(item.get("original_auto_y")): raise Lot05MigrationError("Correction lacks original automatic coordinates")
            if not isinstance(item.get("validated_by"),str) or not item["validated_by"]: raise Lot05MigrationError("Correction lacks validator")
            _aware(item.get("validated_at"),"correction audit timestamp")
        elif origin!="MANUAL": raise Lot05MigrationError("Unsupported landmark provenance")
        by_ref[item["evidence_id"]]=item
    if len(refs)!=len(set(refs)) or any(not isinstance(r,str) or r not in by_ref for r in refs): raise Lot05MigrationError("Ambiguous current refs")
    if len({by_ref[r]["landmark_id"] for r in refs})!=len(refs): raise Lot05MigrationError("Multiple current refs for one landmark")
    sources=source.get("sources")
    if not isinstance(sources,list) or not sources or any(not isinstance(s,dict) for s in sources): raise Lot05MigrationError("Malformed source evidence")
    source_ids=set()
    for s in sources:
        eid=s.get("evidence_id")
        if not isinstance(eid,str) or not eid or eid in source_ids: raise Lot05MigrationError("Invalid/duplicate source evidence_id")
        source_ids.add(eid)
        if isinstance(s.get("patient_id"),bool) or s.get("patient_id")!=patient_id: raise Lot05MigrationError("Patient identity mismatch")
    if len([s for s in sources if s.get("kind")=="lateral_ceph"])!=1: raise Lot05MigrationError("Expected one lateral cephalogram source")
    calibration=[s for s in sources if s.get("kind")=="calibration"]
    if len(calibration)>1: raise Lot05MigrationError("Ambiguous calibration")
    calibration_ref=calibration[0]["evidence_id"] if calibration else None
    registry=[{"canonical_id":cid,"aliases":[],"identity_version":"V1_RUNTIME_ID_PRESERVED","semantic_status":"LEGACY_AMBIGUOUS","tissue_domain":_domain(cid),"analysis_scope":None} for cid in sorted({x["landmark_id"] for x in landmarks})]
    active=[]
    for ref in refs:
        e=by_ref[ref]
        active.append({"evidence_ref":ref,"canonical_id":e["landmark_id"],"origin":e["origin"],"x":e["x"],"y":e["y"],"model_id":e.get("model_id"),"model_sha256":e.get("model_sha256"),"pipeline_version":e.get("pipeline_version"),"original_auto_x":e.get("original_auto_x"),"original_auto_y":e.get("original_auto_y"),"validated_by":e.get("validated_by"),"validated_at":e.get("validated_at")})
    return {"schema_version":"CEPHALO_CANONICAL_SCHEMA_V2","case_id":case_id,"patient_id":patient_id,"evidence_graph_version":"_evidence_graph_v1","landmark_registry":registry,"current_landmark_refs":copy.deepcopy(refs),"active_landmarks":active,"coordinate_space":{"version":"V1_IMAGE_PIXEL_SPACE","unit":"px","source_width_px":width,"source_height_px":height,"calibration_ref":calibration_ref},"quality_metadata":{"model_id":None,"model_sha256":None,"raw_score":None,"score_semantics":"NOT_AVAILABLE","score_calibration_ref":None},"migration":{"migration_version":"CEPHALO_V1_TO_V2_MIGRATION_V1","source_schema":"_evidence_graph_v1","source_sha256":sha256(source),"migration_context_sha256":context_sha(patient_id,width,height),"migrated_at":migrated_at,"compatibility_class":"LOSSLESS_V1","opaque_legacy_payload":source}}

def validate_v2_identity_registry(v2:Mapping[str,Any])->None:
    registry=v2.get("landmark_registry")
    if not isinstance(registry,list) or not registry: raise Lot05MigrationError("Missing landmark registry")
    canonical=set(); aliases=set()
    for item in registry:
        if not isinstance(item,dict) or not isinstance(item.get("canonical_id"),str) or not item["canonical_id"]: raise Lot05MigrationError("Malformed canonical identity")
        cid=item["canonical_id"]
        if cid in canonical or cid in aliases: raise Lot05MigrationError("Canonical identity collision")
        canonical.add(cid)
        aa=item.get("aliases",[])
        if not isinstance(aa,list): raise Lot05MigrationError("Malformed aliases")
        for alias in aa:
            if not isinstance(alias,str) or not alias or alias==cid or alias in aliases or alias in canonical: raise Lot05MigrationError("Alias collision")
            aliases.add(alias)

def _active_from_source(source:Mapping[str,Any])->list[dict[str,Any]]:
    by_ref={x.get("evidence_id"):x for x in source.get("landmarks",[]) if isinstance(x,dict)}
    result=[]
    for ref in source.get("current_landmark_refs",[]):
        e=by_ref.get(ref)
        if not isinstance(e,dict): raise Lot05MigrationError("Active source evidence missing")
        result.append({"evidence_ref":ref,"canonical_id":e.get("landmark_id"),"origin":e.get("origin"),"x":e.get("x"),"y":e.get("y"),"model_id":e.get("model_id"),"model_sha256":e.get("model_sha256"),"pipeline_version":e.get("pipeline_version"),"original_auto_x":e.get("original_auto_x"),"original_auto_y":e.get("original_auto_y"),"validated_by":e.get("validated_by"),"validated_at":e.get("validated_at")})
    return result

def roundtrip_v2_to_v1(v2:Mapping[str,Any])->dict[str,Any]:
    validate_v2_identity_registry(v2)
    m=v2.get("migration",{})
    if m.get("compatibility_class")!="LOSSLESS_V1": raise Lot05MigrationError("Not lossless V1")
    source=m.get("opaque_legacy_payload")
    if not isinstance(source,dict) or sha256(source)!=m.get("source_sha256"): raise Lot05MigrationError("Source snapshot hash mismatch")
    if source.get("case_id")!=v2.get("case_id"): raise Lot05MigrationError("Case identity drift")
    cs=v2.get("coordinate_space",{})
    if context_sha(v2.get("patient_id"),cs.get("source_width_px"),cs.get("source_height_px"))!=m.get("migration_context_sha256"): raise Lot05MigrationError("Migration context drift")
    if source.get("current_landmark_refs")!=v2.get("current_landmark_refs"): raise Lot05MigrationError("Current refs drift")
    if v2.get("active_landmarks")!=_active_from_source(source): raise Lot05MigrationError("Active provenance drift")
    expected_registry=[{"canonical_id":cid,"aliases":[],"identity_version":"V1_RUNTIME_ID_PRESERVED","semantic_status":"LEGACY_AMBIGUOUS","tissue_domain":_domain(cid),"analysis_scope":None} for cid in sorted({x.get("landmark_id") for x in source.get("landmarks",[]) if isinstance(x,dict)})]
    if v2.get("landmark_registry") != expected_registry: raise Lot05MigrationError("Registry metadata drift")
    if cs.get("version")!="V1_IMAGE_PIXEL_SPACE" or cs.get("unit")!="px": raise Lot05MigrationError("Coordinate-space semantics drift")
    q=v2.get("quality_metadata")
    if q != {"model_id":None,"model_sha256":None,"raw_score":None,"score_semantics":"NOT_AVAILABLE","score_calibration_ref":None}: raise Lot05MigrationError("Quality metadata drift")
    cal=[s for s in source.get("sources",[]) if isinstance(s,dict) and s.get("kind")=="calibration"]
    if cs.get("calibration_ref")!=(cal[0].get("evidence_id") if len(cal)==1 else None): raise Lot05MigrationError("Calibration drift")
    return copy.deepcopy(source)
