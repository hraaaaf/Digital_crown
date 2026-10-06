import pytest

from backend.schemas.cephalo_evidence import EvidenceStatus, LandmarkEvidence, LandmarkOrigin
from backend.services.cephalo_canonical_analysis_v2 import (
    CANONICAL_V2_METHOD_IDS,
    materialize_canonical_analysis_v2_measurements,
)
from backend.services.cephalo_canonical_constructions_v2 import (
    RICKETTS_GN_CONSTRUCTION_ID,
    RICKETTS_PTV_CONSTRUCTION_ID,
    RICKETTS_FUNCTIONAL_OCCLUSAL_PLANE_CONSTRUCTION_ID,
    RICKETTS_MANDIBULAR_PLANE_CONSTRUCTION_ID,
    materialize_canonical_constructions_v2,
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
        "S": (0, 0), "N": (10, 0), "A": (12, 4), "Go": (0, 20), "MP_ANGLE_INFERIOR_Ricketts": (0, 18), "Me": (15, 20),
        "Ba": (-8, -4), "Pt_Ricketts": (5, 6), "PR_Ricketts_PTV": (4, 7),
        "Or": (20, 10), "Po_anatomic": (0, 10), "Co_anatomic": (-5, 5),
        "Gn_anatomic": (15, 18), "Pog_hard": (16, 8), "L1_apex": (7, 18),
        "L1_incisal": (9, 8), "Prn": (18, 4), "Pog_soft": (17, 9),
        "Ls_soft": (19, 6), "Li_soft": (18.5, 7),
        "FOP_PREMOLAR_Ricketts": (8, 9), "FOP_MOLAR_Ricketts": (14, 10),
        "ANS": (5, 6), "Pm_Ricketts": (15, 16), "DC_Ricketts": (1, 4),
        "R1_Ricketts": (2, 15), "R2_Ricketts": (8, 15),
        "R3_Ricketts": (5, 12), "R4_Ricketts": (5, 20),
    }
    return {key: _lm(key, *value) for key, value in pts.items()}
def _materialize(*, mm_per_pixel=None, calibration_ref=None, landmarks=None):
    landmarks = landmarks or _landmarks()
    constructions = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:test"
    )
    return materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:test",
        landmarks=landmarks, mm_per_pixel=mm_per_pixel,
        calibration_ref=calibration_ref, constructions=constructions,
    )


def test_canonical_v2_methods_are_complete_and_unique():
    out = _materialize()
    assert {item.method_id for item in out} == CANONICAL_V2_METHOD_IDS
    assert len(out) == len(CANONICAL_V2_METHOD_IDS)


def test_canonical_v2_angles_compute_without_calibration_and_linear_fail_closed():
    out = _materialize()
    angular = [item for item in out if not item.requires_calibration]
    linear = [item for item in out if item.requires_calibration]
    assert angular
    assert linear
    assert all(item.availability_status.value == "AVAILABLE" and item.value is not None for item in angular)
    assert all(item.availability_status.value == "NOT_COMPUTABLE" and item.value is None for item in linear)


def test_canonical_v2_calibration_unlocks_linear_measurements():
    out = _materialize(mm_per_pixel=0.2, calibration_ref="source:calibration")
    linear = [item for item in out if item.requires_calibration]
    assert all(item.availability_status.value == "AVAILABLE" for item in linear)
    assert all(item.value is not None and item.calibration_ref == "source:calibration" for item in linear)
def test_downs_and_ricketts_facial_angle_conventions_are_distinct_methods():
    out = _materialize(mm_per_pixel=0.2, calibration_ref="source:calibration")
    by_method = {item.method_id: item for item in out}
    downs = by_method["DOWNS_FACIAL_ANGLE_CANONICAL_DEG_V2"]
    ricketts = by_method["RICKETTS_FACIAL_DEPTH_CANONICAL_DEG_V2"]
    assert downs.value is not None and ricketts.value is not None
    assert downs.measurement_id != ricketts.measurement_id
    assert downs.value != ricketts.value


def test_ricketts_facial_axis_requires_explicit_pt_ricketts_and_constructed_gn():
    landmarks = _landmarks()
    out = _materialize(landmarks=landmarks)
    by_method = {item.method_id: item for item in out}
    facial_axis = by_method["RICKETTS_FACIAL_AXIS_CANONICAL_DEG_V2"]
    assert facial_axis.availability_status.value == "AVAILABLE"
    assert facial_axis.value is not None
    assert len(facial_axis.construction_refs) == 1
    assert RICKETTS_GN_CONSTRUCTION_ID in facial_axis.construction_refs[0]

    without_pt = dict(landmarks)
    without_pt.pop("Pt_Ricketts")
    out = _materialize(landmarks=without_pt)
    by_method = {item.method_id: item for item in out}
    facial_axis = by_method["RICKETTS_FACIAL_AXIS_CANONICAL_DEG_V2"]
    assert facial_axis.availability_status.value == "NOT_COMPUTABLE"
    assert facial_axis.value is None


