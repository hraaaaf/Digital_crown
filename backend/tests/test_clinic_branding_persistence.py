from pathlib import Path

from backend.routers.clinics import _clinic_asset_dir
from scripts.migrate_legacy_clinic_branding import migrate


def _persistent_media(monkeypatch, tmp_path: Path) -> Path:
    user_data = tmp_path / "user-data"
    monkeypatch.setenv("DIGITALCROWN_USER_DATA_DIR", str(user_data))
    monkeypatch.delenv("MEDIA_ROOT", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "cabinet")
    return user_data / "media"


def test_clinic_branding_directory_is_release_independent(monkeypatch, tmp_path):
    media_root = _persistent_media(monkeypatch, tmp_path)

    path = _clinic_asset_dir("clinic-public-id")

    assert path == media_root / "clinics" / "clinic-public-id"
    assert path.is_dir()
    assert "backend" not in str(path).lower()
    assert "releases" not in str(path).lower()


def test_legacy_branding_migration_copies_once_and_never_overwrites(monkeypatch, tmp_path):
    media_root = _persistent_media(monkeypatch, tmp_path)
    source_root = tmp_path / "legacy" / "clinics"
    source = source_root / "clinic-a" / "logo.png"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"legacy-logo")

    assert migrate(source_root) == (1, 0, 0)
    destination = media_root / "clinics" / "clinic-a" / "logo.png"
    assert destination.read_bytes() == b"legacy-logo"

    assert migrate(source_root) == (0, 1, 0)

    source.write_bytes(b"different-new-content")
    assert migrate(source_root) == (0, 0, 1)
    assert destination.read_bytes() == b"legacy-logo"
