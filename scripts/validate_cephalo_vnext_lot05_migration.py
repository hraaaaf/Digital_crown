"""Isolated LOT05 V1<->V2 migration proof harness. Not product runtime."""
from __future__ import annotations
import copy, hashlib, json\nfrom datetime import datetime
from typing import Any, Mapping

class Lot05MigrationError(ValueError): pass

def canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",",":"), ensure_ascii=False).encode()

def sha256(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()

_SOFT = {"Ls_soft","Li_soft","Sn_soft","Pog_soft","Prn","Cm","Ls2","Li2","Gn_soft","Me_soft","G_soft","N_soft","C_point"}
_DENTAL = {"L1_incisal","U1_incisal","U1_apex","L1_apex","U6","L6"}
_ANCHORS = {"Occ_Ant","Occ_Post"}

def _domain(cid: str) -> str:
    if cid in _SOFT: return "SOFT"
    if cid in _DENTAL: return "DENTAL"
    if cid in _ANCHORS: return "CONSTRUCTION_ANCHOR"
    return "HARD"

def migrate_v1_to_v2(v1: Mapping[str, Any], *, patient_id: int, width: int, height: int, migrated_at: str = "2026-10-01T00:00:00+00:00") -> dict[str, Any]:
    try:
        parsed_at=datetime.fromisoformat(migrated_at)
    except (TypeError, ValueError) as exc:
        raise Lot05MigrationError("Invalid migration timestamp") from exc
    if parsed_at.tzinfo is None or parsed_at.utcoffset() is None:
        raise Lot05MigrationError("Migration timestamp must be timezone-aware")
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
        registry.append({"canonical_id":cid,"aliases":[],"identity_version":"V1_RUNTIME_ID_PRESERVED","semantic_status":"LEGACY_AMBIGUOUS","tissue_domain":_domain(cid),"analysis_scope":None})
    calibration=[s for s in source.get("sources",[]) if isinstance(s,dict) and s.get("kind")=="calibration"]
    if len(calibration)>1: raise Lot05MigrationError("Multiple calibration sources are ambiguous")
    calibration_ref=calibration[0].get("evidence_id") if calibration else None
    source_patient_ids={s.get("patient_id") for s in source.get("sources",[]) if isinstance(s,dict) and isinstance(s.get("patient_id"),int)}
    if source_patient_ids and source_patient_ids != {patient_id}: raise Lot05MigrationError("Patient identity mismatch")
    return {
      "schema_version":"CEPHALO_CANONICAL_SCHEMA_V2","case_id":case_id,"patient_id":patient_id,
      "evidence_graph_version":"_evidence_graph_v1","landmark_registry":registry,
      "current_landmark_refs":copy.deepcopy(refs),
      "coordinate_space":{"version":"V1_IMAGE_PIXEL_SPACE","unit":"px","source_width_px":width,"source_height_px":height,"calibration_ref":calibration_ref},
      "quality_metadata":{"model_id":None,"model_sha256":None,"raw_score":None,"score_semantics":"NOT_AVAILABLE","score_calibration_ref":None},
      "migration":{"migration_version":"CEPHALO_V1_TO_V2_MIGRATION_V1","source_schema":"_evidence_graph_v1","source_sha256":sha256(source),"migrated_at":migrated_at,"compatibility_class":"LOSSLESS_V1","opaque_legacy_payload":source}
    }

def validate_v2_identity_registry(v2: Mapping[str, Any]) -> None:
    registry=v2.get("landmark_registry")
    if not isinstance(registry,list): raise Lot05MigrationError("Missing landmark registry")
    canonical=set()
    aliases=set()
    for item in registry:
        if not isinstance(item,dict) or not isinstance(item.get("canonical_id"),str) or not item["canonical_id"]:
            raise Lot05MigrationError("Malformed canonical landmark identity")
        cid=item["canonical_id"]
        if cid in canonical or cid in aliases: raise Lot05MigrationError("Canonical landmark identity collision")
        canonical.add(cid)
        raw_aliases=item.get("aliases",[])
        if not isinstance(raw_aliases,list): raise Lot05MigrationError("Malformed aliases")
        for alias in raw_aliases:
            if not isinstance(alias,str) or not alias or alias==cid or alias in aliases or alias in canonical:
                raise Lot05MigrationError("Landmark alias collision")
            aliases.add(alias)

def roundtrip_v2_to_v1(v2: Mapping[str, Any]) -> dict[str, Any]:
    validate_v2_identity_registry(v2)
    migration=v2.get("migration",{})
    if migration.get("compatibility_class")!="LOSSLESS_V1": raise Lot05MigrationError("V2 object is not lossless-V1")
    source=migration.get("opaque_legacy_payload")
    if not isinstance(source,dict) or sha256(source)!=migration.get("source_sha256"):
        raise Lot05MigrationError("V1 source snapshot hash mismatch")
    if source.get("current_landmark_refs") != v2.get("current_landmark_refs"):
        raise Lot05MigrationError("Current landmark refs changed during migration")
    return copy.deepcopy(source)
