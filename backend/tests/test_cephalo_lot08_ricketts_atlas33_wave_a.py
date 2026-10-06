import math

import pytest

from backend.schemas.cephalo_evidence import EvidenceStatus, LandmarkEvidence, LandmarkOrigin
from backend.services.cephalo_canonical_analysis_v2 import materialize_canonical_analysis_v2_measurements
from backend.services.cephalo_canonical_constructions_v2 import materialize_canonical_constructions_v2
from backend.services.cephalo_measure_registry import canonical_measurement
from backend.services.cephalo_ricketts_geometry import (
    ricketts_signed_projection_on_plane_px_v1,
    ricketts_u1_apog_inclination_deg_v1,
)


def _lm(landmark_id, x, y, source_image_ref="source:atlas33"):
    return LandmarkEvidence(
        evidence_id=f"landmark:atlas33:{landmark_id}",
        landmark_id=landmark_id,
        x=float(x),
        y=float(y),
        source_image_ref=source_image_ref,
        origin=LandmarkOrigin.MANUAL,
        evidence_refs=[source_image_ref],
        evidence_status=EvidenceStatus.OBSERVED,
    )


def _auto(landmark_id, x, y, source_image_ref="source:atlas33"):
    return LandmarkEvidence(
        evidence_id=f"landmark:atlas33:auto:{landmark_id}",
        landmark_id=landmark_id,
        x=float(x),
        y=float(y),
        source_image_ref=source_image_ref,
        origin=LandmarkOrigin.SRPOSE38_AUTO,
        model_id="test-model",
        model_sha256="a" * 64,
        pipeline_version="test-pipeline",
        evidence_refs=[source_image_ref],
        evidence_status=EvidenceStatus.OBSERVED,
    )


def _materialize(landmarks, mm_per_pixel=1.0, calibration_ref="calibration:atlas33"):
    constructions = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:atlas33"
    )
    out = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:atlas33",
        landmarks=landmarks,
        mm_per_pixel=mm_per_pixel,
        calibration_ref=calibration_ref,
        constructions=constructions,
    )
    return {item.method_id: item for item in out}


def _base_dental_landmarks():
    # FOP premolar->molar is posterior-positive (-x) in this synthetic image.
    return {
        "FOP_PREMOLAR_Ricketts": _lm("FOP_PREMOLAR_Ricketts", 5, 0),
        "FOP_MOLAR_Ricketts": _lm("FOP_MOLAR_Ricketts", -5, 0),
        "U6_DISTAL_Ricketts": _lm("U6_DISTAL_Ricketts", 0, 0),
        "L6_DISTAL_Ricketts": _lm("L6_DISTAL_Ricketts", 3, 0),
        "U3_CUSP_Ricketts": _lm("U3_CUSP_Ricketts", 0, 0),
        "L3_CUSP_Ricketts": _lm("L3_CUSP_Ricketts", 2, 0),
        "U1_incisal": _lm("U1_incisal", 2.5, 0),
        "L1_incisal": _lm("L1_incisal", 0, 0),
    }


def test_wave_a_projection_geometry_uses_plane_axis_not_screen_axis():
    posterior = (-1.0, 0.0)
    assert ricketts_signed_projection_on_plane_px_v1((3, 0), (0, 0), posterior) == pytest.approx(-3)
    assert ricketts_signed_projection_on_plane_px_v1((0, 0), (2.5, 0), posterior) == pytest.approx(2.5)
    assert ricketts_signed_projection_on_plane_px_v1((0, 3), (0, 0), (0, -1)) == pytest.approx(-3)


def test_atlas33_molar_canine_and_overjet_materialize_with_ricketts_signs():
    out = _materialize(_base_dental_landmarks())
    molar = out["RICKETTS_MOLAR_RELATION_FOP_CANONICAL_MM_V2"]
    canine = out["RICKETTS_CANINE_RELATION_FOP_CANONICAL_MM_V2"]
    overjet = out["RICKETTS_OVERJET_FOP_CANONICAL_MM_V2"]
    assert molar.availability_status.value == "AVAILABLE"
    assert molar.value == pytest.approx(-3.0)
    assert canine.availability_status.value == "AVAILABLE"
    assert canine.value == pytest.approx(-2.0)
    assert overjet.availability_status.value == "AVAILABLE"
    assert overjet.value == pytest.approx(2.5)


