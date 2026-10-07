import math

import pytest

from backend.services.cephalo_ricketts_geometry import (
    ricketts_l1_apog_inclination_deg_v1,
    ricketts_l1_edge_apog_signed_distance_px_v1,
    ricketts_l1_occlusal_extrusion_signed_px_v1,
    ricketts_lower_facial_height_ans_xi_pm_deg_v1,
    ricketts_mandibular_arc_deg_v1,
    ricketts_maxillary_depth_deg_v1,
    ricketts_u6_distal_to_ptv_signed_px_v1,
    ricketts_xi_from_r1_r4_fh_v1,
    ricketts_mandibular_plane_fh_deg_v1,
)


def test_ricketts_maxillary_depth_is_fh_to_na_and_allows_values_above_90():
    assert ricketts_maxillary_depth_deg_v1((0, 0), (10, 0), (0, 0), (0, 10)) == 90.0
    value = ricketts_maxillary_depth_deg_v1((0, 0), (10, 0), (0, 0), (-1, 10))
    assert value is not None and value > 90.0


def test_ricketts_l1_apog_inclination_uses_incisal_to_apex_axis():
    theta = math.radians(22.0)
    l1_incisal = (0.0, 0.0)
    l1_apex = (-math.sin(theta), math.cos(theta))
    a = (0.0, 0.0)
    pog = (0.0, 10.0)
    value = ricketts_l1_apog_inclination_deg_v1(l1_incisal, l1_apex, a, pog)
    assert value is not None
    assert value == pytest.approx(22.0, abs=1e-9)


def test_ricketts_new_angles_fail_closed_on_degenerate_axes():
    assert ricketts_maxillary_depth_deg_v1((0, 0), (0, 0), (0, 0), (0, 10)) is None
    assert ricketts_l1_apog_inclination_deg_v1((0, 0), (0, 0), (0, 0), (0, 10)) is None


def test_ricketts_mandibular_plane_uses_explicit_angle_point_to_menton_against_fh():
    value = ricketts_mandibular_plane_fh_deg_v1(
        (0, 0), (10, 0), (0, 0), (10, 5)
    )
    assert value == pytest.approx(math.degrees(math.atan2(5, 10)), abs=1e-9)


def test_ricketts_mandibular_plane_fails_closed_on_degenerate_axis():
    assert ricketts_mandibular_plane_fh_deg_v1(
        (0, 0), (0, 0), (0, 0), (10, 5)
    ) is None
    assert ricketts_mandibular_plane_fh_deg_v1(
        (0, 0), (10, 0), (0, 0), (0, 0)
    ) is None


from backend.schemas.cephalo_evidence import EvidenceStatus, LandmarkEvidence, LandmarkOrigin
from backend.services.cephalo_canonical_analysis_v2 import materialize_canonical_analysis_v2_measurements
from backend.services.cephalo_canonical_constructions_v2 import materialize_canonical_constructions_v2


def _lm(landmark_id, x, y, source_image_ref="source:ceph"):
    return LandmarkEvidence(
        evidence_id=f"landmark:gregoret:{landmark_id}",
        landmark_id=landmark_id,
        x=float(x),
        y=float(y),
        source_image_ref=source_image_ref,
        origin=LandmarkOrigin.MANUAL,
        evidence_refs=["source:ceph"],
        evidence_status=EvidenceStatus.OBSERVED,
    )




def _auto_lm(landmark_id, x, y, source_image_ref="source:ceph"):
    return LandmarkEvidence(
        evidence_id=f"landmark:auto:{landmark_id}",
        landmark_id=landmark_id,
        x=float(x),
        y=float(y),
        source_image_ref=source_image_ref,
        origin=LandmarkOrigin.SRPOSE38_AUTO,
        model_id="test-model",
        model_sha256="a" * 64,
        pipeline_version="test-pipeline",
        evidence_refs=["source:ceph"],
        evidence_status=EvidenceStatus.OBSERVED,
    )


