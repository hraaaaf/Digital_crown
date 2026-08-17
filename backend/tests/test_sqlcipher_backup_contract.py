from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from cryptography.fernet import Fernet

from backend.services.backup_service import BackupService


def _fake_sqlcipher_engine(db_path: Path, password: str = "cabinet-test-key"):
    return SimpleNamespace(
        dialect=SimpleNamespace(name="sqlite"),
        driver="pysqlcipher",
        url=SimpleNamespace(database=str(db_path), password=password),
    )


def test_on_disk_sqlcipher_routes_to_export_then_encryption(tmp_path):
    source = tmp_path / "cabinet.db"
    source.write_bytes(b"encrypted-source-placeholder")
    fake_engine = _fake_sqlcipher_engine(source)
    cipher = Fernet(Fernet.generate_key())

    def fake_export(source_db, snapshot_db, passphrase):
        assert source_db == source
        assert passphrase == "cabinet-test-key"
        snapshot_db.write_bytes(b"coherent-sqlcipher-snapshot")

    with patch("backend.database.engine", fake_engine), \
         patch.object(BackupService, "_get_or_create_key", return_value=cipher), \
         patch.object(BackupService, "_export_sqlcipher_snapshot", side_effect=fake_export) as export:
        result = BackupService._backup_sqlite_family(tmp_path, "20260817_020000", "pysqlcipher")

    export.assert_called_once()
    assert result["status"] == "SUCCESS"
    output = tmp_path / result["backup_filename"]
    assert output.exists()
    assert cipher.decrypt(output.read_bytes()) == b"coherent-sqlcipher-snapshot"
    assert not list(tmp_path.glob(".tmp_*sqlcipher_snapshot.db"))


def test_sqlcipher_backup_fails_closed_when_key_missing(tmp_path, monkeypatch):
    source = tmp_path / "cabinet.db"
    source.write_bytes(b"encrypted-source-placeholder")
    fake_engine = _fake_sqlcipher_engine(source, password=None)
    monkeypatch.delenv("CABINET_MASTER_KEY_HEX", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with patch("backend.database.engine", fake_engine), \
         patch.object(BackupService, "_get_or_create_key", return_value=Fernet(Fernet.generate_key())):
        result = BackupService._backup_sqlite_family(tmp_path, "20260817_020001", "pysqlcipher")

    assert result["status"] == "FAILED"
    assert result["error_code"] == "MISSING_SQLCIPHER_KEY"
    assert result["backup_filename"] is None


def test_restore_verifies_before_atomic_publish(tmp_path):
    cipher = Fernet(Fernet.generate_key())
    encrypted = tmp_path / "backup.db.enc"
    encrypted.write_bytes(cipher.encrypt(b"sqlcipher-snapshot"))
    restored = tmp_path / "restored.db"

    with patch.object(BackupService, "_get_or_create_key", return_value=cipher), \
         patch.object(BackupService, "_verify_sqlcipher_file") as verify:
        BackupService.restore_backup(
            encrypted,
            restored,
            verify_sqlcipher=True,
            passphrase="cabinet-test-key",
        )

    verify.assert_called_once()
    assert restored.read_bytes() == b"sqlcipher-snapshot"
    assert not list(tmp_path.glob(".tmp_*restored.db"))
