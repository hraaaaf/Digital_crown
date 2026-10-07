import math
import pytest

from backend.schemas.cephalo_evidence import EvidenceStatus, LandmarkEvidence, LandmarkOrigin
from backend.services.cephalo_canonical_analysis_v2 import materialize_canonical_analysis_v2_measurements
from backend.services.cephalo_canonical_constructions_v2 import (
    RICKETTS_CF_CONSTRUCTION_ID,
    materialize_canonical_constructions_v2,
)
from backend.services.cephalo_measure_registry import canonical_measurement
from backend.services.cephalo_ricketts_geometry import (
    ricketts_line_angle_acute_deg_v1,
    ricketts_maxillary_height_n_cf_a_deg_v1,
    ricketts_upper_lip_length_px_v1,
)


def _lm(landmark_id, x, y, source_image_ref="source:wave-b"):
    return LandmarkEvidence(
        evidence_id=f"landmark:wave-b:{landmark_id}",
        landmark_id=landmark_id,
        x=float(x),
        y=float(y),
        source_image_ref=source_image_ref,
        origin=LandmarkOrigin.MANUAL,
        evidence_refs=[source_image_ref],
        evidence_status=EvidenceStatus.OBSERVED,
    )


def _auto(landmark_id, x, y, source_image_ref="source:wave-b"):
    return LandmarkEvidence(
        evidence_id=f"landmark:wave-b:auto:{landmark_id}",
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


def _landmarks():
    return {
        "Po_anatomic": _lm("Po_anatomic", 0, 0),
        "Or": _lm("Or", 10, 0),
        "PR_Ricketts_PTV": _lm("PR_Ricketts_PTV", 4, 7),
        "FOP_PREMOLAR_Ricketts": _lm("FOP_PREMOLAR_Ricketts", 0, 5),
        "FOP_MOLAR_Ricketts": _lm("FOP_MOLAR_Ricketts", 10, 5),
        "R1_Ricketts": _lm("R1_Ricketts", 0, 10),
        "R2_Ricketts": _lm("R2_Ricketts", 10, 10),
        "R3_Ricketts": _lm("R3_Ricketts", 5, 5),
        "R4_Ricketts": _lm("R4_Ricketts", 5, 15),
        "Pm_Ricketts": _lm("Pm_Ricketts", 8, 15),
        "ANS": _lm("ANS", 0, 2),
        "LABIAL_COMMISSURE_Ricketts": _lm("LABIAL_COMMISSURE_Ricketts", 3, 6),
        "MP_ANGLE_INFERIOR_Ricketts": _lm("MP_ANGLE_INFERIOR_Ricketts", 0, 0),
        "Me": _lm("Me", 10, 0),
        "N": _lm("N", 0, 8),
        "Pog_hard": _lm("Pog_hard", 8, 0),
        "A": _lm("A", 8, 8),
        "PNS_Ricketts": _lm("PNS_Ricketts", 10, 2),
    }


def _materialize(landmarks=None, mm_per_pixel=1.0, calibration_ref="calibration:wave-b"):
    landmarks = landmarks or _landmarks()
    constructions = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:wave-b"
    )
    out = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:wave-b",
        landmarks=landmarks,
        mm_per_pixel=mm_per_pixel,
        calibration_ref=calibration_ref,
        constructions=constructions,
    )
    return constructions, {item.method_id: item for item in out}


def test_wave_b_geometry_primitives_are_deterministic():
    assert ricketts_line_angle_acute_deg_v1((1, 0), (1, 1)) == pytest.approx(45.0)
    assert ricketts_line_angle_acute_deg_v1((-1, 0), (1, 1)) == pytest.approx(45.0)
    assert ricketts_upper_lip_length_px_v1((0, 2), (3, 6)) == pytest.approx(5.0)
    assert ricketts_maxillary_height_n_cf_a_deg_v1(
        (0, 8), (4, 0), (8, 8)
    ) == pytest.approx(53.13010235415598)


def test_wave_b_cf_is_constructed_only_from_source_locked_ptv_and_fh():
    constructions, _ = _materialize()
    cf = constructions[RICKETTS_CF_CONSTRUCTION_ID]
    assert cf.availability_status.value == "AVAILABLE"
    assert cf.geometry["x"] == pytest.approx(4.0)
    assert cf.geometry["y"] == pytest.approx(0.0)
    assert cf.geometry["constructed_landmark_id"] == "CF_Ricketts"
    assert cf.geometry["upstream_construction_id"].endswith("RICKETTS_PTV_PR_POSTERIOR_PPF_PERP_FH_V1")

    landmarks = _landmarks()
    landmarks["PR_Ricketts_PTV"] = _auto("PR_Ricketts_PTV", 4, 7)
    constructions, _ = _materialize(landmarks)
    assert constructions[RICKETTS_CF_CONSTRUCTION_ID].availability_status.value == "NOT_COMPUTABLE"