def test_gregoret_new_angles_materialize_through_canonical_v2_bridge():
    pts = {
        "S": (0, 0), "N": (0, 0), "A": (0, 10), "Go": (0, 20), "Me": (15, 20),
        "Ba": (-8, -4), "Pt_Ricketts": (5, 6), "Or": (10, 0), "Po_anatomic": (0, 0),
        "Co_anatomic": (-5, 5), "Gn_anatomic": (15, 18), "Pog_hard": (0, 20),
        "L1_incisal": (0, 0), "L1_apex": (-math.sin(math.radians(22)), math.cos(math.radians(22))),
        "Prn": (18, 4), "Pog_soft": (17, 9), "Ls_soft": (19, 6), "Li_soft": (18.5, 7),
    }
    landmarks = {key: _lm(key, *value) for key, value in pts.items()}
    constructions = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:gregoret"
    )
    out = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:gregoret",
        landmarks=landmarks,
        mm_per_pixel=None,
        calibration_ref=None,
        constructions=constructions,
    )
    by_method = {item.method_id: item for item in out}
    max_depth = by_method["RICKETTS_MAXILLARY_DEPTH_CANONICAL_DEG_V2"]
    l1_apog = by_method["RICKETTS_L1_APOG_INCLINATION_CANONICAL_DEG_V2"]
    assert max_depth.availability_status.value == "AVAILABLE"
    assert max_depth.value == pytest.approx(90.0)
    assert l1_apog.availability_status.value == "AVAILABLE"
    assert l1_apog.value == pytest.approx(22.0)


def test_ricketts_l1_edge_apog_signed_distance_is_positive_anterior():
    assert ricketts_l1_edge_apog_signed_distance_px_v1((2,5),(0,0),(0,10),(0,0),(10,0)) == pytest.approx(2.0)
    assert ricketts_l1_edge_apog_signed_distance_px_v1((-2,5),(0,0),(0,10),(0,0),(10,0)) == pytest.approx(-2.0)

def test_ricketts_l1_edge_apog_fail_closed_on_degenerate_apog_or_fh():
    assert ricketts_l1_edge_apog_signed_distance_px_v1((2,5),(0,0),(0,0),(0,0),(10,0)) is None
    assert ricketts_l1_edge_apog_signed_distance_px_v1((2,5),(0,0),(0,10),(0,0),(0,0)) is None


def test_gregoret_l1_edge_apog_materializes_with_calibration_and_correct_sign():
    pts = {
        "S": (0, 0), "N": (0, 0), "A": (0, 0), "Go": (0, 20), "Me": (15, 20),
        "Ba": (-8, -4), "Pt_Ricketts": (5, 6), "Or": (10, 0), "Po_anatomic": (0, 0),
        "Co_anatomic": (-5, 5), "Gn_anatomic": (15, 18), "Pog_hard": (0, 10),
        "L1_incisal": (2, 5), "L1_apex": (1, 6),
        "Prn": (18, 4), "Pog_soft": (17, 9), "Ls_soft": (19, 6), "Li_soft": (18.5, 7),
    }
    landmarks = {key: _lm(key, *value) for key, value in pts.items()}
    constructions = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:gregoret"
    )
    out = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:gregoret",
        landmarks=landmarks,
        mm_per_pixel=0.5,
        calibration_ref="source:calibration",
        constructions=constructions,
    )
    by_method = {item.method_id: item for item in out}
    item = by_method["RICKETTS_L1_EDGE_APOG_CANONICAL_MM_V2"]
    assert item.availability_status.value == "AVAILABLE"
    assert item.value == pytest.approx(1.0)
    assert item.calibration_ref == "source:calibration"
    assert item.requires_calibration is True


def test_ricketts_l1_occlusal_extrusion_sign_is_crownward_positive_and_apical_negative():
    plane_point = (0.0, 5.0)
    plane_direction = (10.0, 0.0)
    assert ricketts_l1_occlusal_extrusion_signed_px_v1(
        (5.0, 3.0), (5.0, 8.0), plane_point, plane_direction
    ) == pytest.approx(2.0)
    assert ricketts_l1_occlusal_extrusion_signed_px_v1(
        (5.0, 7.0), (5.0, 10.0), plane_point, plane_direction
    ) == pytest.approx(-2.0)


def test_ricketts_l1_occlusal_extrusion_is_rotation_and_mirror_invariant():
    original = ricketts_l1_occlusal_extrusion_signed_px_v1(
        (5.0, 3.0), (5.0, 8.0), (0.0, 5.0), (10.0, 0.0)
    )
    rotated = ricketts_l1_occlusal_extrusion_signed_px_v1(
        (-3.0, 5.0), (-8.0, 5.0), (-5.0, 0.0), (0.0, 10.0)
    )
    mirrored = ricketts_l1_occlusal_extrusion_signed_px_v1(
        (-5.0, 3.0), (-5.0, 8.0), (0.0, 5.0), (-10.0, 0.0)
    )
    assert original == pytest.approx(2.0)
    assert rotated == pytest.approx(2.0)
    assert mirrored == pytest.approx(2.0)


