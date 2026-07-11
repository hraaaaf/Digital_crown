from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from backend.core import media_paths


def test_get_media_root_prefers_media_root_env(monkeypatch, tmp_path):
    media_dir = tmp_path / "custom_media"
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("MEDIA_ROOT", str(media_dir))

    assert media_paths.get_media_root() == media_dir.resolve(strict=False)


def test_rehearsal_requires_media_root(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "e2e_install_rehearsal")
    monkeypatch.delenv("MEDIA_ROOT", raising=False)

    with pytest.raises(RuntimeError, match="Unsafe MEDIA_ROOT for rehearsal"):
        media_paths.get_media_root()


def test_rehearsal_rejects_real_media_root(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "e2e_install_rehearsal")
    monkeypatch.setenv("MEDIA_ROOT", str(media_paths.get_real_media_root()))

    with pytest.raises(RuntimeError, match="Unsafe MEDIA_ROOT for rehearsal"):
        media_paths.get_media_root()


def test_archive_service_uses_rehearsal_media_root(monkeypatch, tmp_path):
    rehearsal_media = tmp_path / "install_rehearsal_media"
    monkeypatch.setenv("ENVIRONMENT", "e2e_install_rehearsal")
    monkeypatch.setenv("MEDIA_ROOT", str(rehearsal_media))

    import backend.services.archive_service as archive_service

    reloaded = importlib.reload(archive_service)
    assert reloaded.MEDIA_DIR == rehearsal_media.resolve(strict=False)
    assert str(reloaded.ARCHIVE_BASE_DIR).startswith(str(rehearsal_media.resolve(strict=False)))


def test_backup_media_dry_run_uses_rehearsal_media_root(monkeypatch, tmp_path, caplog):
    rehearsal_media = tmp_path / "install_rehearsal_media"
    rehearsal_media.mkdir()
    (rehearsal_media / "sample.txt").write_text("ok", encoding="utf-8")
    monkeypatch.setenv("ENVIRONMENT", "e2e_install_rehearsal")
    monkeypatch.setenv("MEDIA_ROOT", str(rehearsal_media))
    caplog.set_level("INFO")

    import backend.scripts.backup_media as backup_media

    backup_media.backup_media(dry_run=True)
    assert f"Source media dir: {rehearsal_media.resolve(strict=False)}" in caplog.text
    assert "Dry-run" in caplog.text


def test_backup_db_rehearsal_refuses_digitalcrown_db(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "e2e_install_rehearsal")

    import backend.scripts.backup_db as backup_db

    with pytest.raises(RuntimeError, match="Unsafe DATABASE_URL for rehearsal"):
        backup_db._validate_rehearsal_database(
            "postgresql://postgres:secret@localhost/digitalcrown_db?client_encoding=utf8"
        )


def test_backup_db_dry_run_logs_masked_target(monkeypatch, caplog):
    monkeypatch.setenv("ENVIRONMENT", "e2e_install_rehearsal")
    caplog.set_level("INFO")

    # backup_db.py no longer imports `settings` at module level (AUTO-BACKUP-POSTGRES-
    # ROUTING-FIX-1: an eager `settings`/env-loading import made it unsafe to import
    # backup_db.py as a library from the live server process). `settings` is now
    # imported lazily inside backup_db(), but it's still the same singleton object
    # from backend.config — mutating it there has the same effect.
    from backend.config import settings
    import backend.scripts.backup_db as backup_db

    original_url = settings.DATABASE_URL
    settings.DATABASE_URL = (
        "postgresql://digitalcrown_e2e_user:secret@localhost:5432/"
        "digitalcrown_e2e_install_rehearsal"
    )
    try:
        backup_db.backup_db(dry_run=True)
    finally:
        settings.DATABASE_URL = original_url

    assert "Target database: postgresql://digitalcrown_e2e_user:***@localhost:5432/digitalcrown_e2e_install_rehearsal" in caplog.text
    assert "Dry-run PostgreSQL target: db=digitalcrown_e2e_install_rehearsal host=localhost port=5432 user=digitalcrown_e2e_user" in caplog.text


def test_run_rehearsal_backend_script_contains_safety_guards():
    script = Path("backend/scripts/run_rehearsal_backend.ps1").read_text(encoding="utf-8")

    assert "digitalcrown_db" in script
    assert "MEDIA_ROOT missing" in script
    assert "unsafe folder for rehearsal" in script
    assert "PORT=8005 forbidden for rehearsal" in script
    assert "ENVIRONMENT=e2e_install_rehearsal" in script
