import math
import pytest

from backend.schemas.cephalo_evidence import EvidenceStatus, LandmarkEvidence, LandmarkOrigin
from backend.services.cephalo_canonical_analysis_v2 import materialize_canonical_analysis_v2_measurements
from backend.services.cephalo_canonical_constructions_v2 import (
    RICKETTS_CC_ATLAS2009_CONSTRUCTION_ID,
    RICKETTS_CF_CONSTRUCTION_ID,
    materialize_canonical_constructions_v2,
)
from backend.services.cephalo_measure_registry import canonical_measurement
from backend.services.cephalo_ricketts_geometry import (
    ricketts_cc_atlas2009_v1,
    ricketts_cranial_deflection_deg_v1,
    ricketts_point_distance_px_v1,
    ricketts_porion_location_signed_px_v1,
    ricketts_ramus_position_deg_v1,
    ricketts_total_facial_height_deg_v1,
)


def _lm(landmark_id, x, y, source_image_ref="source:wave-c"):
    return LandmarkEvidence(
        evidence_id=f"landmark:wave-c:{landmark_id}",
        landmark_id=landmark_id,
        x=float(x),
        y=float(y),
        source_image_ref=source_image_ref,
        origin=LandmarkOrigin.MANUAL,
        evidence_refs=[source_image_ref],
        evidence_status=EvidenceStatus.OBSERVED,
    )


def _auto(landmark_id, x, y, source_image_ref="source:wave-c"):
    return LandmarkEvidence(
        evidence_id=f"landmark:wave-c:auto:{landmark_id}",
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
        "Ba": _lm("Ba", 0, 10),
        "N": _lm("N", 10, 10),
        "Pt_Ricketts": _lm("Pt_Ricketts", 0, 20),
        "Pog_hard": _lm("Pog_hard", 10, 0),
        "Go": _lm("Go", 0, 0),
        "Me": _lm("Me", 10, 0),
        "GO_Ricketts_PFH": _lm("GO_Ricketts_PFH", 4, 14),
        "R1_Ricketts": _lm("R1_Ricketts", 0, 10),
        "R2_Ricketts": _lm("R2_Ricketts", 10, 10),
        "R3_Ricketts": _lm("R3_Ricketts", 5, 5),
        "R4_Ricketts": _lm("R4_Ricketts", 5, 15),
        "Pm_Ricketts": _lm("Pm_Ricketts", 8, 15),
    }


def _materialize(landmarks=None, mm_per_pixel=1.0, calibration_ref="calibration:wave-c"):
    landmarks = landmarks or _landmarks()
    constructions = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:wave-c"
    )
    out = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:wave-c",
        landmarks=landmarks,
        mm_per_pixel=mm_per_pixel,
        calibration_ref=calibration_ref,
        constructions=constructions,
    )
    return constructions, {item.method_id: item for item in out}


def test_wave_c_geometry_primitives_are_deterministic():
    assert ricketts_cc_atlas2009_v1(
        (0, 10), (10, 10), (0, 20), (10, 0)
    ) == pytest.approx((5, 10))
    assert ricketts_cranial_deflection_deg_v1(
        (0, 0), (10, 0), (0, 10), (10, 10)
    ) == pytest.approx(0.0)
    assert ricketts_point_distance_px_v1((5, 10), (8, 15)) == pytest.approx(math.sqrt(34))
    assert ricketts_total_facial_height_deg_v1(
        (0, 10), (10, 10), (5, 10), (8, 15)
    ) == pytest.approx(59.03624346792648)
    assert ricketts_ramus_position_deg_v1(
        (0, 0), (10, 0), (4, 0), (5, 10)
    ) == pytest.approx(84.28940686250037)
    assert ricketts_porion_location_signed_px_v1(
        (0, 0), (4, 7), (1, 0)
    ) == pytest.approx(-4.0)


def test_wave_c_cc_uses_atlas_ban_ptgn_contract_and_manual_pt():
    constructions, _ = _materialize()
    cc = constructions[RICKETTS_CC_ATLAS2009_CONSTRUCTION_ID]
    assert cc.availability_status.value == "AVAILABLE"
    assert cc.geometry["x"] == pytest.approx(5.0)
    assert cc.geometry["y"] == pytest.approx(10.0)
    assert cc.geometry["constructed_landmark_id"] == "CC_Ricketts_Atlas2009"
    assert cc.geometry["upstream_construction_id"].endswith(
        "RICKETTS_GN_CONSTRUCTED_NPOG_GOME_V1"
    )

    landmarks = _landmarks()
    landmarks["Pt_Ricketts"] = _auto("Pt_Ricketts", 0, 20)
    constructions, _ = _materialize(landmarks)
    assert constructions[RICKETTS_CC_ATLAS2009_CONSTRUCTION_ID].availability_status.value == "NOT_COMPUTABLE"