def test_ricketts_l1_occlusal_extrusion_fails_closed_when_sign_orientation_is_ambiguous():
    assert ricketts_l1_occlusal_extrusion_signed_px_v1(
        (5.0, 3.0), (0.0, 3.0), (0.0, 5.0), (10.0, 0.0)
    ) is None
    assert ricketts_l1_occlusal_extrusion_signed_px_v1(
        (5.0, 3.0), (5.0, 8.0), (0.0, 5.0), (0.0, 0.0)
    ) is None


def test_gregoret_l1_occlusal_extrusion_materializes_from_canonical_fop_with_calibration():
    pts = {
        "S": (0, 0), "N": (0, 0), "A": (0, 10), "Go": (0, 20), "Me": (15, 20),
        "Ba": (-8, -4), "Pt_Ricketts": (5, 6), "Or": (10, 0), "Po_anatomic": (0, 0),
        "Co_anatomic": (-5, 5), "Gn_anatomic": (15, 18), "Pog_hard": (0, 20),
        "L1_incisal": (5, 3), "L1_apex": (5, 8),
        "FOP_PREMOLAR_Ricketts": (0, 5), "FOP_MOLAR_Ricketts": (10, 5),
        "Prn": (18, 4), "Pog_soft": (17, 9), "Ls_soft": (19, 6), "Li_soft": (18.5, 7),
    }
    landmarks = {key: _lm(key, *value) for key, value in pts.items()}
    constructions = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:gregoret"
    )
    out = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:gregoret",
        landmarks=landmarks,
        mm_per_pixel=0.5,
        calibration_ref="source:calibration",
        constructions=constructions,
    )
    by_method = {item.method_id: item for item in out}
    item = by_method["RICKETTS_L1_OCCLUSAL_EXTRUSION_CANONICAL_MM_V2"]
    assert item.availability_status.value == "AVAILABLE"
    assert item.value == pytest.approx(1.0)
    assert item.requires_calibration is True
    assert item.calibration_ref == "source:calibration"
    assert item.construction_refs == [
        "construction:gregoret:RICKETTS_FUNCTIONAL_OCCLUSAL_PLANE_BICUSPID_MOLAR_V1"
    ]


def test_gregoret_l1_occlusal_extrusion_fails_closed_without_explicit_fop_anchors():
    pts = {
        "L1_incisal": (5, 3), "L1_apex": (5, 8),
    }
    landmarks = {key: _lm(key, *value) for key, value in pts.items()}
    constructions = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:gregoret"
    )
    out = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:gregoret",
        landmarks=landmarks,
        mm_per_pixel=0.5,
        calibration_ref="source:calibration",
        constructions=constructions,
    )
    by_method = {item.method_id: item for item in out}
    item = by_method["RICKETTS_L1_OCCLUSAL_EXTRUSION_CANONICAL_MM_V2"]
    assert item.availability_status.value == "NOT_COMPUTABLE"
    assert item.value is None


def test_gregoret_l1_occlusal_extrusion_requires_verified_calibration():
    pts = {
        "L1_incisal": (5, 3), "L1_apex": (5, 8),
        "FOP_PREMOLAR_Ricketts": (0, 5), "FOP_MOLAR_Ricketts": (10, 5),
    }
    landmarks = {key: _lm(key, *value) for key, value in pts.items()}
    constructions = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:gregoret"
    )
    out = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:gregoret",
        landmarks=landmarks,
        mm_per_pixel=None,
        calibration_ref=None,
        constructions=constructions,
    )
    item = {entry.method_id: entry for entry in out}[
        "RICKETTS_L1_OCCLUSAL_EXTRUSION_CANONICAL_MM_V2"
    ]
    assert item.availability_status.value == "NOT_COMPUTABLE"
    assert item.value is None
    assert item.calibration_ref is None


