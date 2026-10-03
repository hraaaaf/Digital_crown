import datetime as dt
from backend.schemas.cephalo_evidence import EvidenceStatus, LandmarkEvidence, LandmarkOrigin, AvailabilityStatus
from backend.services.cephalo_steiner_protocol_evidence import materialize_steiner_protocol_evidence
from backend.services.cephalo_canonical_method_bridge import canonical_measurement_id_for_method

def _lm(i,x,y):
    return LandmarkEvidence(evidence_id=f"lm:{i}",landmark_id=i,x=x,y=y,source_image_ref="src:1",origin=LandmarkOrigin.MANUAL,evidence_refs=["src:1"],evidence_status=EvidenceStatus.OBSERVED)

def _landmarks():
    pts={
      "S":(-10,0),"N":(0,0),"A":(0,10),"B":(0,12),"Pog_hard":(6,12),
      "Go":(0,20),"Gn_anatomic":(10,20),"L1_apex":(2,20),"L1_incisal":(2,10),
      "U1_facial_surface":(3,8),"L1_facial_surface":(4,11),"D_Steiner_1959":(0,15),
      "Occ_Steiner_Ant":(0,5),"Occ_Steiner_Post":(10,10),
    }
    return {k:_lm(k,*v) for k,v in pts.items()}

def test_source_locked_steiner_protocol_materializes_with_explicit_identities():
    c,m=materialize_steiner_protocol_evidence(landmarks=_landmarks(),construction_namespace="c",measurement_namespace="m",mm_per_pixel=0.5,calibration_ref="cal:1")
    assert len(c)==8 and len(m)==8
    assert all(x.availability_status==AvailabilityStatus.AVAILABLE for x in m)
    for x in m:
        assert canonical_measurement_id_for_method(x.method_id)
        if x.requires_calibration:
            assert x.calibration_ref=="cal:1"

def test_detector_d_point_cannot_substitute_for_explicit_steiner_d():
    lm=_landmarks(); lm.pop("D_Steiner_1959"); lm["D_point"]=_lm("D_point",0,15)
    _,m=materialize_steiner_protocol_evidence(landmarks=lm,construction_namespace="c",measurement_namespace="m",mm_per_pixel=0.5,calibration_ref="cal:1")
    by={x.method_id:x for x in m}
    assert by["STEINER_SND_CANONICAL_DEG_V2"].availability_status==AvailabilityStatus.NOT_COMPUTABLE
    assert by["STEINER_L1_DLINE_CANONICAL_MM_V2"].availability_status==AvailabilityStatus.NOT_COMPUTABLE

def test_linear_measurements_fail_closed_without_calibration():
    _,m=materialize_steiner_protocol_evidence(landmarks=_landmarks(),construction_namespace="c",measurement_namespace="m",mm_per_pixel=None,calibration_ref=None)
    linear=[x for x in m if x.requires_calibration]
    assert linear and all(x.availability_status==AvailabilityStatus.NOT_COMPUTABLE and x.value is None for x in linear)
