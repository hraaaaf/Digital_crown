"""P2 U6/PTV source evidence tests, synthetics only — NO clinical certification.

Traverses canonical constructions -> measurements -> Atlas/Gregoret profiles -> Focus.
The ratio/reference supplied here are test fixtures; real calibration provenance,
image acquisition correctness and clinical A6 placement are NOT established.
"""
import math

import pytest

from backend.schemas.cephalo_evidence import (
    EvidenceStatus, LandmarkEvidence, LandmarkOrigin,
)
from backend.services.cephalo_canonical_constructions_v2 import (
    RICKETTS_PTV_CONSTRUCTION_ID,
    materialize_canonical_constructions_v2,
)
from backend.services.cephalo_canonical_analysis_v2 import (
    materialize_canonical_analysis_v2_measurements,
)
from backend.services.cephalo_canonical_method_bridge import project_canonical_measurements
from backend.services.cephalo_protocol_projection import (
    project_ricketts_atlas2009_protocol, project_ricketts_gregoret13_protocol,
)
from backend.services.cephalo_runtime_focus import derive_active_runtime_focus

TARGET = "M_U6_PTV_MM_V1"
METHOD = "RICKETTS_U6_PTV_CANONICAL_MM_V2"
COORDS = {
    "U6_DISTAL_Ricketts": (8.0, 5.0),
    "PR_Ricketts_PTV": (2.0, 5.0),
    "Po_anatomic": (0.0, 0.0),
    "Or": (10.0, 0.0),
}


def _landmarks(points=None):
    return {
        name: LandmarkEvidence(
            evidence_id=f"landmark:p2u6:{name}",
            landmark_id=name, x=float(x), y=float(y),
            source_image_ref="source:p2-u6-synthetic",
            origin=LandmarkOrigin.MANUAL,
            evidence_refs=["source:p2-u6-synthetic"],
            evidence_status=EvidenceStatus.OBSERVED,
        )
        for name, (x, y) in (COORDS if points is None else points).items()
    }


def _run(landmarks, *, ratio=0.5, calibration_ref="cal:p2-u6-fixture"):
    constructions = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:p2u6",
    )
    measurements = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:p2u6",
        landmarks=landmarks, mm_per_pixel=ratio,
        calibration_ref=calibration_ref, constructions=constructions,
    )
    canonical_rows = project_canonical_measurements(measurements)["measurements"]
    focus = derive_active_runtime_focus(
        canonical_rows,
        landmarks=landmarks, constructions=constructions,
        measurements={m.measurement_id: m for m in measurements},
    )
    rows = [
        next(row for row in project(canonical_rows)["rows"]
             if row["canonical_measurement_id"] == TARGET)
        for project in (
            project_ricketts_atlas2009_protocol,
            project_ricketts_gregoret13_protocol,
        )
    ]
    measurement = next((m for m in measurements if m.method_id == METHOD), None)
    return constructions[RICKETTS_PTV_CONSTRUCTION_ID], measurement, rows, focus


def _assert_not_promoted(result):
    _, measurement, rows, focus = result
    if measurement is not None:
        assert measurement.availability_status.value != "AVAILABLE"
        assert measurement.value is None
    assert TARGET not in focus
    for row in rows:
        assert row["availability_status"] != "AVAILABLE"
        assert row["value"] is None
        assert row["classification_authority"] is False
        assert row.get("focus_evidence") is None


def _assert_available(result, *, value):
    ptv, measurement, rows, focus = result
    assert ptv.availability_status.value == "AVAILABLE"
    assert measurement is not None
    assert measurement.availability_status.value == "AVAILABLE"
    assert measurement.value == pytest.approx(value)
    assert measurement.unit == "mm"
    assert measurement.requires_calibration is True
    assert measurement.calibration_ref == "cal:p2-u6-fixture"
    assert measurement.construction_refs == [ptv.construction_id]
    assert TARGET in focus
    assert focus[TARGET]["measurement_ref"] == measurement.measurement_id
    assert focus[TARGET]["value_authority_method_id"] == METHOD
    assert focus[TARGET]["landmark_ids"] == ["U6_DISTAL_Ricketts"]
    assert focus[TARGET]["construction_ids"] == [ptv.construction_id]
    assert focus[TARGET]["calibration_required"] is True
    for row in rows:
        assert row["availability_status"] == "AVAILABLE"
        assert row["value"] == pytest.approx(value)
        assert row["measurement_refs"] == [measurement.measurement_id]
        assert row["value_authority_method_id"] == METHOD
        assert row["contract_state"] == "CONDITIONAL_EXECUTABLE"
        assert row["classification_authority"] is False
        assert row["source_contracts"] == [row["source_contract"]]
    # The two sources share an ID, but NOT identical source gate wording.
    assert rows[0]["contract_gate"] != rows[1]["contract_gate"]


