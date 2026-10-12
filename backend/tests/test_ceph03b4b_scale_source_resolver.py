"""Adversarial 03B.4b tests: heterogeneous commercial equipment sources.

No patient records, model inference, HTTP auth, or clinical accuracy claim.
A DICOM attribute dictionary is metadata *only*: its numbers never become
approved patient-plane millimetres through this resolver.
"""
from dataclasses import replace
import pytest

from backend.services.cephalo_auto_calibration_gate import ValidatedFiducialProfile
from backend.services.cephalo_calibration_candidate import CalibrationCandidate
from backend.services.cephalo_scale_source_resolver import (
    DicomScaleEvidence,
    ScaleSourceState,
    ScaleSourceReason,
    resolve_scale_sources,
    manual_calibration_required,
)


def _dicom(**overrides):
    values = {
        "pixel_spacing": "0.2\\0.2",
        "imager_pixel_spacing": "0.25\\0.25",
        "calibration_type": "FIDUCIAL",
        "calibration_description": "Known fiducial, near central ray at specified depth",
        "source_rows": 2048,
        "source_columns": 2048,
        "rendered_rows": 2048,
        "rendered_columns": 2048,
        "source_verified": True,
        "source_digest_sha256": "a" * 64,
    }
    values.update(overrides)
    return DicomScaleEvidence(**values)


def _ruler():
    return CalibrationCandidate.from_ticks(
        axis_x_px=80.0, tick_positions_y_px=[20., 45., 70., 95., 120., 145.]
    )


def _profile(**overrides):
    values = {
        "profile_id": "SERVER_TEST_PROFILE",
        "version": "2",
        "known_tick_spacing_mm": 5.0,
        "min_ticks": 5,
        "max_spacing_deviation_ratio": 0.05,
        "validation_reference": "unit-test://validated-physical-gauge-only",
    }
    values.update(overrides)
    return ValidatedFiducialProfile(**values)


def test_no_evidence_falls_back_without_scale():
    result = resolve_scale_sources()
    assert result.state is ScaleSourceState.NO_PHYSICAL_SOURCE
    assert result.reason is ScaleSourceReason.NO_EVIDENCE
    assert result.eligible_mm_per_pixel is None
    assert manual_calibration_required(result)
    assert result.to_payload()["applied_to_analysis"] is False


def test_jpeg_candidate_does_not_claim_mm_or_provider_specific_defaults():
    r = resolve_scale_sources(ruler=_ruler())
    assert r.state is ScaleSourceState.IMAGE_RULER_UNVERIFIED
    assert r.reason is ScaleSourceReason.RULER_WITHOUT_PROFILE
    assert r.to_payload()["eligible_mm_per_pixel"] is None
    assert r.to_payload()["profile_id"] is None
    assert manual_calibration_required(r)


@pytest.mark.parametrize("attrs,reason", [
    ({}, ScaleSourceReason.DICOM_PIXEL_SPACING_ABSENT),
    ({"PixelSpacing": "0.2\\0"}, ScaleSourceReason.DICOM_PIXEL_SPACING_INVALID),
    ({"PixelSpacing": "nan\\0.2"}, ScaleSourceReason.DICOM_PIXEL_SPACING_INVALID),
    ({"PixelSpacing": "inf\\0.2"}, ScaleSourceReason.DICOM_PIXEL_SPACING_INVALID),
    ({"PixelSpacing": "0.2"}, ScaleSourceReason.DICOM_PIXEL_SPACING_INVALID),
    ({"PixelSpacing": "-0.2\\0.2"}, ScaleSourceReason.DICOM_PIXEL_SPACING_INVALID),
    ({"ImagerPixelSpacing": "0.2\\0.2"}, ScaleSourceReason.DICOM_PIXEL_SPACING_ABSENT),
])
def test_dicom_tags_never_infer_verified_scale(attrs,reason):
    d=DicomScaleEvidence.from_dicom_attributes(attrs)
    result=resolve_scale_sources(dicom=d)
    assert result.state is ScaleSourceState.DICOM_REVIEW_REQUIRED
    assert result.reason is reason
    assert result.eligible_mm_per_pixel is None
    assert manual_calibration_required(result)


def test_valid_calibrated_dicom_still_requires_patient_plane_review():
    r=resolve_scale_sources(dicom=_dicom())
    assert r.state is ScaleSourceState.DICOM_REVIEW_REQUIRED
    assert r.reason is ScaleSourceReason.DICOM_CALIBRATION_UNATTESTED
    assert r.to_payload()["eligible_mm_per_pixel"] is None


@pytest.mark.parametrize("reason,overrides", [
    (ScaleSourceReason.DICOM_CALIBRATION_UNATTESTED,{"source_verified":False}),
    (ScaleSourceReason.DICOM_CALIBRATION_UNATTESTED,{"source_digest_sha256":"INVALID"}),
    (ScaleSourceReason.DICOM_CALIBRATION_UNATTESTED,{"calibration_type":None}),
    (ScaleSourceReason.DICOM_CALIBRATION_UNATTESTED,{"calibration_type":"UNKNOWN"}),
    (ScaleSourceReason.DICOM_DESCRIPTION_MISSING,{"calibration_description":None}),
    (ScaleSourceReason.DICOM_PIXEL_GRID_UNATTESTED,{"rendered_columns":1024}),
    (ScaleSourceReason.DICOM_PIXEL_GRID_UNATTESTED,{"source_rows":None}),
    (ScaleSourceReason.DICOM_ANISOTROPIC_SPACING,{"pixel_spacing":"0.2\\0.3"}),
    (ScaleSourceReason.DICOM_PIXEL_SPACING_INVALID,{"pixel_spacing":["0.2","0"]}),
])
def test_invalid_dicom_sources_are_not_accepted(overrides,reason):
    r=resolve_scale_sources(dicom=_dicom(**overrides))
    assert r.reason is reason
    assert r.eligible_mm_per_pixel is None


