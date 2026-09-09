import errno
import hashlib
import json
from pathlib import Path

import pytest

from backend.core.paths import AppPaths
from backend.services import disaster_recovery_service as dr_mod
from backend.services.backup_service import BackupService
from backend.services.cabinet_bundle import CabinetBundleService
from backend.services.disaster_recovery_service import (
    BUNDLE_PREFIX,
    DR_DESTINATION_ENV,
    DR_KEEP_ENV,
    DR_SECRET_ENV,
    DisasterRecoveryService,
)


def _patch_appdata(monkeypatch, path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(AppPaths, "get_user_data_dir", staticmethod(lambda: path))
    return path


def _configure(monkeypatch, destination: Path, *, keep: int = 2):
    monkeypatch.setenv(DR_DESTINATION_ENV, str(destination))
    monkeypatch.setenv(DR_SECRET_ENV, "correct-horse-battery-staple")
    monkeypatch.setenv(DR_KEEP_ENV, str(keep))


def _fake_export(monkeypatch):
    def create(target: Path, secret: str):
        assert secret == "correct-horse-battery-staple"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"portable-cabinet")
        return {
            "path": target,
            "filename": target.name,
            "size_bytes": target.stat().st_size,
            "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            "media_file_count": 3,
            "source_os": "windows",
            "source_architecture": "amd64",
        }

    def verify(bundle: Path, secret: str, target_archive: Path, *, active_engine=None):
        assert bundle.read_bytes() == b"portable-cabinet"
        assert secret == "correct-horse-battery-staple"
        assert active_engine == ("sqlite", "pysqlite")
        target_archive.parent.mkdir(parents=True, exist_ok=True)
        target_archive.write_bytes(b"guided-restore")
        return {"path": target_archive, "media_file_count": 3}

    monkeypatch.setattr(CabinetBundleService, "create_bundle", staticmethod(create))
    monkeypatch.setattr(CabinetBundleService, "to_local_guided_restore_archive", staticmethod(verify))
    monkeypatch.setattr(BackupService, "_detect_engine", staticmethod(lambda: ("sqlite", "pysqlite")))


def test_missing_configuration_is_explicit_and_non_destructive(tmp_path, monkeypatch):
    appdata = _patch_appdata(monkeypatch, tmp_path / "appdata")
    monkeypatch.delenv(DR_DESTINATION_ENV, raising=False)
    monkeypatch.delenv(DR_SECRET_ENV, raising=False)

    result = DisasterRecoveryService.create_verified_snapshot()

    assert result["status"] == "CONFIGURATION_REQUIRED"
    assert result["destination_configured"] is False
    persisted = json.loads((appdata / "backups" / "last_dr_status.json").read_text())
    assert persisted["error_code"] == "DR_CONFIGURATION_REQUIRED"
    assert DisasterRecoveryService.run_scheduled_snapshot() is True


def test_destination_inside_appdata_is_refused_without_creating_destination(tmp_path, monkeypatch):
    appdata = _patch_appdata(monkeypatch, tmp_path / "appdata")
    destination = appdata / "dr"
    _configure(monkeypatch, destination)

    result = DisasterRecoveryService.create_verified_snapshot()

    assert result["status"] == "FAILED"
    assert result["error_code"] == "DR_CONFIGURATION_INVALID"
    assert not destination.exists()


def test_relative_destination_is_refused(tmp_path, monkeypatch):
    appdata = _patch_appdata(monkeypatch, tmp_path / "appdata")
    monkeypatch.setenv(DR_DESTINATION_ENV, "relative/dr")
    monkeypatch.setenv(DR_SECRET_ENV, "correct-horse-battery-staple")

    result = DisasterRecoveryService.create_verified_snapshot()

    assert result["status"] == "FAILED"
    assert result["error_code"] == "DR_CONFIGURATION_INVALID"
    persisted = json.loads((appdata / "backups" / "last_dr_status.json").read_text())
    assert persisted["error_code"] == "DR_CONFIGURATION_INVALID"


def test_unavailable_destination_is_reported_fail_closed(tmp_path, monkeypatch):
    _patch_appdata(monkeypatch, tmp_path / "appdata")
    destination = tmp_path / "external"
    _configure(monkeypatch, destination)

    class BrokenAdapter:
        def ensure_private_directory(self, path):
            raise OSError("offline mount")

        def atomic_write_text(self, path, content):
            raise OSError("status path unavailable")

    monkeypatch.setattr(dr_mod, "get_platform_adapter", lambda: BrokenAdapter())

    result = DisasterRecoveryService.create_verified_snapshot()

    assert result["status"] == "FAILED"
    assert result["error_code"] == "DR_DESTINATION_UNAVAILABLE"
    assert result["verified_restore_path"] is False


