"""R23-G P2 Xi/Pm: synthetic active evidence -> canonical -> Atlas/Gregoret -> Focus.

This is an executable technical refusal test, NOT a radiographic or clinical oracle.
No patient material, norms, VERT, diagnosis or activation.
"""
import pytest

from backend.schemas.cephalo_evidence import EvidenceStatus, LandmarkEvidence, LandmarkOrigin
from backend.services.cephalo_canonical_analysis_v2 import materialize_canonical_analysis_v2_measurements
from backend.services.cephalo_canonical_constructions_v2 import (
    RICKETTS_XI_CONSTRUCTION_ID,
    materialize_canonical_constructions_v2,
)
from backend.services.cephalo_canonical_method_bridge import project_canonical_measurements
from backend.services.cephalo_protocol_projection import (
    project_ricketts_atlas2009_protocol,
    project_ricketts_gregoret13_protocol,
)
from backend.services.cephalo_runtime_focus import derive_active_runtime_focus


TARGET = "M_ORAL_GNOMON_ANS_XI_PM_DEG_V1"
METHOD = "RICKETTS_LOWER_FACIAL_HEIGHT_CANONICAL_DEG_V2"
COORDS = {
    "ANS": (5, -4),
    "Pm_Ricketts": (15, 6),
    "R1_Ricketts": (2, 5),
    "R2_Ricketts": (8, 5),
    "R3_Ricketts": (5, 2),
    "R4_Ricketts": (5, 10),
    "Po_anatomic": (0, 0),
    "Or": (10, 0),
}


def _landmarks():
    return {
        key: LandmarkEvidence(
            evidence_id=f"landmark:p2:{key}", landmark_id=key,
            x=float(x), y=float(y), source_image_ref="source:p2-synthetic",
            origin=LandmarkOrigin.MANUAL, evidence_refs=["source:p2-synthetic"],
            evidence_status=EvidenceStatus.OBSERVED,
        )
        for key, (x, y) in COORDS.items()
    }


def _run(landmarks):
    constructions = materialize_canonical_constructions_v2(
        landmarks, construction_namespace="construction:p2"
    )
    measurements = materialize_canonical_analysis_v2_measurements(
        measurement_namespace="measurement:p2", landmarks=landmarks,
        mm_per_pixel=None, calibration_ref=None, constructions=constructions,
    )
    canonical = project_canonical_measurements(measurements)["measurements"]
    focused = derive_active_runtime_focus(
        canonical, landmarks=landmarks, constructions=constructions,
        measurements={row.measurement_id: row for row in measurements},
    )
    projections = [
        project_ricketts_atlas2009_protocol(canonical),
        project_ricketts_gregoret13_protocol(canonical),
    ]
    rows = [
        next(row for row in profile["rows"]
             if row["canonical_measurement_id"] == TARGET)
        for profile in projections
    ]
    measured = next(row for row in measurements if row.method_id == METHOD)
    return constructions[RICKETTS_XI_CONSTRUCTION_ID], measured, rows, focused


def test_valid_source_locked_xi_pm_evidence_survives_both_profiles_without_classification():
    xi, measurement, rows, focus = _run(_landmarks())
    assert xi.availability_status.value == "AVAILABLE"
    assert measurement.availability_status.value == "AVAILABLE"
    assert measurement.value == pytest.approx(90.0)
    assert measurement.construction_refs == [xi.construction_id]
    assert TARGET in focus
    assert focus[TARGET]["value_authority_method_id"] == METHOD
    assert focus[TARGET]["construction_ids"] == [xi.construction_id]
    assert set(focus[TARGET]["landmark_ids"]) == {"ANS", "Pm_Ricketts"}
    for row in rows:
        assert row["availability_status"] == "AVAILABLE"
        assert row["value"] == pytest.approx(90.0)
        assert row["value_authority_method_id"] == METHOD
        assert row["classification_authority"] is False
        assert row["contract_state"] == "CONDITIONAL_EXECUTABLE"
        assert row["focus_evidence"] if "focus_evidence" in row else True
    # The profile-specific source gates are distinct; sharing a canonical
    # calculation does NOT by itself validate either clinical protocol.
    assert rows[0]["contract_gate"] != rows[1]["contract_gate"]


@pytest.mark.parametrize("missing", [
    "R1_Ricketts", "R2_Ricketts", "R3_Ricketts", "R4_Ricketts",
    "Po_anatomic", "Or", "Pm_Ricketts", "ANS",
])
def test_missing_manual_or_anatomical_anchor_cannot_promote_value_or_focus(missing):
    landmarks = _landmarks()
    landmarks.pop(missing)
    _, measured, rows, focus = _run(landmarks)
    assert measured.availability_status.value != "AVAILABLE"
    assert measured.value is None
    assert TARGET not in focus
    for row in rows:
        assert row["availability_status"] != "AVAILABLE"
        assert row["value"] is None
        assert row["classification_authority"] is False


@pytest.mark.parametrize("automatic", [
    "R1_Ricketts", "R2_Ricketts", "R3_Ricketts", "R4_Ricketts", "Pm_Ricketts",
])
def test_unreviewed_auto_ramal_or_pm_landmark_cannot_promote(automatic):
    landmarks = _landmarks()
    item = landmarks[automatic]
    landmarks[automatic] = item.model_copy(update={
        "origin": LandmarkOrigin.SRPOSE38_AUTO,
        "model_id": "synthetic-p2", "model_sha256": "a" * 64,
        "pipeline_version": "synthetic-p2",
    })
    _, measured, rows, focus = _run(landmarks)
    assert measured.availability_status.value != "AVAILABLE"
    assert measured.value is None
    assert TARGET not in focus
    assert all(row["value"] is None for row in rows)


@pytest.mark.parametrize("different_image", ["R4_Ricketts", "Pm_Ricketts"])
def test_cross_image_source_never_produces_shared_measurement_or_focus(different_image):
    landmarks = _landmarks()
    landmarks[different_image] = landmarks[different_image].model_copy(
        update={"source_image_ref": "source:other-synthetic-image"}
    )
    _, measured, rows, focus = _run(landmarks)
    assert measured.availability_status.value != "AVAILABLE"
    assert measured.value is None
    assert TARGET not in focus
    assert all(row["value"] is None for row in rows)


def test_degenerate_anatomical_frankfort_refuses_xi_and_both_protocols():
    landmarks = _landmarks()
    landmarks["Or"] = landmarks["Or"].model_copy(update={"x": 0.0, "y": 0.0})
    xi, measured, rows, focus = _run(landmarks)
    assert xi.availability_status.value == "INVALID"
    assert measured.value is None
    assert TARGET not in focus
    assert all(row["availability_status"] != "AVAILABLE" for row in rows)


def test_generic_xi_pm_aliases_cannot_replace_manual_source_identities():
    landmarks = _landmarks()
    landmarks["Pm"] = landmarks.pop("Pm_Ricketts").model_copy(
        update={"landmark_id": "Pm", "evidence_id": "landmark:p2:Pm"}
    )
    _, measured, rows, focus = _run(landmarks)
    assert measured.value is None
    assert TARGET not in focus
    assert all(row["value"] is None for row in rows)