def test_ricketts_ptv_requires_explicit_pr_ricketts_ptv_and_anatomical_frankfort():
    landmarks = _landmarks()
    constructions = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:test"
    )
    ptv = constructions[RICKETTS_PTV_CONSTRUCTION_ID]
    assert ptv.availability_status.value == "AVAILABLE"
    assert ptv.geometry["construction_rule"] == "line_through_PR_Ricketts_PTV_perpendicular_to_Frankfort_Po_anatomic_Or"
    assert ptv.geometry["point_x"] == pytest.approx(landmarks["PR_Ricketts_PTV"].x)
    assert ptv.geometry["point_y"] == pytest.approx(landmarks["PR_Ricketts_PTV"].y)
    dx = ptv.geometry["direction_x"]
    dy = ptv.geometry["direction_y"]
    fhx = landmarks["Or"].x - landmarks["Po_anatomic"].x
    fhy = landmarks["Or"].y - landmarks["Po_anatomic"].y
    assert dx * fhx + dy * fhy == pytest.approx(0.0, abs=1e-12)


def test_ricketts_ptv_does_not_promote_facial_axis_pt_or_generic_pt_point():
    landmarks = _landmarks()
    landmarks["PT_point"] = _lm("PT_point", 5, 6)
    landmarks.pop("PR_Ricketts_PTV")
    ptv = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:test"
    )[RICKETTS_PTV_CONSTRUCTION_ID]
    assert ptv.availability_status.value == "NOT_COMPUTABLE"
    assert "PR_Ricketts_PTV" in ptv.missing_landmark_ids


def test_ricketts_ptv_fails_closed_on_degenerate_frankfort():
    landmarks = _landmarks()
    landmarks["Or"] = _lm("Or", landmarks["Po_anatomic"].x, landmarks["Po_anatomic"].y)
    ptv = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:test"
    )[RICKETTS_PTV_CONSTRUCTION_ID]
    assert ptv.availability_status.value == "INVALID"


def test_ricketts_ptv_does_not_promote_ptm_or_facial_axis_pt():
    landmarks = _landmarks()
    landmarks.pop("PR_Ricketts_PTV")
    landmarks["Ptm"] = _lm("Ptm", 4, 7)
    ptv = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:test"
    )[RICKETTS_PTV_CONSTRUCTION_ID]
    assert ptv.availability_status.value == "NOT_COMPUTABLE"
    assert "PR_Ricketts_PTV" in ptv.missing_landmark_ids


def test_ricketts_ptv_rejects_mixed_source_landmarks():
    landmarks = _landmarks()
    landmarks["PR_Ricketts_PTV"] = LandmarkEvidence(
        evidence_id="landmark:test:PR_Ricketts_PTV:mixed",
        landmark_id="PR_Ricketts_PTV",
        x=4.0,
        y=7.0,
        source_image_ref="source:other-ceph",
        origin=LandmarkOrigin.MANUAL,
        evidence_refs=["source:other-ceph"],
        evidence_status=EvidenceStatus.OBSERVED,
    )
    ptv = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:test"
    )[RICKETTS_PTV_CONSTRUCTION_ID]
    assert ptv.availability_status.value == "INVALID"


def test_ricketts_source_specific_planes_require_explicit_identities():
    landmarks = _landmarks()
    constructions = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:test"
    )
    fop = constructions[RICKETTS_FUNCTIONAL_OCCLUSAL_PLANE_CONSTRUCTION_ID]
    mp = constructions[RICKETTS_MANDIBULAR_PLANE_CONSTRUCTION_ID]
    assert fop.availability_status.value == "AVAILABLE"
    assert mp.availability_status.value == "AVAILABLE"
    assert fop.geometry["required_landmark_ids"] == [
        "FOP_PREMOLAR_Ricketts", "FOP_MOLAR_Ricketts"
    ]
    assert mp.geometry["required_landmark_ids"] == ["MP_ANGLE_INFERIOR_Ricketts", "Me"]

    generic_only = dict(landmarks)
    generic_only.pop("MP_ANGLE_INFERIOR_Ricketts")
    generic_only.pop("FOP_PREMOLAR_Ricketts")
    generic_only.pop("FOP_MOLAR_Ricketts")
    blocked = materialize_canonical_constructions_v2(
        generic_only, construction_namespace="construction:test"
    )
    assert blocked[RICKETTS_MANDIBULAR_PLANE_CONSTRUCTION_ID].availability_status.value == "NOT_COMPUTABLE"
    assert "MP_ANGLE_INFERIOR_Ricketts" in blocked[RICKETTS_MANDIBULAR_PLANE_CONSTRUCTION_ID].missing_landmark_ids
    assert blocked[RICKETTS_FUNCTIONAL_OCCLUSAL_PLANE_CONSTRUCTION_ID].availability_status.value == "NOT_COMPUTABLE"


def test_ricketts_mandibular_plane_materializes_only_with_explicit_ricketts_angle_point():
    landmarks = _landmarks()
    out = _materialize(landmarks=landmarks)
    by_method = {item.method_id: item for item in out}
    mp = by_method["RICKETTS_MANDIBULAR_PLANE_FH_CANONICAL_DEG_V2"]
    assert mp.availability_status.value == "AVAILABLE"
    assert mp.value is not None
    assert len(mp.construction_refs) == 1
    assert RICKETTS_MANDIBULAR_PLANE_CONSTRUCTION_ID in mp.construction_refs[0]

    without_explicit = dict(landmarks)
    without_explicit.pop("MP_ANGLE_INFERIOR_Ricketts")
    out = _materialize(landmarks=without_explicit)
    by_method = {item.method_id: item for item in out}
    mp = by_method["RICKETTS_MANDIBULAR_PLANE_FH_CANONICAL_DEG_V2"]
    assert mp.availability_status.value == "NOT_COMPUTABLE"
    assert mp.value is None