def test_wave_b_runtime_materializes_only_source_locked_executable_factors():
    constructions, out = _materialize()
    assert constructions[RICKETTS_CF_CONSTRUCTION_ID].availability_status.value == "AVAILABLE"

    expected = {
        "RICKETTS_OCCLUSAL_PLANE_XIPM_CANONICAL_DEG_V2",
        "RICKETTS_UPPER_LIP_LENGTH_CANONICAL_MM_V2",
        "RICKETTS_FACIAL_TAPER_CANONICAL_DEG_V2",
        "RICKETTS_MAXILLARY_HEIGHT_CANONICAL_DEG_V2",
    }
    assert expected <= set(out)
    assert all(out[method].availability_status.value == "AVAILABLE" for method in expected)
    assert out["RICKETTS_UPPER_LIP_LENGTH_CANONICAL_MM_V2"].value == pytest.approx(5.0)
    assert out["RICKETTS_FACIAL_TAPER_CANONICAL_DEG_V2"].value == pytest.approx(45.0)
    assert out["RICKETTS_MAXILLARY_HEIGHT_CANONICAL_DEG_V2"].value == pytest.approx(53.13010235415598)


def test_wave_b_authority_gates_fail_closed():
    landmarks = _landmarks()
    landmarks["Pm_Ricketts"] = _auto("Pm_Ricketts", 8, 15)
    _, out = _materialize(landmarks)
    assert out["RICKETTS_OCCLUSAL_PLANE_XIPM_CANONICAL_DEG_V2"].availability_status.value == "NOT_COMPUTABLE"

    landmarks = _landmarks()
    landmarks["LABIAL_COMMISSURE_Ricketts"] = _auto("LABIAL_COMMISSURE_Ricketts", 3, 6)
    _, out = _materialize(landmarks)
    assert out["RICKETTS_UPPER_LIP_LENGTH_CANONICAL_MM_V2"].availability_status.value == "NOT_COMPUTABLE"



def test_wave_b_linear_lip_length_requires_verified_calibration():
    _, out = _materialize(mm_per_pixel=None, calibration_ref=None)
    item = out["RICKETTS_UPPER_LIP_LENGTH_CANONICAL_MM_V2"]
    assert item.availability_status.value == "NOT_COMPUTABLE"
    assert item.value is None


def test_wave_b_rejects_cross_image_dependencies():
    landmarks = _landmarks()
    landmarks["A"] = _lm("A", 8, 8, "source:other")
    _, out = _materialize(landmarks)
    item = out["RICKETTS_MAXILLARY_HEIGHT_CANONICAL_DEG_V2"]
    assert item.availability_status.value == "INVALID"
    assert item.value is None


def test_wave_b_blocked_signed_distances_have_no_runtime_method():
    _, out = _materialize()
    assert out["RICKETTS_OCCLUSAL_PLANE_XI_CANONICAL_MM_V2"].availability_status.value == "NOT_COMPUTABLE"
    assert out["RICKETTS_COMMISSURE_FOP_CANONICAL_MM_V2"].availability_status.value == "NOT_COMPUTABLE"

    op_xi = canonical_measurement("M_RICKETTS_OCCLUSAL_PLANE_XI_MM_V1")
    commissure = canonical_measurement("M_RICKETTS_COMMISSURE_FOP_MM_V1")
    palatal = canonical_measurement("M_RICKETTS_PALATAL_PLANE_FH_DEG_V1")
    assert op_xi is not None
    assert commissure is not None
    assert palatal is not None
    assert op_xi.source_status == "CONDITIONAL_EXECUTABLE__IMAGE_ORIENTATION_EVIDENCE_REQUIRED"
    assert commissure.source_status == "CONDITIONAL_EXECUTABLE__IMAGE_ORIENTATION_EVIDENCE_REQUIRED"
    assert palatal.source_status == "CONDITIONAL_EXECUTABLE__IMAGE_ORIENTATION_EVIDENCE_REQUIRED"


def test_wave_b_generic_soft_tissue_and_pns_aliases_are_not_promoted():
    landmarks = _landmarks()
    landmarks.pop("LABIAL_COMMISSURE_Ricketts")
    landmarks.pop("PNS_Ricketts")
    landmarks["Em"] = _lm("Em", 3, 6)
    landmarks["PNS"] = _lm("PNS", 10, 2)
    _, out = _materialize(landmarks)
    lip = out["RICKETTS_UPPER_LIP_LENGTH_CANONICAL_MM_V2"]
    assert lip.availability_status.value == "NOT_COMPUTABLE"
    assert lip.value is None
    palatal = out["RICKETTS_PALATAL_PLANE_FH_CANONICAL_DEG_V2"]
    assert palatal.availability_status.value == "NOT_COMPUTABLE"
    assert palatal.value is None