def test_gregoret_l1_occlusal_extrusion_rejects_cross_image_fop_and_incisor_evidence():
    landmarks = {
        "L1_incisal": _lm("L1_incisal", 5, 3, "source:l1"),
        "L1_apex": _lm("L1_apex", 5, 8, "source:l1"),
        "FOP_PREMOLAR_Ricketts": _lm("FOP_PREMOLAR_Ricketts", 0, 5, "source:fop"),
        "FOP_MOLAR_Ricketts": _lm("FOP_MOLAR_Ricketts", 10, 5, "source:fop"),
    }
    constructions = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:gregoret"
    )
    out = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:gregoret",
        landmarks=landmarks,
        mm_per_pixel=0.5,
        calibration_ref="source:calibration",
        constructions=constructions,
    )
    item = {entry.method_id: entry for entry in out}[
        "RICKETTS_L1_OCCLUSAL_EXTRUSION_CANONICAL_MM_V2"
    ]
    assert item.availability_status.value == "INVALID"
    assert item.value is None


def test_gregoret_l1_occlusal_extrusion_propagates_invalid_degenerate_fop():
    landmarks = {
        "L1_incisal": _lm("L1_incisal", 5, 3),
        "L1_apex": _lm("L1_apex", 5, 8),
        "FOP_PREMOLAR_Ricketts": _lm("FOP_PREMOLAR_Ricketts", 5, 5),
        "FOP_MOLAR_Ricketts": _lm("FOP_MOLAR_Ricketts", 5, 5),
    }
    constructions = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:gregoret"
    )
    out = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:gregoret",
        landmarks=landmarks,
        mm_per_pixel=0.5,
        calibration_ref="source:calibration",
        constructions=constructions,
    )
    item = {entry.method_id: entry for entry in out}[
        "RICKETTS_L1_OCCLUSAL_EXTRUSION_CANONICAL_MM_V2"
    ]
    assert item.availability_status.value == "INVALID"
    assert item.value is None


def test_ricketts_xi_constructs_center_of_ramal_rectangle_in_fh_basis():
    xi = ricketts_xi_from_r1_r4_fh_v1(
        (2.0, 5.0),
        (8.0, 5.0),
        (5.0, 2.0),
        (5.0, 10.0),
        (0.0, 0.0),
        (10.0, 0.0),
    )
    assert xi == pytest.approx((5.0, 6.0))


def test_ricketts_xi_is_rotation_and_mirror_invariant():
    original = ricketts_xi_from_r1_r4_fh_v1(
        (2.0, 5.0), (8.0, 5.0), (5.0, 2.0), (5.0, 10.0),
        (0.0, 0.0), (10.0, 0.0),
    )
    rotated = ricketts_xi_from_r1_r4_fh_v1(
        (-5.0, 2.0), (-5.0, 8.0), (-2.0, 5.0), (-10.0, 5.0),
        (0.0, 0.0), (0.0, 10.0),
    )
    mirrored = ricketts_xi_from_r1_r4_fh_v1(
        (-2.0, 5.0), (-8.0, 5.0), (-5.0, 2.0), (-5.0, 10.0),
        (0.0, 0.0), (-10.0, 0.0),
    )
    assert original == pytest.approx((5.0, 6.0))
    assert rotated == pytest.approx((-6.0, 5.0))
    assert mirrored == pytest.approx((-5.0, 6.0))


def test_ricketts_xi_fails_closed_on_degenerate_fh_or_rectangle():
    assert ricketts_xi_from_r1_r4_fh_v1(
        (2,5),(8,5),(5,2),(5,10),(0,0),(0,0)
    ) is None
    assert ricketts_xi_from_r1_r4_fh_v1(
        (5,5),(5,5),(5,2),(5,10),(0,0),(10,0)
    ) is None


def test_ricketts_lower_facial_height_is_ans_xi_pm_angle():
    value = ricketts_lower_facial_height_ans_xi_pm_deg_v1(
        (5.0, -4.0),
        (5.0, 6.0),
        (15.0, 6.0),
    )
    assert value == pytest.approx(90.0)


def test_gregoret_lower_facial_height_materializes_from_constructed_xi_and_explicit_pm():
    pts = {
        "ANS": (5, -4), "Pm_Ricketts": (15, 6),
        "R1_Ricketts": (2, 5), "R2_Ricketts": (8, 5),
        "R3_Ricketts": (5, 2), "R4_Ricketts": (5, 10),
        "Po_anatomic": (0, 0), "Or": (10, 0),
    }
    landmarks = {key: _lm(key, *value) for key, value in pts.items()}
    constructions = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:gregoret"
    )
    out = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:gregoret",
        landmarks=landmarks,
        mm_per_pixel=None,
        calibration_ref=None,
        constructions=constructions,
    )
    item = {entry.method_id: entry for entry in out}[
        "RICKETTS_LOWER_FACIAL_HEIGHT_CANONICAL_DEG_V2"
    ]
    assert item.availability_status.value == "AVAILABLE"
    assert item.value == pytest.approx(90.0)
    assert item.construction_refs == [
        "construction:gregoret:RICKETTS_XI_RAMAL_RECTANGLE_R1_R4_FH_V1"
    ]


