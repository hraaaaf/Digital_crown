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
