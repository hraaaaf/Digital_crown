import math

import pytest

from backend.services.cephalo_ricketts_geometry import (
    ricketts_l1_apog_inclination_deg_v1,
    ricketts_l1_edge_apog_signed_distance_px_v1,
    ricketts_maxillary_depth_deg_v1,
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


def _lm(landmark_id, x, y):
    return LandmarkEvidence(
        evidence_id=f"landmark:gregoret:{landmark_id}",
        landmark_id=landmark_id,
        x=float(x),
        y=float(y),
        source_image_ref="source:ceph",
        origin=LandmarkOrigin.MANUAL,
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
