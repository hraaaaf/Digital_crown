import copy
import pytest
from scripts.validate_cephalo_vnext_lot05_migration import Lot05MigrationError, migrate_v1_to_v2, roundtrip_v2_to_v1

def v1():
    return {"schema_version":"CEPHALO_EVIDENCE_V1","case_id":"case:1","revision":3,
      "sources":[{"evidence_id":"source:image","kind":"lateral_ceph"},{"evidence_id":"cal:1","kind":"calibration","ratio":0.1}],
      "landmarks":[
        {"evidence_id":"lm:auto:A","landmark_id":"A","x":10.0,"y":20.0,"origin":"SRPOSE38_AUTO"},
        {"evidence_id":"lm:auto:B","landmark_id":"B","x":30.0,"y":40.0,"origin":"SRPOSE38_AUTO"},
        {"evidence_id":"lm:r3:A","landmark_id":"A","x":11.0,"y":21.0,"origin":"MANUAL_CORRECTED","original_auto_x":10.0,"original_auto_y":20.0,"validated_by":"99","validated_at":"2026-09-10T15:35:00+00:00"}],
      "current_landmark_refs":["lm:r3:A"],
      "measurements":[{"measurement_id":"SNA","value":81.0}],
      "calibration_status":"clinician_confirmed","unknown_legacy":{"keep":True}}

def test_lossless_roundtrip_preserves_v1_exactly():
    source=v1(); v2=migrate_v1_to_v2(source,patient_id=7,width=1935,height=2400)
    assert roundtrip_v2_to_v1(v2)==source

def test_current_refs_and_correction_lineage_preserved():
    source=v1(); v2=migrate_v1_to_v2(source,patient_id=7,width=1935,height=2400)
    assert v2["current_landmark_refs"]==["lm:r3:A"]
    restored=roundtrip_v2_to_v1(v2)
    corrected=next(x for x in restored["landmarks"] if x["evidence_id"]=="lm:r3:A")
    assert corrected["origin"]=="MANUAL_CORRECTED"
    assert corrected["original_auto_x"]==10.0 and corrected["validated_by"]=="99"
    assert "lm:auto:B" not in restored["current_landmark_refs"]

def test_calibration_and_measurements_are_not_recomputed():
    source=v1(); v2=migrate_v1_to_v2(source,patient_id=7,width=1935,height=2400)
    assert v2["coordinate_space"]["calibration_ref"]=="cal:1"
    restored=roundtrip_v2_to_v1(v2)
    assert restored["measurements"]==source["measurements"]
    assert restored["calibration_status"]=="clinician_confirmed"

def test_unknown_legacy_data_is_losslessly_preserved():
    source=v1(); restored=roundtrip_v2_to_v1(migrate_v1_to_v2(source,patient_id=7,width=1935,height=2400))
    assert restored["unknown_legacy"]=={"keep":True}

def test_missing_or_unknown_current_refs_fail_closed():
    source=v1(); source.pop("current_landmark_refs")
    with pytest.raises(Lot05MigrationError): migrate_v1_to_v2(source,patient_id=7,width=1935,height=2400)
    source=v1(); source["current_landmark_refs"]=["does:not:exist"]
    with pytest.raises(Lot05MigrationError): migrate_v1_to_v2(source,patient_id=7,width=1935,height=2400)

def test_roundtrip_detects_tampering():
    v2=migrate_v1_to_v2(v1(),patient_id=7,width=1935,height=2400)
    v2["migration"]["opaque_legacy_payload"]["revision"]=999
    with pytest.raises(Lot05MigrationError): roundtrip_v2_to_v1(v2)


def test_semantic_domains_are_not_silently_flattened_to_hard_tissue():
    source=v1()
    source["landmarks"].extend([
      {"evidence_id":"lm:soft","landmark_id":"Pog_soft","x":1.0,"y":2.0,"origin":"MANUAL"},
      {"evidence_id":"lm:dental","landmark_id":"U1_apex","x":3.0,"y":4.0,"origin":"MANUAL"},
      {"evidence_id":"lm:occ","landmark_id":"Occ_Ant","x":5.0,"y":6.0,"origin":"MANUAL"}])
    reg={x["canonical_id"]:x for x in migrate_v1_to_v2(source,patient_id=7,width=1935,height=2400)["landmark_registry"]}
    assert reg["Pog_soft"]["tissue_domain"]=="SOFT"
    assert reg["U1_apex"]["tissue_domain"]=="DENTAL"
    assert reg["Occ_Ant"]["tissue_domain"]=="CONSTRUCTION_ANCHOR"

def test_multiple_calibrations_and_patient_mismatch_fail_closed():
    source=v1(); source["sources"].append({"evidence_id":"cal:2","kind":"calibration"})
    with pytest.raises(Lot05MigrationError): migrate_v1_to_v2(source,patient_id=7,width=1935,height=2400)
    source=v1(); source["sources"][0]["patient_id"]=8
    with pytest.raises(Lot05MigrationError): migrate_v1_to_v2(source,patient_id=7,width=1935,height=2400)

def test_invalid_dimensions_fail_closed():
    for width,height in [(0,2400),(1935,0),(-1,2400)]:
        with pytest.raises(Lot05MigrationError): migrate_v1_to_v2(v1(),patient_id=7,width=width,height=height)


def test_alias_cannot_shadow_canonical_identity():
    v2=migrate_v1_to_v2(v1(),patient_id=7,width=1935,height=2400)
    v2["landmark_registry"][0]["aliases"]=[v2["landmark_registry"][1]["canonical_id"]]
    with pytest.raises(Lot05MigrationError): roundtrip_v2_to_v1(v2)

def test_duplicate_alias_fails_closed():
    v2=migrate_v1_to_v2(v1(),patient_id=7,width=1935,height=2400)
    v2["landmark_registry"][0]["aliases"]=["legacy-x"]
    v2["landmark_registry"][1]["aliases"]=["legacy-x"]
    with pytest.raises(Lot05MigrationError): roundtrip_v2_to_v1(v2)


def test_migration_timestamp_is_auditable_and_timezone_aware():
    v2=migrate_v1_to_v2(v1(),patient_id=7,width=1935,height=2400,migrated_at="2026-10-01T17:00:00+00:00")
    assert v2["migration"]["migrated_at"]=="2026-10-01T17:00:00+00:00"
    with pytest.raises(Lot05MigrationError):
        migrate_v1_to_v2(v1(),patient_id=7,width=1935,height=2400,migrated_at="2026-10-01T17:00:00")


def test_migration_harness_import_and_core_path_execute():
    source=v1()
    v2=migrate_v1_to_v2(source,patient_id=7,width=1935,height=2400)
    assert v2["schema_version"]=="CEPHALO_CANONICAL_SCHEMA_V2"
    assert roundtrip_v2_to_v1(v2)==source


@pytest.mark.parametrize("x,y",[(float("nan"),1.0),(float("inf"),1.0),(1.0,float("-inf")),(True,1.0),("10",1.0)])
def test_nonfinite_or_non_numeric_landmark_coordinates_fail_closed(x,y):
    source=v1(); source["landmarks"][0]["x"]=x; source["landmarks"][0]["y"]=y
    with pytest.raises(Lot05MigrationError):
        migrate_v1_to_v2(source,patient_id=7,width=1935,height=2400)

def test_calibration_requires_stable_evidence_id():
    source=v1(); source["sources"][1].pop("evidence_id")
    with pytest.raises(Lot05MigrationError):
        migrate_v1_to_v2(source,patient_id=7,width=1935,height=2400)