def test_wave_c_materializes_internal_structures_with_source_locked_dependencies():
    constructions, out = _materialize()
    assert constructions[RICKETTS_CF_CONSTRUCTION_ID].availability_status.value == "AVAILABLE"
    expected = {
        "RICKETTS_CRANIAL_DEFLECTION_CANONICAL_DEG_V2",
        "RICKETTS_ANTERIOR_CRANIAL_LENGTH_CANONICAL_MM_V2",
        "RICKETTS_POSTERIOR_FACIAL_HEIGHT_CANONICAL_MM_V2",
        "RICKETTS_TOTAL_FACIAL_HEIGHT_CANONICAL_DEG_V2",
        "RICKETTS_RAMUS_POSITION_CANONICAL_DEG_V2",
        "RICKETTS_PORION_LOCATION_CANONICAL_MM_V2",
        "RICKETTS_CORPUS_LENGTH_CANONICAL_MM_V2",
    }
    assert expected <= set(out)
    assert all(out[method].availability_status.value == "AVAILABLE" for method in expected)
    assert out["RICKETTS_ANTERIOR_CRANIAL_LENGTH_CANONICAL_MM_V2"].value == pytest.approx(5.0)
    assert out["RICKETTS_POSTERIOR_FACIAL_HEIGHT_CANONICAL_MM_V2"].value == pytest.approx(14.0)
    assert out["RICKETTS_PORION_LOCATION_CANONICAL_MM_V2"].value == pytest.approx(-4.0)
    assert out["RICKETTS_CORPUS_LENGTH_CANONICAL_MM_V2"].value == pytest.approx(math.sqrt(34))


def test_wave_c_manual_authority_gates_fail_closed():
    landmarks = _landmarks()
    landmarks["GO_Ricketts_PFH"] = _auto("GO_Ricketts_PFH", 4, 14)
    _, out = _materialize(landmarks)
    assert out["RICKETTS_POSTERIOR_FACIAL_HEIGHT_CANONICAL_MM_V2"].availability_status.value == "NOT_COMPUTABLE"

    landmarks = _landmarks()
    landmarks["Pm_Ricketts"] = _auto("Pm_Ricketts", 8, 15)
    _, out = _materialize(landmarks)
    assert out["RICKETTS_TOTAL_FACIAL_HEIGHT_CANONICAL_DEG_V2"].availability_status.value == "NOT_COMPUTABLE"
    assert out["RICKETTS_CORPUS_LENGTH_CANONICAL_MM_V2"].availability_status.value == "NOT_COMPUTABLE"


def test_wave_c_linear_measurements_require_verified_calibration():
    _, out = _materialize(mm_per_pixel=None, calibration_ref=None)
    for method in (
        "RICKETTS_ANTERIOR_CRANIAL_LENGTH_CANONICAL_MM_V2",
        "RICKETTS_POSTERIOR_FACIAL_HEIGHT_CANONICAL_MM_V2",
        "RICKETTS_PORION_LOCATION_CANONICAL_MM_V2",
        "RICKETTS_CORPUS_LENGTH_CANONICAL_MM_V2",
    ):
        assert out[method].availability_status.value == "NOT_COMPUTABLE"
        assert out[method].value is None


def test_wave_c_cross_image_evidence_is_invalid():
    landmarks = _landmarks()
    landmarks["GO_Ricketts_PFH"] = _lm("GO_Ricketts_PFH", 4, 14, "source:other")
    _, out = _materialize(landmarks)
    assert out["RICKETTS_POSTERIOR_FACIAL_HEIGHT_CANONICAL_MM_V2"].availability_status.value == "INVALID"

    landmarks = _landmarks()
    landmarks["Pm_Ricketts"] = _lm("Pm_Ricketts", 8, 15, "source:other")
    _, out = _materialize(landmarks)
    assert out["RICKETTS_CORPUS_LENGTH_CANONICAL_MM_V2"].availability_status.value == "INVALID"


def test_wave_c_generic_go_does_not_unlock_posterior_facial_height():
    landmarks = _landmarks()
    landmarks.pop("GO_Ricketts_PFH")
    _, out = _materialize(landmarks)
    assert "RICKETTS_POSTERIOR_FACIAL_HEIGHT_CANONICAL_MM_V2" not in out


def test_wave_c_factor29_is_resolved_as_total_facial_height_not_duplicate_pfh():
    total = canonical_measurement("M_RICKETTS_TOTAL_FACIAL_HEIGHT_BAN_XIPM_DEG_V1")
    posterior = canonical_measurement("M_RICKETTS_POSTERIOR_FACIAL_HEIGHT_GO_CF_MM_V1")
    assert total is not None
    assert posterior is not None
    assert total.unit == "°"
    assert posterior.unit == "mm"
    assert "TOTAL_FACIAL_HEIGHT" in total.source_status