def test_atlas33_molar_and_canine_reject_auto_authority():
    landmarks = _base_dental_landmarks()
    landmarks["L6_DISTAL_Ricketts"] = _auto("L6_DISTAL_Ricketts", 3, 0)
    landmarks["U3_CUSP_Ricketts"] = _auto("U3_CUSP_Ricketts", 0, 0)
    out = _materialize(landmarks)
    assert out["RICKETTS_MOLAR_RELATION_FOP_CANONICAL_MM_V2"].availability_status.value == "NOT_COMPUTABLE"
    assert out["RICKETTS_CANINE_RELATION_FOP_CANONICAL_MM_V2"].availability_status.value == "NOT_COMPUTABLE"


def test_atlas33_dental_projection_requires_calibration_and_same_image():
    landmarks = _base_dental_landmarks()
    out = _materialize(landmarks, mm_per_pixel=None, calibration_ref=None)
    assert out["RICKETTS_OVERJET_FOP_CANONICAL_MM_V2"].availability_status.value == "NOT_COMPUTABLE"

    landmarks = _base_dental_landmarks()
    landmarks["U1_incisal"] = _lm("U1_incisal", 2.5, 0, "source:other")
    out = _materialize(landmarks)
    assert out["RICKETTS_OVERJET_FOP_CANONICAL_MM_V2"].availability_status.value == "INVALID"


def test_atlas33_generic_molar_canine_aliases_are_not_promoted():
    landmarks = {
        "FOP_PREMOLAR_Ricketts": _lm("FOP_PREMOLAR_Ricketts", 5, 0),
        "FOP_MOLAR_Ricketts": _lm("FOP_MOLAR_Ricketts", -5, 0),
        "U6": _lm("U6", 0, 0),
        "L6": _lm("L6", 3, 0),
        "U3": _lm("U3", 0, 0),
        "L3": _lm("L3", 2, 0),
    }
    out = _materialize(landmarks)
    assert "RICKETTS_MOLAR_RELATION_FOP_CANONICAL_MM_V2" not in out
    assert "RICKETTS_CANINE_RELATION_FOP_CANONICAL_MM_V2" not in out


def test_atlas33_u1_apog_protrusion_and_inclination_materialize():
    theta = math.radians(28.0)
    landmarks = {
        "U1_incisal": _lm("U1_incisal", 3.5, 0),
        "U1_apex": _lm("U1_apex", 3.5 - math.sin(theta), math.cos(theta)),
        "A": _lm("A", 0, 0),
        "Pog_hard": _lm("Pog_hard", 0, 10),
        "Po_anatomic": _lm("Po_anatomic", 0, 0),
        "Or": _lm("Or", 10, 0),
    }
    out = _materialize(landmarks)
    protrusion = out["RICKETTS_U1_APOG_PROTRUSION_CANONICAL_MM_V2"]
    inclination = out["RICKETTS_U1_APOG_INCLINATION_CANONICAL_DEG_V2"]
    assert protrusion.availability_status.value == "AVAILABLE"
    assert protrusion.value == pytest.approx(3.5)
    assert inclination.availability_status.value == "AVAILABLE"
    assert inclination.value == pytest.approx(28.0)
    registry = canonical_measurement("M_RICKETTS_U1_APOG_PROTRUSION_MM_V1")
    assert registry is not None
    assert registry.source_status == "GEOMETRY_COVERED_EXPLICIT_U1_EDGE_PERPENDICULAR_APOG_ANTERIOR_POSITIVE"


def test_atlas33_u1_inclination_fails_closed_on_degenerate_axis():
    assert ricketts_u1_apog_inclination_deg_v1(
        (0, 0), (0, 0), (0, 0), (0, 10)
    ) is None


def test_wave_a_registry_keeps_ricketts_overbite_blocked_without_runtime_promotion():
    item = canonical_measurement("M_RICKETTS_OVERBITE_FOP_MM_V1")
    assert item is not None
    assert item.source_status == "CONDITIONAL_EXECUTABLE__IMAGE_ORIENTATION_EVIDENCE_REQUIRED"

    out = _materialize(_base_dental_landmarks())
    assert "RICKETTS_OVERBITE_FOP_CANONICAL_MM_V2" not in out


def test_wave_a_lower_incisor_protrusion_uses_incisal_edge_not_facial_surface():
    edge = canonical_measurement("M_L1_EDGE_APOG_MM_V1")
    facial = canonical_measurement("M_L1_FACIAL_SURFACE_APOG_MM_V1")
    assert edge is not None and edge.source_status == "GEOMETRY_COVERED"
    assert facial is not None and facial.source_status == "BLOCKED_LANDMARK"