def test_explicit_manual_u6_ptv_with_synthetic_calibration_reaches_both_profiles_and_focus():
    _assert_available(_run(_landmarks()), value=3.0)


def test_posterior_is_negative_not_screen_x_or_unsigned_distance():
    points = {**COORDS, "U6_DISTAL_Ricketts": (-4.0, 5.0)}
    _assert_available(_run(_landmarks(points)), value=-3.0)


@pytest.mark.parametrize("transform", [
    lambda x, y: (-y, x),  # 90-degree image rotation
    lambda x, y: (-x, y),  # mirror of the synthetic coordinate system
])
def test_rotation_and_mirror_preserve_signed_anatomical_distance(transform):
    points = {k: transform(*xy) for k, xy in COORDS.items()}
    _assert_available(_run(_landmarks(points)), value=3.0)


@pytest.mark.parametrize("missing", [
    "U6_DISTAL_Ricketts", "PR_Ricketts_PTV", "Po_anatomic", "Or",
])
def test_missing_exact_identity_denies_numeric_value_and_focus(missing):
    landmarks = _landmarks()
    landmarks.pop(missing)
    _assert_not_promoted(_run(landmarks))


@pytest.mark.parametrize("auto", ["U6_DISTAL_Ricketts", "PR_Ricketts_PTV"])
def test_unreviewed_auto_molar_or_pterygoid_point_is_never_authoritative(auto):
    landmarks = _landmarks()
    item = landmarks[auto]
    landmarks[auto] = LandmarkEvidence.model_validate({
        **item.model_dump(), "origin": LandmarkOrigin.SRPOSE38_AUTO,
        "model_id": "p2-synthetic-only", "model_sha256": "a" * 64,
        "pipeline_version": "p2-test-only",
    })
    _assert_not_promoted(_run(landmarks))


@pytest.mark.parametrize("other_source", [
    "U6_DISTAL_Ricketts", "PR_Ricketts_PTV", "Po_anatomic", "Or",
])
def test_mix_of_different_images_is_rejected_at_construction_or_measurement(other_source):
    landmarks = _landmarks()
    landmarks[other_source] = landmarks[other_source].model_copy(
        update={"source_image_ref": "source:other-synthetic-image"}
    )
    _assert_not_promoted(_run(landmarks))


@pytest.mark.parametrize("ratio,ref", [
    (None, None), (0.5, None), (None, "cal:p2-u6-fixture"),
    (0.0, "cal:p2-u6-fixture"), (-0.5, "cal:p2-u6-fixture"),
    (math.nan, "cal:p2-u6-fixture"),
])
def test_absent_or_nonpositive_or_nonfinite_calibration_fails_closed(ratio, ref):
    _assert_not_promoted(_run(_landmarks(), ratio=ratio, calibration_ref=ref))


def test_degenerate_anatomical_frankfort_refuses_ptv_and_both_profiles():
    points = {**COORDS, "Or": COORDS["Po_anatomic"]}
    result = _run(_landmarks(points))
    assert result[0].availability_status.value == "INVALID"
    _assert_not_promoted(result)


@pytest.mark.parametrize("replacement", [
    {"PR_Ricketts_PTV": "Pt_Ricketts"},
    {"PR_Ricketts_PTV": "PTV"},
    {"U6_DISTAL_Ricketts": "U6"},
    {"U6_DISTAL_Ricketts": "U6_CUSP"},
])
def test_generic_aliases_are_not_promoted_to_authoritative_ptv_or_u6(replacement):
    landmarks = _landmarks()
    for original, alias in replacement.items():
        landmarks[alias] = landmarks.pop(original).model_copy(
            update={"landmark_id": alias, "evidence_id": "landmark:p2u6:" + alias}
        )
    _assert_not_promoted(_run(landmarks))
