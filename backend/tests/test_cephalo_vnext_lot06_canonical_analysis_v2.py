from backend.schemas.cephalo_evidence import EvidenceStatus, LandmarkEvidence, LandmarkOrigin
from backend.services.cephalo_canonical_analysis_v2 import (
    CANONICAL_V2_METHOD_IDS,
    materialize_canonical_analysis_v2_measurements,
)


def _lm(landmark_id, x, y):
    return LandmarkEvidence(
        evidence_id=f"landmark:test:{landmark_id}",
        landmark_id=landmark_id,
        x=float(x), y=float(y),
        source_image_ref="source:ceph",
        origin=LandmarkOrigin.MANUAL,
        evidence_refs=["source:ceph"],
        evidence_status=EvidenceStatus.OBSERVED,
    )


def _landmarks():
    pts = {
        "S": (0, 0), "N": (10, 0), "A": (12, 4), "Go": (0, 20), "Me": (15, 20),
        "Or": (20, 10), "Po_anatomic": (0, 10), "Co_anatomic": (-5, 5),
        "Gn_anatomic": (15, 18), "Pog_hard": (16, 8), "L1_apex": (7, 18),
        "L1_incisal": (9, 8), "Prn": (18, 4), "Pog_soft": (17, 9),
        "Ls_soft": (19, 6), "Li_soft": (18.5, 7),
    }
    return {key: _lm(key, *value) for key, value in pts.items()}
def test_canonical_v2_methods_are_complete_and_unique():
    out = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:test",
        landmarks=_landmarks(), mm_per_pixel=None, calibration_ref=None,
    )
    assert {item.method_id for item in out} == CANONICAL_V2_METHOD_IDS
    assert len(out) == len(CANONICAL_V2_METHOD_IDS)


def test_canonical_v2_angles_compute_without_calibration_and_linear_fail_closed():
    out = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:test",
        landmarks=_landmarks(), mm_per_pixel=None, calibration_ref=None,
    )
    angular = [item for item in out if not item.requires_calibration]
    linear = [item for item in out if item.requires_calibration]
    assert angular
    assert linear
    assert all(item.availability_status.value == "AVAILABLE" and item.value is not None for item in angular)
    assert all(item.availability_status.value == "NOT_COMPUTABLE" and item.value is None for item in linear)


def test_canonical_v2_calibration_unlocks_linear_measurements():
    out = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:test",
        landmarks=_landmarks(), mm_per_pixel=0.2, calibration_ref="source:calibration",
    )
    linear = [item for item in out if item.requires_calibration]
    assert all(item.availability_status.value == "AVAILABLE" for item in linear)
    assert all(item.value is not None and item.calibration_ref == "source:calibration" for item in linear)
def test_downs_and_ricketts_facial_angle_conventions_are_distinct_methods():
    out = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:test",
        landmarks=_landmarks(), mm_per_pixel=0.2, calibration_ref="source:calibration",
    )
    by_method = {item.method_id: item for item in out}
    downs = by_method["DOWNS_FACIAL_ANGLE_CANONICAL_DEG_V2"]
    ricketts = by_method["RICKETTS_FACIAL_DEPTH_CANONICAL_DEG_V2"]
    assert downs.value is not None and ricketts.value is not None
    assert downs.measurement_id != ricketts.measurement_id
    assert downs.value != ricketts.value