def test_dicom_keywords_and_tags_extract_same_values():
    keywords={"PixelSpacing":"0.2\\0.2","PixelSpacingCalibrationType":"FIDUCIAL",
              "Rows":1200,"Columns":1400}
    tags={"0028,0030":"0.2\\0.2","0028,0A02":"FIDUCIAL",
          "0028,0010":1200,"0028,0011":1400}
    a=DicomScaleEvidence.from_dicom_attributes(keywords)
    b=DicomScaleEvidence.from_dicom_attributes(tags)
    assert a.pixel_spacing == b.pixel_spacing
    assert a.calibration_type == b.calibration_type
    assert a.source_rows==b.source_rows==1200
    assert a.source_columns==b.source_columns==1400


@pytest.mark.parametrize("kind",["FIDUCIAL","GEOMETRY"])
def test_both_dicom_calibration_types_require_independent_review(kind):
    r=resolve_scale_sources(dicom=_dicom(calibration_type=kind))
    assert r.state is ScaleSourceState.DICOM_REVIEW_REQUIRED
    assert r.eligible_mm_per_pixel is None


def test_strict_registry_owned_profile_gate_can_create_only_nonapplied_preview():
    r=resolve_scale_sources(ruler=_ruler(),server_validated_profile=_profile())
    assert r.state is ScaleSourceState.FIDUCIAL_GATE_READY
    assert r.reason is ScaleSourceReason.SERVER_PROFILE_GATE_PASSED
    assert r.eligible_mm_per_pixel == pytest.approx(0.2)
    assert r.to_payload()["applied_to_analysis"] is False
    assert r.to_payload()["requires_server_promotion"] is True
    assert not manual_calibration_required(r)


def test_invalid_candidate_spacing_refuses_even_if_physical_profile_exists():
    c=CalibrationCandidate.from_ticks(axis_x_px=80,tick_positions_y_px=[20,45,70,98,123,148])
    r=resolve_scale_sources(ruler=c,server_validated_profile=_profile())
    assert r.state is ScaleSourceState.IMAGE_RULER_UNVERIFIED
    assert r.reason is ScaleSourceReason.SERVER_PROFILE_GATE_FAILED
    assert r.eligible_mm_per_pixel is None


def test_sources_disagree_and_fail_closed():
    r=resolve_scale_sources(
        dicom=_dicom(pixel_spacing="0.3\\0.3"),
        ruler=_ruler(),server_validated_profile=_profile(),
    )
    assert r.state is ScaleSourceState.SOURCE_CONFLICT
    assert r.reason is ScaleSourceReason.SOURCES_DISAGREE
    assert r.eligible_mm_per_pixel is None
    assert manual_calibration_required(r)


def test_subpercent_dicom_fiducial_disagreement_is_still_blocked():
    # 0.1% is small, but no validated physical agreement tolerance exists yet.
    r=resolve_scale_sources(
        dicom=_dicom(pixel_spacing="0.2002\\\\0.2002"),
        ruler=_ruler(),server_validated_profile=_profile(),
    )
    assert r.state is ScaleSourceState.SOURCE_CONFLICT
    assert r.eligible_mm_per_pixel is None


def test_same_image_metadata_and_profile_no_patient_scale_applied():
    r=resolve_scale_sources(
        dicom=_dicom(pixel_spacing="0.2\\0.2"),
        ruler=_ruler(),server_validated_profile=_profile(),
    )
    assert r.state is ScaleSourceState.FIDUCIAL_GATE_READY
    assert r.to_payload()["applied_to_analysis"] is False


def test_profile_alone_is_not_evidence_and_image_only_never_promoted():
    r=resolve_scale_sources(server_validated_profile=_profile())
    assert r.state is ScaleSourceState.NO_PHYSICAL_SOURCE
    assert r.eligible_mm_per_pixel is None


def test_result_does_not_expose_dicom_description_or_hash():
    meta=_dicom(calibration_description="SENSITIVE-FREEFORM-DO-NOT-EXPOSE")
    result=resolve_scale_sources(dicom=meta)
    rendered=str(result.to_payload())
    assert "SENSITIVE-FREEFORM" not in rendered
    assert "a"*64 not in rendered


def test_manufacturer_free_matrix_and_no_per_cabinet_overrides():
    source=DicomScaleEvidence.from_dicom_attributes(
        {"0028,0030":[0.16,0.16],"0028,0A02":"GEOMETRY"},
        rendered_rows=1500,rendered_columns=2048,source_verified=True,
    )
    assert resolve_scale_sources(dicom=source).eligible_mm_per_pixel is None