def test_verified_snapshot_roundtrip_sidecar_and_retention(tmp_path, monkeypatch):
    appdata = _patch_appdata(monkeypatch, tmp_path / "appdata")
    destination = tmp_path / "external"
    destination.mkdir()
    _configure(monkeypatch, destination, keep=2)
    _fake_export(monkeypatch)

    # Unverified/orphan-looking historical files must never evict a verified generation.
    # They stay outside the retention count and are left untouched for manual inspection.
    old_files = []
    for index in range(3):
        old = destination / f"{BUNDLE_PREFIX}2026010{index}T000000Z-old{index}.dcbundle"
        old.write_bytes(f"old-{index}".encode())
        old.with_name(old.name + ".sha256").write_text("old\n", encoding="utf-8")
        old.touch()
        old_files.append(old)

    result = DisasterRecoveryService.create_verified_snapshot()

    assert result["status"] == "SUCCESS"
    assert result["verified_restore_path"] is True
    current = destination / result["bundle_filename"]
    assert current.exists()
    expected_sha = hashlib.sha256(current.read_bytes()).hexdigest()
    assert result["sha256"] == expected_sha
    sidecar = current.with_name(current.name + ".sha256")
    assert sidecar.read_text(encoding="utf-8") == f"{expected_sha}  {current.name}\n"
    assert result["checksum_sidecar"] == sidecar.name

    verified = [
        bundle
        for bundle in destination.glob(f"{BUNDLE_PREFIX}*.dcbundle")
        if DisasterRecoveryService._is_verified_pair(bundle)
    ]
    assert len(verified) == 1
    assert verified == [current]
    assert all(path.exists() for path in old_files)
    assert result["retention_removed"] == []

    persisted = json.loads((appdata / "backups" / "last_dr_status.json").read_text())
    serialized = json.dumps(persisted)
    assert "correct-horse-battery-staple" not in serialized
    assert persisted["status"] == "SUCCESS"


def test_verification_failure_deletes_untrusted_bundle_and_sidecar(tmp_path, monkeypatch):
    _patch_appdata(monkeypatch, tmp_path / "appdata")
    destination = tmp_path / "external"
    destination.mkdir()
    _configure(monkeypatch, destination)
    _fake_export(monkeypatch)

    def fail_verify(*args, **kwargs):
        raise ValueError("tampered")

    monkeypatch.setattr(CabinetBundleService, "to_local_guided_restore_archive", staticmethod(fail_verify))
    result = DisasterRecoveryService.create_verified_snapshot()

    assert result["status"] == "FAILED"
    assert result["verified_restore_path"] is False
    assert list(destination.glob(f"{BUNDLE_PREFIX}*.dcbundle")) == []
    assert list(destination.glob("*.sha256")) == []


def test_disk_full_is_classified_and_partial_bundle_removed(tmp_path, monkeypatch):
    _patch_appdata(monkeypatch, tmp_path / "appdata")
    destination = tmp_path / "external"
    destination.mkdir()
    _configure(monkeypatch, destination)
    monkeypatch.setattr(BackupService, "_detect_engine", staticmethod(lambda: ("sqlite", "pysqlite")))

    def disk_full(target: Path, secret: str):
        target.write_bytes(b"partial")
        raise OSError(errno.ENOSPC, "No space left on device")

    monkeypatch.setattr(CabinetBundleService, "create_bundle", staticmethod(disk_full))

    result = DisasterRecoveryService.create_verified_snapshot()

    assert result["status"] == "FAILED"
    assert result["error_code"] == "DR_DISK_FULL"
    assert list(destination.glob(f"{BUNDLE_PREFIX}*.dcbundle")) == []
    assert list(destination.glob("*.partial")) == []


def test_postgres_portable_dr_is_explicitly_unsupported(tmp_path, monkeypatch):
    _patch_appdata(monkeypatch, tmp_path / "appdata")
    destination = tmp_path / "external"
    destination.mkdir()
    _configure(monkeypatch, destination)
    monkeypatch.setattr(BackupService, "_detect_engine", staticmethod(lambda: ("postgresql", "psycopg2")))

    result = DisasterRecoveryService.create_verified_snapshot()

    assert result["status"] == "FAILED"
    assert result["error_code"] == "DR_PORTABLE_ENGINE_UNSUPPORTED"
    assert list(destination.glob(f"{BUNDLE_PREFIX}*.dcbundle")) == []


@pytest.mark.parametrize("raw", ["0", "91", "abc"])
def test_retention_bounds_are_fail_closed(tmp_path, monkeypatch, raw):
    destination = tmp_path / "external"
    destination.mkdir()
    _patch_appdata(monkeypatch, tmp_path / "appdata")
    monkeypatch.setenv(DR_DESTINATION_ENV, str(destination))
    monkeypatch.setenv(DR_SECRET_ENV, "correct-horse-battery-staple")
    monkeypatch.setenv(DR_KEEP_ENV, raw)

    result = DisasterRecoveryService.create_verified_snapshot()

    assert result["status"] == "FAILED"
    assert result["error_code"] == "DR_CONFIGURATION_INVALID"
