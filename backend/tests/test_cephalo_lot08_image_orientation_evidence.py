import datetime as dt
import math

import pytest

from backend.schemas.cephalo_evidence import (
    AvailabilityStatus,
    EvidenceStatus,
    ImageOrientationEvidence,
    ImageOrientationOrigin,
    LandmarkEvidence,
    LandmarkOrigin,
    MeasurementEvidence,
    SourceEvidence,
)
from backend.services.cephalo_canonical_analysis_v2 import materialize_canonical_analysis_v2_measurements
from backend.services.cephalo_canonical_constructions_v2 import materialize_canonical_constructions_v2
from backend.services.cephalo_evidence_graph import EvidenceGraphSnapshot, EvidenceGraphValidationError, validate_evidence_graph


def _lm(landmark_id, x, y, source="source:orientation"):
    return LandmarkEvidence(
        evidence_id=f"landmark:orientation:{landmark_id}",
        landmark_id=landmark_id,
        x=float(x),
        y=float(y),
        source_image_ref=source,
        origin=LandmarkOrigin.MANUAL,
        evidence_refs=[source],
        evidence_status=EvidenceStatus.OBSERVED,
    )


def _orientation(source="source:orientation"):
    return ImageOrientationEvidence(
        evidence_id="orientation:source:orientation:v1",
        source_image_ref=source,
        anterior_x=1.0,
        anterior_y=0.0,
        superior_x=0.0,
        superior_y=1.0,
        is_mirrored=False,
        origin=ImageOrientationOrigin.ACQUISITION_METADATA,
        provenance_ref=source,
        evidence_refs=[source],
    )


def _landmarks():
    return {
        "Po_anatomic": _lm("Po_anatomic", 0, 0),
        "Or": _lm("Or", 10, 0),
        "FOP_PREMOLAR_Ricketts": _lm("FOP_PREMOLAR_Ricketts", 0, 0),
        "FOP_MOLAR_Ricketts": _lm("FOP_MOLAR_Ricketts", 10, 0),
        "U1_incisal": _lm("U1_incisal", 5, -1),
        "L1_incisal": _lm("L1_incisal", 5, 1),
        "LABIAL_COMMISSURE_Ricketts": _lm("LABIAL_COMMISSURE_Ricketts", 5, 2),
        "ANS": _lm("ANS", 10, math.tan(math.radians(10))),
        "PNS_Ricketts": _lm("PNS_Ricketts", 0, 0),
        "R1_Ricketts": _lm("R1_Ricketts", 0, -3),
        "R2_Ricketts": _lm("R2_Ricketts", 2, -3),
        "R3_Ricketts": _lm("R3_Ricketts", 1, -4),
        "R4_Ricketts": _lm("R4_Ricketts", 1, -2),
    }


def _materialize(*, orientation):
    landmarks = _landmarks()
    constructions = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:orientation"
    )
    out = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:orientation",
        landmarks=landmarks,
        mm_per_pixel=1.0,
        calibration_ref="source:calibration",
        constructions=constructions,
        image_orientation=orientation,
    )
    return {item.method_id: item for item in out}


def test_orientation_schema_rejects_non_orthogonal_axes_and_unaudited_manual():
    with pytest.raises(ValueError):
        ImageOrientationEvidence(
            evidence_id="orientation:bad",
            source_image_ref="source:orientation",
            anterior_x=1,
            anterior_y=0,
            superior_x=1,
            superior_y=1,
            is_mirrored=False,
            origin=ImageOrientationOrigin.ACQUISITION_METADATA,
            provenance_ref="source:orientation",
            evidence_refs=["source:orientation"],
        )

    with pytest.raises(ValueError):
        ImageOrientationEvidence(
            evidence_id="orientation:manual",
            source_image_ref="source:orientation",
            anterior_x=1,
            anterior_y=0,
            superior_x=0,
            superior_y=1,
            is_mirrored=False,
            origin=ImageOrientationOrigin.MANUAL_VERIFIED,
            provenance_ref="validation:missing",
            evidence_refs=["source:orientation"],
        )

    manual = ImageOrientationEvidence(
        evidence_id="orientation:manual-ok",
        source_image_ref="source:orientation",
        anterior_x=1,
        anterior_y=0,
        superior_x=0,
        superior_y=1,
        is_mirrored=False,
        origin=ImageOrientationOrigin.MANUAL_VERIFIED,
        provenance_ref="validation:orientation",
        validated_by="clinician:test",
        validated_at=dt.datetime(2026, 10, 6, tzinfo=dt.timezone.utc),
        evidence_refs=["source:orientation"],
    )
    assert manual.availability_status.value == "AVAILABLE"