def test_gregoret_lower_facial_height_fails_closed_without_explicit_pm_ricketts():
    pts = {
        "ANS": (5, -4),
        "R1_Ricketts": (2, 5), "R2_Ricketts": (8, 5),
        "R3_Ricketts": (5, 2), "R4_Ricketts": (5, 10),
        "Po_anatomic": (0, 0), "Or": (10, 0),
    }
    landmarks = {key: _lm(key, *value) for key, value in pts.items()}
    constructions = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:gregoret"
    )
    out = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:gregoret",
        landmarks=landmarks,
        mm_per_pixel=None,
        calibration_ref=None,
        constructions=constructions,
    )
    item = {entry.method_id: entry for entry in out}[
        "RICKETTS_LOWER_FACIAL_HEIGHT_CANONICAL_DEG_V2"
    ]
    assert item.availability_status.value == "NOT_COMPUTABLE"
    assert item.value is None


def test_gregoret_lower_facial_height_rejects_cross_image_xi_and_pm():
    landmarks = {
        "ANS": _lm("ANS", 5, -4, "source:face"),
        "Pm_Ricketts": _lm("Pm_Ricketts", 15, 6, "source:face"),
        "R1_Ricketts": _lm("R1_Ricketts", 2, 5, "source:ramus"),
        "R2_Ricketts": _lm("R2_Ricketts", 8, 5, "source:ramus"),
        "R3_Ricketts": _lm("R3_Ricketts", 5, 2, "source:ramus"),
        "R4_Ricketts": _lm("R4_Ricketts", 5, 10, "source:ramus"),
        "Po_anatomic": _lm("Po_anatomic", 0, 0, "source:ramus"),
        "Or": _lm("Or", 10, 0, "source:ramus"),
    }
    constructions = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:gregoret"
    )
    out = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:gregoret",
        landmarks=landmarks,
        mm_per_pixel=None,
        calibration_ref=None,
        constructions=constructions,
    )
    item = {entry.method_id: entry for entry in out}[
        "RICKETTS_LOWER_FACIAL_HEIGHT_CANONICAL_DEG_V2"
    ]
    assert item.availability_status.value == "INVALID"
    assert item.value is None


def test_gregoret_lower_facial_height_does_not_promote_generic_xi_or_pm_aliases():
    landmarks = {
        "ANS": _lm("ANS", 5, -4),
        "Xi": _lm("Xi", 5, 6),
        "Pm": _lm("Pm", 15, 6),
        "Po_anatomic": _lm("Po_anatomic", 0, 0),
        "Or": _lm("Or", 10, 0),
    }
    constructions = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:gregoret"
    )
    out = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:gregoret",
        landmarks=landmarks,
        mm_per_pixel=None,
        calibration_ref=None,
        constructions=constructions,
    )
    item = {entry.method_id: entry for entry in out}[
        "RICKETTS_LOWER_FACIAL_HEIGHT_CANONICAL_DEG_V2"
    ]
    assert item.availability_status.value == "NOT_COMPUTABLE"
    assert item.value is None


def test_ricketts_xi_rejects_auto_r1_r4_authority():
    landmarks = {
        "R1_Ricketts": _auto_lm("R1_Ricketts", 2, 5),
        "R2_Ricketts": _lm("R2_Ricketts", 8, 5),
        "R3_Ricketts": _lm("R3_Ricketts", 5, 2),
        "R4_Ricketts": _lm("R4_Ricketts", 5, 10),
        "Po_anatomic": _lm("Po_anatomic", 0, 0),
        "Or": _lm("Or", 10, 0),
    }
    constructions = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:gregoret"
    )
    xi = constructions["RICKETTS_XI_RAMAL_RECTANGLE_R1_R4_FH_V1"]
    assert xi.availability_status.value == "NOT_COMPUTABLE"
    assert "R1_Ricketts" in xi.missing_landmark_ids


