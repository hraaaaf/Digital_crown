from pathlib import Path

import pytest

from backend.services import cephalo_superimposition_api as api_service
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