def test_signed_ricketts_contracts_fail_closed_without_orientation():
    out = _materialize(orientation=None)
    for method in (
        "RICKETTS_OVERBITE_FOP_CANONICAL_MM_V2",
        "RICKETTS_OCCLUSAL_PLANE_XI_CANONICAL_MM_V2",
        "RICKETTS_COMMISSURE_FOP_CANONICAL_MM_V2",
        "RICKETTS_PALATAL_PLANE_FH_CANONICAL_DEG_V2",
    ):
        assert out[method].availability_status.value == "NOT_COMPUTABLE"
        assert out[method].value is None
        assert out[method].orientation_ref is None


def test_signed_ricketts_contracts_unlock_with_same_image_orientation():
    out = _materialize(orientation=_orientation())

    overbite = out["RICKETTS_OVERBITE_FOP_CANONICAL_MM_V2"]
    fop_xi = out["RICKETTS_OCCLUSAL_PLANE_XI_CANONICAL_MM_V2"]
    commissure = out["RICKETTS_COMMISSURE_FOP_CANONICAL_MM_V2"]
    palatal = out["RICKETTS_PALATAL_PLANE_FH_CANONICAL_DEG_V2"]

    assert overbite.availability_status.value == "AVAILABLE"
    assert overbite.value == pytest.approx(2.0)
    assert fop_xi.availability_status.value == "AVAILABLE"
    assert fop_xi.value == pytest.approx(3.0)
    assert commissure.availability_status.value == "AVAILABLE"
    assert commissure.value == pytest.approx(-2.0)
    assert palatal.availability_status.value == "AVAILABLE"
    assert palatal.value == pytest.approx(10.0)

    for item in (overbite, fop_xi, commissure, palatal):
        assert item.orientation_ref == "orientation:source:orientation:v1"
        assert item.orientation_ref in item.evidence_refs


def test_orientation_evidence_must_match_source_image():
    out = _materialize(orientation=_orientation("source:other"))
    for method in (
        "RICKETTS_OVERBITE_FOP_CANONICAL_MM_V2",
        "RICKETTS_OCCLUSAL_PLANE_XI_CANONICAL_MM_V2",
        "RICKETTS_COMMISSURE_FOP_CANONICAL_MM_V2",
        "RICKETTS_PALATAL_PLANE_FH_CANONICAL_DEG_V2",
    ):
        assert out[method].availability_status.value == "NOT_COMPUTABLE"
        assert out[method].value is None


def test_orientation_ref_is_referentially_validated():
    source = SourceEvidence(
        evidence_id="source:orientation",
        patient_id=1,
        kind="lateral_ceph",
        source_record_id="image:1",
        recorded_at=dt.datetime(2026, 10, 6, tzinfo=dt.timezone.utc),
    )
    landmark = _lm("U1_incisal", 1, 1)
    orientation = _orientation()
    measurement = MeasurementEvidence(
        measurement_id="measurement:orientation:test",
        analysis_id="RICKETTS",
        method_id="TEST_ORIENTATION_METHOD",
        method_version="1",
        value=1.0,
        unit="mm",
        landmark_refs=[landmark.evidence_id],
        orientation_ref=orientation.evidence_id,
        evidence_refs=[landmark.evidence_id, orientation.evidence_id],
        availability_status=AvailabilityStatus.AVAILABLE,
    )
    graph = EvidenceGraphSnapshot(
        sources=[source],
        landmarks=[landmark],
        image_orientations=[orientation],
        measurements=[measurement],
    )
    validate_evidence_graph(graph)

    bad = EvidenceGraphSnapshot(
        sources=[source],
        landmarks=[landmark],
        measurements=[measurement],
    )
    with pytest.raises(EvidenceGraphValidationError):
        validate_evidence_graph(bad)
