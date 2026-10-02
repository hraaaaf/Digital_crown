import copy
import pytest
from scripts.validate_cephalo_vnext_lot05_migration import Lot05MigrationError, migrate_v1_to_v2, roundtrip_v2_to_v1

def v1():
    common_source = {"patient_id":7,"source_record_id":"img:1","recorded_at":"2026-09-10T15:00:00+00:00","evidence_status":"OBSERVED","availability_status":"AVAILABLE","metadata":{}}
    auto_common = {"source_image_ref":"source:image","origin":"SRPOSE38_AUTO","model_id":"srpose38","model_sha256":"a"*64,"pipeline_version":"SRPOSE38_V1","evidence_refs":["source:image"],"evidence_status":"OBSERVED","availability_status":"AVAILABLE"}
    return {"schema_version":"CEPHALO_EVIDENCE_V1","case_id":"case:1","revision":3,
      "sources":[
        {"evidence_id":"source:image","kind":"lateral_ceph",**common_source},
        {"evidence_id":"cal:1","kind":"calibration","ratio":0.1,**common_source}],
      "landmarks":[
        {"evidence_id":"lm:auto:A","landmark_id":"A","x":10.0,"y":20.0,**auto_common},
        {"evidence_id":"lm:auto:B","landmark_id":"B","x":30.0,"y":40.0,**auto_common},
        {"evidence_id":"lm:r3:A","landmark_id":"A","x":11.0,"y":21.0,"source_image_ref":"source:image","origin":"MANUAL_CORRECTED","original_auto_x":10.0,"original_auto_y":20.0,"validated_by":"99","validated_at":"2026-09-10T15:35:00+00:00","evidence_refs":["source:image"],"evidence_status":"CLINICIAN_VALIDATED","availability_status":"AVAILABLE"}],
      "current_landmark_refs":["lm:r3:A"],
      "measurements":[{"measurement_id":"SNA","value":81.0}],
      "calibration_status":"clinician_confirmed","unknown_legacy":{"keep":True}}



def test_typed_v1_provenance_preconditions_fail_closed():
    source=v1(); source["landmarks"][0].pop("model_sha256")
    with pytest.raises(Lot05MigrationError):
        migrate_v1_to_v2(source,patient_id=7,width=1935,height=2400,migrated_at="2026-10-01T00:00:00+00:00")
    source=v1(); source["landmarks"][2].pop("original_auto_x")
    with pytest.raises(Lot05MigrationError):
        migrate_v1_to_v2(source,patient_id=7,width=1935,height=2400,migrated_at="2026-10-01T00:00:00+00:00")
