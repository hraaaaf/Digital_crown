"""Isolated LOT05 V1<->V2 migration proof harness. Not product runtime."""
from __future__ import annotations
import copy, hashlib, json
from typing import Any, Mapping

class Lot05MigrationError(ValueError): pass

def canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",",":"), ensure_ascii=False).encode()

def sha256(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()

def migrate_v1_to_v2(v1: Mapping[str, Any], *, patient_id: int, width: int, height: int) -> dict[str, Any]:
    source=copy.deepcopy(dict(v1))
    case_id=source.get("case_id")
    landmarks=source.get("landmarks")
    refs=source.get("current_landmark_refs")
    if not isinstance(case_id,str) or not case_id or not isinstance(landmarks,list) or not isinstance(refs,list):
        raise Lot05MigrationError("V1 graph lacks provable case/landmark/current-ref identity")
    by_ref={}
    for item in landmarks:
        if not isinstance(item,dict) or not isinstance(item.get("evidence_id"),str) or not isinstance(item.get("landmark_id"),str):
            raise Lot05MigrationError("Malformed V1 landmark evidence")
        if item["evidence_id"] in by_ref: raise Lot05MigrationError("Duplicate evidence_id")
        by_ref[item["evidence_id"]]=item
    if len(refs)!=len(set(refs)) or any(ref not in by_ref for ref in refs):
        raise Lot05MigrationError("Ambiguous current_landmark_refs")
    current_ids=[by_ref[r]["landmark_id"] for r in refs]
    if len(current_ids)!=len(set(current_ids)): raise Lot05MigrationError("Multiple current refs for one landmark")
    registry=[]
    for cid in sorted(set(item["landmark_id"] for item in landmarks)):
        registry.append({"canonical_id":cid,"aliases":[],"identity_version":"V1_RUNTIME_ID_PRESERVED","semantic_status":"LEGACY_AMBIGUOUS","tissue_domain":"CONSTRUCTION_ANCHOR" if cid in {"Occ_Ant","Occ_Post"} else "HARD","analysis_scope":None})
    calibration=[s for s in source.get("sources",[]) if isinstance(s,dict) and s.get("kind")=="calibration"]
    calibration_ref=calibration[0].get("evidence_id") if len(calibration)==1 else None
    return {
      "schema_version":"CEPHALO_CANONICAL_SCHEMA_V2","case_id":case_id,"patient_id":patient_id,
      "evidence_graph_version":"_evidence_graph_v1","landmark_registry":registry,
      "current_landmark_refs":copy.deepcopy(refs),
      "coordinate_space":{"version":"V1_IMAGE_PIXEL_SPACE","unit":"px","source_width_px":width,"source_height_px":height,"calibration_ref":calibration_ref},
      "quality_metadata":{"model_id":None,"model_sha256":None,"raw_score":None,"score_semantics":"NOT_AVAILABLE","score_calibration_ref":None},
      "migration":{"migration_version":"CEPHALO_V1_TO_V2_MIGRATION_V1","source_schema":"_evidence_graph_v1","source_sha256":sha256(source),"compatibility_class":"LOSSLESS_V1","opaque_legacy_payload":source}
    }

def roundtrip_v2_to_v1(v2: Mapping[str, Any]) -> dict[str, Any]:
    migration=v2.get("migration",{})
    if migration.get("compatibility_class")!="LOSSLESS_V1": raise Lot05MigrationError("V2 object is not lossless-V1")
    source=migration.get("opaque_legacy_payload")
    if not isinstance(source,dict) or sha256(source)!=migration.get("source_sha256"):
        raise Lot05MigrationError("V1 source snapshot hash mismatch")
    if source.get("current_landmark_refs") != v2.get("current_landmark_refs"):
        raise Lot05MigrationError("Current landmark refs changed during migration")
    return copy.deepcopy(source)
