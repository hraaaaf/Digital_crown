import pytest

from backend.schemas.cephalo_evidence import (
    AvailabilityStatus,
    EvidenceStatus,
    LandmarkEvidence,
    LandmarkOrigin,
)
from backend.services import cephalo_mcnamara_evidence as mcnamara
from backend.services.cephalo_constructions import signed_axis_distance_px_v1


def _lm(
    landmark_id: str,
    x: float,
    y: float,
    *,
    source: str = "source:case:ceph",
) -> LandmarkEvidence:
    return LandmarkEvidence(
        evidence_id=f"landmark:case:{landmark_id}",
        landmark_id=landmark_id,
        x=x,
        y=y,
        source_image_ref=source,
        origin=LandmarkOrigin.MANUAL,
        evidence_refs=[source],
        evidence_status=EvidenceStatus.OBSERVED,
    )


def _landmarks(*, a_x: float = 4.0, pog_x: float = -3.0):
    return {
        "N": _lm("N", 0.0, 0.0),
        "Po": _lm("Po", 0.0, 10.0),
        "Or": _lm("Or", 10.0, 10.0),
        "A": _lm("A", a_x, 3.0),
        "Pog": _lm("Pog", pog_x, 2.0),
    }


def test_signed_axis_distance_pixel_primitive_is_fail_closed():
    assert signed_axis_distance_px_v1((4.0, 2.0), (0.0, 0.0), (1.0, 0.0)) == pytest.approx(4.0)
    assert signed_axis_distance_px_v1((-4.0, 2.0), (0.0, 0.0), (1.0, 0.0)) == pytest.approx(-4.0)
    assert signed_axis_distance_px_v1((4.0, 2.0), (0.0, 0.0), (2.0, 0.0)) is None


def test_mcnamara_nperp_values_are_signed_calibrated_and_canonical():
    constructions = mcnamara.materialize_mcnamara_nperp_constructions(
        _landmarks(), construction_namespace="construction:case:mcnamara"
    )
    measurements = mcnamara.adapt_mcnamara_nperp_measurements(
        measurement_namespace="measurement:case:mcnamara",
        constructions=constructions,
        mm_per_pixel=0.5,
        calibration_ref="source:case:calibration",
    )

    by_method = {item.method_id: item for item in measurements}
    a = by_method["M_A_NPERP_MM_V1"]
    pog = by_method["M_POG_NPERP_MM_V1"]

    assert a.value == pytest.approx(2.0)
    assert pog.value == pytest.approx(-1.5)
    assert a.unit == pog.unit == "mm"
    assert a.availability_status == AvailabilityStatus.AVAILABLE
    assert pog.availability_status == AvailabilityStatus.AVAILABLE
    assert a.requires_calibration and pog.requires_calibration
    assert a.calibration_ref == pog.calibration_ref == "source:case:calibration"
    assert "M_B_NPERP_MM_V1" not in by_method


def test_mcnamara_nperp_zero_is_a_valid_signed_measurement():
    constructions = mcnamara.materialize_mcnamara_nperp_constructions(
        _landmarks(a_x=0.0, pog_x=0.0), construction_namespace="construction:case:mcnamara"
    )
    measurements = mcnamara.adapt_mcnamara_nperp_measurements(
        measurement_namespace="measurement:case:mcnamara",
        constructions=constructions,
        mm_per_pixel=0.5,
        calibration_ref="source:case:calibration",
    )
    assert [item.value for item in measurements] == pytest.approx([0.0, 0.0])
    assert all(item.availability_status == AvailabilityStatus.AVAILABLE for item in measurements)


def test_mcnamara_nperp_requires_verified_calibration_pair():
    constructions = mcnamara.materialize_mcnamara_nperp_constructions(
        _landmarks(), construction_namespace="construction:case:mcnamara"
    )
    unavailable = mcnamara.adapt_mcnamara_nperp_measurements(
        measurement_namespace="measurement:case:mcnamara",
        constructions=constructions,
        mm_per_pixel=None,
        calibration_ref=None,
    )
    assert all(item.value is None for item in unavailable)
    assert all(item.availability_status == AvailabilityStatus.NOT_COMPUTABLE for item in unavailable)

    invalid = mcnamara.adapt_mcnamara_nperp_measurements(
        measurement_namespace="measurement:case:mcnamara",
        constructions=constructions,
        mm_per_pixel=0.5,
        calibration_ref=None,
    )
    assert all(item.value is None for item in invalid)
    assert all(item.availability_status == AvailabilityStatus.INVALID for item in invalid)


def test_mcnamara_nperp_rejects_cross_image_geometry():
    landmarks = _landmarks()
    landmarks["Or"] = _lm("Or", 10.0, 10.0, source="source:other:ceph")
    constructions = mcnamara.materialize_mcnamara_nperp_constructions(
        landmarks, construction_namespace="construction:case:mcnamara"
    )
    assert all(
        item.availability_status == AvailabilityStatus.INVALID
        for item in constructions.values()
    )


def test_mcnamara_nperp_fails_closed_if_canonical_unit_is_unlocked(monkeypatch):
    constructions = mcnamara.materialize_mcnamara_nperp_constructions(
        _landmarks(), construction_namespace="construction:case:mcnamara"
    )
    monkeypatch.setattr(mcnamara, "canonical_unit", lambda _measurement_id: None)
    with pytest.raises(ValueError, match="Canonical unit is not source-locked"):
        mcnamara.adapt_mcnamara_nperp_measurements(
            measurement_namespace="measurement:case:mcnamara",
            constructions=constructions,
            mm_per_pixel=0.5,
            calibration_ref="source:case:calibration",
        )