def test_gregoret_lower_facial_height_rejects_auto_pm_authority():
    landmarks = {
        "ANS": _lm("ANS", 5, -4),
        "Pm_Ricketts": _auto_lm("Pm_Ricketts", 15, 6),
        "R1_Ricketts": _lm("R1_Ricketts", 2, 5),
        "R2_Ricketts": _lm("R2_Ricketts", 8, 5),
        "R3_Ricketts": _lm("R3_Ricketts", 5, 2),
        "R4_Ricketts": _lm("R4_Ricketts", 5, 10),
        "Po_anatomic": _lm("Po_anatomic", 0, 0),
        "Or": _lm("Or", 10, 0),
    }
    constructions = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:gregoret"
    )
    out = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:gregoret",
        landmarks=landmarks,
        mm_per_pixel=None,
        calibration_ref=None,
        constructions=constructions,
    )
    item = {entry.method_id: entry for entry in out}[
        "RICKETTS_LOWER_FACIAL_HEIGHT_CANONICAL_DEG_V2"
    ]
    assert item.availability_status.value == "NOT_COMPUTABLE"
    assert item.value is None


def test_ricketts_mandibular_arc_uses_condylar_axis_vs_posterior_corpus_extension():
    value = ricketts_mandibular_arc_deg_v1(
        (0.0, 1.0),
        (5.0, 6.0),
        (15.0, 6.0),
    )
    assert value == pytest.approx(45.0)


def test_ricketts_mandibular_arc_fails_closed_on_degenerate_axis():
    assert ricketts_mandibular_arc_deg_v1(
        (5.0, 6.0), (5.0, 6.0), (15.0, 6.0)
    ) is None
    assert ricketts_mandibular_arc_deg_v1(
        (0.0, 1.0), (5.0, 6.0), (5.0, 6.0)
    ) is None


def test_gregoret_mandibular_arc_materializes_from_manual_dc_constructed_xi_manual_pm():
    pts = {
        "DC_Ricketts": (0, 1), "Pm_Ricketts": (15, 6),
        "R1_Ricketts": (2, 5), "R2_Ricketts": (8, 5),
        "R3_Ricketts": (5, 2), "R4_Ricketts": (5, 10),
        "Po_anatomic": (0, 0), "Or": (10, 0),
    }
    landmarks = {key: _lm(key, *value) for key, value in pts.items()}
    constructions = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:gregoret"
    )
    out = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:gregoret",
        landmarks=landmarks,
        mm_per_pixel=None,
        calibration_ref=None,
        constructions=constructions,
    )
    item = {entry.method_id: entry for entry in out}[
        "RICKETTS_MANDIBULAR_ARC_CANONICAL_DEG_V2"
    ]
    assert item.availability_status.value == "AVAILABLE"
    assert item.value == pytest.approx(45.0)
    assert item.construction_refs == [
        "construction:gregoret:RICKETTS_XI_RAMAL_RECTANGLE_R1_R4_FH_V1"
    ]


def test_gregoret_mandibular_arc_rejects_auto_dc_authority():
    landmarks = {
        "DC_Ricketts": _auto_lm("DC_Ricketts", 0, 1),
        "Pm_Ricketts": _lm("Pm_Ricketts", 15, 6),
        "R1_Ricketts": _lm("R1_Ricketts", 2, 5),
        "R2_Ricketts": _lm("R2_Ricketts", 8, 5),
        "R3_Ricketts": _lm("R3_Ricketts", 5, 2),
        "R4_Ricketts": _lm("R4_Ricketts", 5, 10),
        "Po_anatomic": _lm("Po_anatomic", 0, 0),
        "Or": _lm("Or", 10, 0),
    }
    constructions = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:gregoret"
    )
    out = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:gregoret",
        landmarks=landmarks,
        mm_per_pixel=None,
        calibration_ref=None,
        constructions=constructions,
    )
    item = {entry.method_id: entry for entry in out}[
        "RICKETTS_MANDIBULAR_ARC_CANONICAL_DEG_V2"
    ]
    assert item.availability_status.value == "NOT_COMPUTABLE"
    assert item.value is None


