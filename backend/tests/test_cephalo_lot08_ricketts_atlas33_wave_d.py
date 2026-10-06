import math

import pytest

from backend.schemas.cephalo_evidence import EvidenceStatus, LandmarkEvidence, LandmarkOrigin
from backend.services.cephalo_canonical_analysis_v2 import materialize_canonical_analysis_v2_measurements
from backend.services.cephalo_canonical_constructions_v2 import materialize_canonical_constructions_v2
from backend.services.cephalo_measure_registry import canonical_measurement
from backend.services.cephalo_canonical_method_bridge import canonical_measurement_id_for_method
from backend.services.cephalo_ricketts_geometry import (
    ricketts_l1_edge_apog_signed_distance_px_v1,
    ricketts_u1_edge_apog_signed_distance_px_v1,
)


def _lm(landmark_id, x, y, source_image_ref="source:wave-d"):
    return LandmarkEvidence(
        evidence_id=f"landmark:wave-d:{landmark_id}",
        landmark_id=landmark_id,
        x=float(x),
        y=float(y),
        source_image_ref=source_image_ref,
        origin=LandmarkOrigin.MANUAL,
        evidence_refs=[source_image_ref],
        evidence_status=EvidenceStatus.OBSERVED,
    )


def _materialize(landmarks, mm_per_pixel=1.0, calibration_ref="calibration:wave-d"):
    constructions = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:wave-d"
    )
    out = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:wave-d",
        landmarks=landmarks,
        mm_per_pixel=mm_per_pixel,
        calibration_ref=calibration_ref,
        constructions=constructions,
    )
    return {item.method_id: item for item in out}


def _rotate(point, degrees):
    angle = math.radians(degrees)
    c, s = math.cos(angle), math.sin(angle)
    return (point[0] * c - point[1] * s, point[0] * s + point[1] * c)


def _mirror_x(point):
    return (-point[0], point[1])


def test_wave_d_apog_perpendicular_sign_is_rotation_and_mirror_invariant():
    u1=(3.5, 4)
    l1=(2.0, 6)
    a=(0, 0)
    pog=(0, 10)
    po=(0, 0)
    or_=(10, 0)

    assert ricketts_u1_edge_apog_signed_distance_px_v1(u1,a,pog,po,or_) == pytest.approx(3.5)
    assert ricketts_l1_edge_apog_signed_distance_px_v1(l1,a,pog,po,or_) == pytest.approx(2.0)

    for transform in (lambda p:_rotate(p, 73), _mirror_x):
        assert ricketts_u1_edge_apog_signed_distance_px_v1(
            transform(u1),transform(a),transform(pog),transform(po),transform(or_)
        ) == pytest.approx(3.5)
        assert ricketts_l1_edge_apog_signed_distance_px_v1(
            transform(l1),transform(a),transform(pog),transform(po),transform(or_)
        ) == pytest.approx(2.0)


def test_wave_d_u1_apog_materializes_and_requires_calibration():
    landmarks={
        "U1_incisal":_lm("U1_incisal",3.5,4),
        "A":_lm("A",0,0),
        "Pog_hard":_lm("Pog_hard",0,10),
        "Po_anatomic":_lm("Po_anatomic",0,0),
        "Or":_lm("Or",10,0),
    }
    out=_materialize(landmarks,mm_per_pixel=0.5)
    item=out["RICKETTS_U1_APOG_PROTRUSION_CANONICAL_MM_V2"]
    assert item.availability_status.value=="AVAILABLE"
    assert item.value==pytest.approx(1.75)
    assert canonical_measurement_id_for_method(item.method_id)=="M_RICKETTS_U1_APOG_PROTRUSION_MM_V1"

    out=_materialize(landmarks,mm_per_pixel=None,calibration_ref=None)
    item=out["RICKETTS_U1_APOG_PROTRUSION_CANONICAL_MM_V2"]
    assert item.availability_status.value=="NOT_COMPUTABLE"
    assert item.value is None


def test_wave_d_u1_apog_rejects_cross_image_evidence():
    landmarks={
        "U1_incisal":_lm("U1_incisal",3.5,4,"source:other"),
        "A":_lm("A",0,0),
        "Pog_hard":_lm("Pog_hard",0,10),
        "Po_anatomic":_lm("Po_anatomic",0,0),
        "Or":_lm("Or",10,0),
    }
    out=_materialize(landmarks)
    item=out["RICKETTS_U1_APOG_PROTRUSION_CANONICAL_MM_V2"]
    assert item.availability_status.value=="INVALID"
    assert item.value is None


def test_wave_d_four_orientation_dependent_contracts_stay_fail_closed():
    expected={
        "M_RICKETTS_OVERBITE_FOP_MM_V1",
        "M_RICKETTS_OCCLUSAL_PLANE_XI_MM_V1",
        "M_RICKETTS_COMMISSURE_FOP_MM_V1",
        "M_RICKETTS_PALATAL_PLANE_FH_DEG_V1",
    }
    for measurement_id in expected:
        item=canonical_measurement(measurement_id)
        assert item is not None
        assert item.source_status=="CONDITIONAL_EXECUTABLE__IMAGE_ORIENTATION_EVIDENCE_REQUIRED"

    landmarks={
        "U1_incisal":_lm("U1_incisal",3.5,4),
        "L1_incisal":_lm("L1_incisal",2,6),
        "A":_lm("A",0,0),
        "Pog_hard":_lm("Pog_hard",0,10),
        "Po_anatomic":_lm("Po_anatomic",0,0),
        "Or":_lm("Or",10,0),
        "FOP_PREMOLAR_Ricketts":_lm("FOP_PREMOLAR_Ricketts",2,5),
        "FOP_MOLAR_Ricketts":_lm("FOP_MOLAR_Ricketts",8,5),
        "R1_Ricketts":_lm("R1_Ricketts",0,10),
        "R2_Ricketts":_lm("R2_Ricketts",10,10),
        "R3_Ricketts":_lm("R3_Ricketts",5,5),
        "R4_Ricketts":_lm("R4_Ricketts",5,15),
        "LABIAL_COMMISSURE_Ricketts":_lm("LABIAL_COMMISSURE_Ricketts",3,3),
        "ANS":_lm("ANS",2,1),
        "PNS_Ricketts":_lm("PNS_Ricketts",8,2),
    }
    out=_materialize(landmarks)
    for method in (
        "RICKETTS_OVERBITE_FOP_CANONICAL_MM_V2",
        "RICKETTS_OCCLUSAL_PLANE_XI_CANONICAL_MM_V2",
        "RICKETTS_COMMISSURE_FOP_CANONICAL_MM_V2",
        "RICKETTS_PALATAL_PLANE_FH_CANONICAL_DEG_V2",
    ):
        assert out[method].availability_status.value == "NOT_COMPUTABLE"
        assert out[method].value is None
        assert out[method].orientation_ref is None
