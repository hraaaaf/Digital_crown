from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.services import cephalo_superimposition_api as api_service
from backend.tests.conftest import make_user
from backend.services.cephalo_superimposition_source import SuperimpositionSourceError


def test_f5_engineering_preview_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("DIGITAL_CROWN_F5_ENGINEERING_PREVIEW", raising=False)
    assert api_service.engineering_preview_enabled() is False


def test_f5_engineering_preview_requires_explicit_opt_in(monkeypatch):
    monkeypatch.setenv("DIGITAL_CROWN_F5_ENGINEERING_PREVIEW", "1")
    assert api_service.engineering_preview_enabled() is True


def test_canonical_path_rejects_non_static_source():
    with pytest.raises(SuperimpositionSourceError) as error:
        api_service._canonical_local_path("/tmp/patient.png")
    assert error.value.code == "SOURCE_PATH_UNSUPPORTED"


def test_canonical_path_rejects_other_static_media_family():
    with pytest.raises(SuperimpositionSourceError) as error:
        api_service._canonical_local_path("api/static/uploads/panoramic/patient.png")
    assert error.value.code == "SOURCE_PATH_UNSUPPORTED"


def test_canonical_path_rejects_path_traversal():
    with pytest.raises(SuperimpositionSourceError) as error:
        api_service._canonical_local_path("api/static/../../etc/passwd")
    assert error.value.code == "SOURCE_PATH_INVALID"


def test_canonical_path_resolves_only_existing_media(monkeypatch, tmp_path):
    static_root = tmp_path / "static"
    image = static_root / "uploads" / "radios" / "x.png"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"x")
    monkeypatch.setattr(api_service, "_STATIC_ROOT", static_root.resolve())

    resolved = api_service._canonical_local_path("api/static/uploads/radios/x.png")

    assert resolved == image.resolve()
    assert isinstance(resolved, Path)


def test_context_rejects_external_or_noncanonical_source_before_browser_use(monkeypatch):
    class Source:
        timepoint_id = 1
        timepoint_ordinal = 0
        occurred_at = None
        cephalo_analysis_id = 10
        image_original_path = "https://example.invalid/patient.png"
        is_calibrated = False
        mm_per_pixel = None

    class Pair:
        patient_id = 1
        ortho_case_id = 2
        from_source = Source()
        to_source = Source()
        quantitative_mm_allowed = False
        applicability_status = "ADULT_ENGINEERING_SCOPE_ONLY"

    monkeypatch.setattr(api_service, "resolve_superimposition_pair", lambda *args, **kwargs: Pair())

    with pytest.raises(SuperimpositionSourceError) as error:
        api_service.build_context(
            object(),
            patient_id=1,
            case_id=2,
            employer_id=3,
            from_timepoint_id=4,
            to_timepoint_id=5,
        )

    assert error.value.code == "SOURCE_PATH_UNSUPPORTED"


def test_f5_routes_require_cephalo_permission_not_general_patient_access(client, db, dentiste):
    employee = make_user(db, email="f5-patient-only@cabinet.ma", role="DENTISTE")
    employee.employer_id = dentiste.id
    employee.permissions = {"patients": True, "cephalo": False}
    db.commit()

    login = client.post(
        "/api/auth/login",
        data={"username": employee.email, "password": "TestPass123!"},
    )
    assert login.status_code == 200, login.text
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    context = client.get(
        "/api/patients/999/ortho-case/999/superimposition/context",
        params={"from_timepoint_id": 1, "to_timepoint_id": 2},
        headers=headers,
    )
    estimate = client.post(
        "/api/patients/999/ortho-case/999/superimposition/estimate",
        headers=headers,
        json={
            "from_timepoint_id": 1,
            "to_timepoint_id": 2,
            "reference_roi": {"x": 0, "y": 0, "width": 10, "height": 10},
            "moving_roi": {"x": 0, "y": 0, "width": 10, "height": 10},
        },
    )

    assert context.status_code == 403
    assert estimate.status_code == 403


def test_f5_http_schema_cannot_claim_clinical_validation():
    from backend.schemas.ortho_superimposition import OrthoSuperimpositionContextOut

    payload = {
        "patient_id": 1,
        "ortho_case_id": 2,
        "from_source": {
            "timepoint_id": 10,
            "timepoint_ordinal": 0,
            "occurred_at": "2026-01-01T10:00:00",
            "cephalo_analysis_id": 31,
            "is_calibrated": False,
            "mm_per_pixel": None,
        },
        "to_source": {
            "timepoint_id": 11,
            "timepoint_ordinal": 1,
            "occurred_at": "2026-06-01T10:00:00",
            "cephalo_analysis_id": 32,
            "is_calibrated": False,
            "mm_per_pixel": None,
        },
        "quantitative_mm_allowed": False,
        "applicability_status": "ADULT_ENGINEERING_SCOPE_ONLY",
        "acquisition_protocol_status": "UNVERIFIED",
        "method_id": "ACB_STRUCTURAL_FEATURE_SIMILARITY",
        "method_version": "1",
        "quality_status": "ENGINE_ESTIMATE_ONLY",
        "clinically_validated": True,
    }

    with pytest.raises(ValidationError):
        OrthoSuperimpositionContextOut.model_validate(payload)


def test_f5_http_schema_rejects_non_finite_registration_values():
    from backend.schemas.ortho_superimposition import OrthoSuperimpositionRegistrationOut

    payload = {
        "method_id": "ACB_STRUCTURAL_FEATURE_SIMILARITY",
        "method_version": "1",
        "quality_status": "ENGINE_ESTIMATE_ONLY",
        "clinically_validated": False,
        "transform_direction": "moving_to_reference",
        "matrix": [[float("nan"), 0.0, 0.0], [0.0, 1.0, 0.0]],
        "rotation_degrees": 0.0,
        "uniform_scale": 1.0,
        "translation_px": {"x": 0.0, "y": 0.0},
        "good_match_count": 2,
        "inlier_count": 2,
        "reference_roi": {"x": 0, "y": 0, "width": 10, "height": 10},
        "moving_roi": {"x": 0, "y": 0, "width": 10, "height": 10},
        "reference_size_px": {"width": 100, "height": 100},
        "moving_size_px": {"width": 100, "height": 100},
        "algorithm": {},
    }

    with pytest.raises(ValidationError):
        OrthoSuperimpositionRegistrationOut.model_validate(payload)


def test_f5_context_marks_acquisition_protocol_unverified(monkeypatch):
    class Source:
        timepoint_id = 1
        timepoint_ordinal = 0
        occurred_at = None
        cephalo_analysis_id = 10
        image_original_path = "api/static/uploads/radios/a.png"
        is_calibrated = False
        mm_per_pixel = None

    class Pair:
        patient_id = 1
        ortho_case_id = 2
        from_source = Source()
        to_source = Source()
        quantitative_mm_allowed = False
        applicability_status = "ADULT_ENGINEERING_SCOPE_ONLY"

    context = api_service.context_from_pair(Pair())
    assert context["acquisition_protocol_status"] == "UNVERIFIED"
    assert context["clinically_validated"] is False