def test_gregoret_mandibular_arc_does_not_promote_generic_dc_xi_pm_aliases():
    landmarks = {
        "DC": _lm("DC", 0, 1),
        "Xi": _lm("Xi", 5, 6),
        "Pm": _lm("Pm", 15, 6),
    }
    constructions = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:gregoret"
    )
    out = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:gregoret",
        landmarks=landmarks,
        mm_per_pixel=None,
        calibration_ref=None,
        constructions=constructions,
    )
    assert "RICKETTS_MANDIBULAR_ARC_CANONICAL_DEG_V2" not in {
        entry.method_id for entry in out
    }


def test_gregoret_mandibular_arc_rejects_cross_image_dc_xi_pm_evidence():
    landmarks = {
        "DC_Ricketts": _lm("DC_Ricketts", 0, 1, "source:face"),
        "Pm_Ricketts": _lm("Pm_Ricketts", 15, 6, "source:face"),
        "R1_Ricketts": _lm("R1_Ricketts", 2, 5, "source:ramus"),
        "R2_Ricketts": _lm("R2_Ricketts", 8, 5, "source:ramus"),
        "R3_Ricketts": _lm("R3_Ricketts", 5, 2, "source:ramus"),
        "R4_Ricketts": _lm("R4_Ricketts", 5, 10, "source:ramus"),
        "Po_anatomic": _lm("Po_anatomic", 0, 0, "source:ramus"),
        "Or": _lm("Or", 10, 0, "source:ramus"),
    }
    constructions = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:gregoret"
    )
    out = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:gregoret",
        landmarks=landmarks,
        mm_per_pixel=None,
        calibration_ref=None,
        constructions=constructions,
    )
    item = {entry.method_id: entry for entry in out}[
        "RICKETTS_MANDIBULAR_ARC_CANONICAL_DEG_V2"
    ]
    assert item.availability_status.value == "INVALID"
    assert item.value is None


def test_gregoret_mandibular_arc_rejects_auto_pm_authority():
    landmarks = {
        "DC_Ricketts": _lm("DC_Ricketts", 0, 1),
        "Pm_Ricketts": _auto_lm("Pm_Ricketts", 15, 6),
        "R1_Ricketts": _lm("R1_Ricketts", 2, 5),
        "R2_Ricketts": _lm("R2_Ricketts", 8, 5),
        "R3_Ricketts": _lm("R3_Ricketts", 5, 2),
        "R4_Ricketts": _lm("R4_Ricketts", 5, 10),
        "Po_anatomic": _lm("Po_anatomic", 0, 0),
        "Or": _lm("Or", 10, 0),
    }
    constructions = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:gregoret"
    )
    out = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:gregoret",
        landmarks=landmarks,
        mm_per_pixel=None,
        calibration_ref=None,
        constructions=constructions,
    )
    item = {entry.method_id: entry for entry in out}[
        "RICKETTS_MANDIBULAR_ARC_CANONICAL_DEG_V2"
    ]
    assert item.availability_status.value == "NOT_COMPUTABLE"
    assert item.value is None


def test_ricketts_u6_ptv_distance_is_anterior_positive_and_rotation_mirror_invariant():
    original = ricketts_u6_distal_to_ptv_signed_px_v1(
        (8.0, 5.0), (2.0, 5.0), (1.0, 0.0)
    )
    rotated = ricketts_u6_distal_to_ptv_signed_px_v1(
        (-5.0, 8.0), (-5.0, 2.0), (0.0, 1.0)
    )
    mirrored = ricketts_u6_distal_to_ptv_signed_px_v1(
        (-8.0, 5.0), (-2.0, 5.0), (-1.0, 0.0)
    )
    assert original == pytest.approx(6.0)
    assert rotated == pytest.approx(6.0)
    assert mirrored == pytest.approx(6.0)


def test_ricketts_u6_ptv_distance_fails_closed_on_degenerate_frankfort():
    assert ricketts_u6_distal_to_ptv_signed_px_v1(
        (8.0, 5.0), (2.0, 5.0), (0.0, 0.0)
    ) is None


def test_gregoret_u6_ptv_materializes_from_manual_u6_and_manual_pr_with_calibration():
    landmarks = {
        "U6_DISTAL_Ricketts": _lm("U6_DISTAL_Ricketts", 8, 5),
        "PR_Ricketts_PTV": _lm("PR_Ricketts_PTV", 2, 5),
        "Po_anatomic": _lm("Po_anatomic", 0, 0),
        "Or": _lm("Or", 10, 0),
    }
    constructions = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:gregoret"
    )
    out = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:gregoret",
        landmarks=landmarks,
        mm_per_pixel=0.5,
        calibration_ref="source:calibration",
        constructions=constructions,
    )
    item = {entry.method_id: entry for entry in out}["RICKETTS_U6_PTV_CANONICAL_MM_V2"]
    assert item.availability_status.value == "AVAILABLE"
    assert item.value == pytest.approx(3.0)
    assert item.calibration_ref == "source:calibration"
    assert item.construction_refs == [
        "construction:gregoret:RICKETTS_PTV_PR_POSTERIOR_PPF_PERP_FH_V1"
    ]


def test_gregoret_u6_ptv_rejects_auto_u6_distal_authority():
    landmarks = {
        "U6_DISTAL_Ricketts": _auto_lm("U6_DISTAL_Ricketts", 8, 5),
        "PR_Ricketts_PTV": _lm("PR_Ricketts_PTV", 2, 5),
        "Po_anatomic": _lm("Po_anatomic", 0, 0),
        "Or": _lm("Or", 10, 0),
    }
    constructions = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:gregoret"
    )
    out = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:gregoret",
        landmarks=landmarks,
        mm_per_pixel=0.5,
        calibration_ref="source:calibration",
        constructions=constructions,
    )
    item = {entry.method_id: entry for entry in out}["RICKETTS_U6_PTV_CANONICAL_MM_V2"]
    assert item.availability_status.value == "NOT_COMPUTABLE"
    assert item.value is None


def test_ricketts_ptv_rejects_auto_pr_authority():
    landmarks = {
        "PR_Ricketts_PTV": _auto_lm("PR_Ricketts_PTV", 2, 5),
        "Po_anatomic": _lm("Po_anatomic", 0, 0),
        "Or": _lm("Or", 10, 0),
    }
    constructions = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:gregoret"
    )
    ptv = constructions["RICKETTS_PTV_PR_POSTERIOR_PPF_PERP_FH_V1"]
    assert ptv.availability_status.value == "NOT_COMPUTABLE"
    assert "PR_Ricketts_PTV" in ptv.missing_landmark_ids


def test_gregoret_u6_ptv_requires_verified_calibration():
    landmarks = {
        "U6_DISTAL_Ricketts": _lm("U6_DISTAL_Ricketts", 8, 5),
        "PR_Ricketts_PTV": _lm("PR_Ricketts_PTV", 2, 5),
        "Po_anatomic": _lm("Po_anatomic", 0, 0),
        "Or": _lm("Or", 10, 0),
    }
    constructions = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:gregoret"
    )
    out = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:gregoret",
        landmarks=landmarks,
        mm_per_pixel=None,
        calibration_ref=None,
        constructions=constructions,
    )
    item = {entry.method_id: entry for entry in out}["RICKETTS_U6_PTV_CANONICAL_MM_V2"]
    assert item.availability_status.value == "NOT_COMPUTABLE"
    assert item.value is None


def test_gregoret_u6_ptv_rejects_cross_image_evidence():
    landmarks = {
        "U6_DISTAL_Ricketts": _lm("U6_DISTAL_Ricketts", 8, 5, "source:u6"),
        "PR_Ricketts_PTV": _lm("PR_Ricketts_PTV", 2, 5, "source:ptv"),
        "Po_anatomic": _lm("Po_anatomic", 0, 0, "source:ptv"),
        "Or": _lm("Or", 10, 0, "source:ptv"),
    }
    constructions = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:gregoret"
    )
    out = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:gregoret",
        landmarks=landmarks,
        mm_per_pixel=0.5,
        calibration_ref="source:calibration",
        constructions=constructions,
    )
    item = {entry.method_id: entry for entry in out}["RICKETTS_U6_PTV_CANONICAL_MM_V2"]
    assert item.availability_status.value == "INVALID"
    assert item.value is None


def test_gregoret_u6_ptv_does_not_promote_generic_u6_or_ptv_aliases():
    landmarks = {
        "U6": _lm("U6", 8, 5),
        "PTV": _lm("PTV", 2, 5),
        "Po_anatomic": _lm("Po_anatomic", 0, 0),
        "Or": _lm("Or", 10, 0),
    }
    constructions = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:gregoret"
    )
    out = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:gregoret",
        landmarks=landmarks,
        mm_per_pixel=0.5,
        calibration_ref="source:calibration",
        constructions=constructions,
    )
    assert "RICKETTS_U6_PTV_CANONICAL_MM_V2" not in {entry.method_id for entry in out}
