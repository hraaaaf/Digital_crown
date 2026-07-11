"""Tests for BackupService — aligned with the current API."""
import pytest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
from cryptography.fernet import Fernet

from backend.services.backup_service import BackupService


def _fake_engine(dialect_name: str, driver: str, db_path: str | None = None):
    """Stand-in for backend.database.engine — dialect.name/driver/url.database only."""
    return SimpleNamespace(
        dialect=SimpleNamespace(name=dialect_name),
        driver=driver,
        url=SimpleNamespace(database=db_path),
    )


def test_get_or_create_key_creates_file(tmp_path):
    """First call generates and persists a key file; returns a Fernet instance."""
    with patch("backend.services.backup_service.AppPaths.get_user_data_dir", return_value=tmp_path):
        cipher = BackupService._get_or_create_key()
        key_path = tmp_path / "backup.key"
        assert key_path.exists()
        assert isinstance(cipher, Fernet)


def test_get_or_create_key_reuses_existing_key(tmp_path):
    """Subsequent calls load the same key (no new file generated)."""
    with patch("backend.services.backup_service.AppPaths.get_user_data_dir", return_value=tmp_path):
        cipher1 = BackupService._get_or_create_key()
        key1 = (tmp_path / "backup.key").read_bytes()

        cipher2 = BackupService._get_or_create_key()
        key2 = (tmp_path / "backup.key").read_bytes()

        assert key1 == key2


def _make_sqlite_db(path: Path) -> None:
    """Create a minimal valid SQLite database at *path*."""
    import sqlite3
    conn = sqlite3.connect(str(path))
    conn.execute("CREATE TABLE records (id INTEGER PRIMARY KEY, name TEXT)")
    conn.execute("INSERT INTO records VALUES (1, 'test')")
    conn.commit()
    conn.close()


def test_encrypt_and_save_produces_different_bytes(tmp_path):
    """Encrypted file must differ from the plaintext source."""
    source = tmp_path / "clinical_vault.db"
    _make_sqlite_db(source)
    target = tmp_path / "backup.enc"

    cipher = Fernet(Fernet.generate_key())
    BackupService._encrypt_and_save(source, target, cipher)

    assert target.exists()
    assert target.read_bytes() != source.read_bytes()


def test_restore_backup_roundtrip(tmp_path):
    """Encrypt then restore must preserve database content."""
    import sqlite3

    source = tmp_path / "clinical_vault.db"
    _make_sqlite_db(source)

    enc_file = tmp_path / "backup.enc"
    restored = tmp_path / "restored.db"

    cipher = Fernet(Fernet.generate_key())
    BackupService._encrypt_and_save(source, enc_file, cipher)

    # Stub _get_or_create_key so restore uses the same cipher
    with patch.object(BackupService, "_get_or_create_key", return_value=cipher):
        BackupService.restore_backup(enc_file, restored)

    # sqlite3.backup() may change internal header counters, so verify content not raw bytes
    conn = sqlite3.connect(str(restored))
    rows = conn.execute("SELECT id, name FROM records").fetchall()
    conn.close()
    assert rows == [(1, "test")]


def test_restore_backup_missing_file_raises(tmp_path):
    """restore_backup must raise FileNotFoundError for a non-existent enc file."""
    with pytest.raises(FileNotFoundError):
        BackupService.restore_backup(tmp_path / "ghost.enc", tmp_path / "out.db")


def test_cleanup_old_backups_keeps_n_most_recent(tmp_path):
    """_cleanup_old_backups must delete files beyond the keep limit."""
    backups_dir = tmp_path / "backups"
    backups_dir.mkdir()
    prefix = "clinical_vault_backup_"

    # Create 10 fake backup files with distinct mtimes
    files = []
    for i in range(10):
        f = backups_dir / f"{prefix}2026010{i:01d}_120000.enc"
        f.write_bytes(b"x")
        files.append(f)

    BackupService._cleanup_old_backups(backups_dir, prefix=prefix, keep=7)

    remaining = list(backups_dir.glob(f"{prefix}*.enc"))
    assert len(remaining) == 7


def test_run_daily_backup_true_when_postgres_backup_succeeds(tmp_path):
    """run_daily_backup delegates to backup_active_database and returns True on SUCCESS."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    fake_result = {"status": "SUCCESS", "engine": "postgresql", "backup_filename": "db_backup_x.sql.enc"}

    with patch("backend.services.backup_service.AppPaths.get_user_data_dir", return_value=data_dir), \
         patch.object(BackupService, "backup_active_database", return_value=fake_result):
        result = BackupService.run_daily_backup()

    assert result is True


def test_run_daily_backup_false_when_sqlcipher_skipped(tmp_path):
    """run_daily_backup returns False (not True) when the engine is unsupported —
    the old behavior of always returning True regardless of outcome masked real
    failures and is exactly the bug this mission fixes."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    fake_result = {
        "status": "SKIPPED_UNSUPPORTED_ENGINE", "engine": "sqlite",
        "error_message": "SQLCipher automatic backup unsupported",
    }

    with patch("backend.services.backup_service.AppPaths.get_user_data_dir", return_value=data_dir), \
         patch.object(BackupService, "backup_active_database", return_value=fake_result):
        result = BackupService.run_daily_backup()

    assert result is False


class TestEngineDetection:
    def test_detect_engine_reads_dialect_and_driver(self):
        fake = _fake_engine("postgresql", "psycopg2")
        with patch("backend.database.engine", fake):
            dialect_name, driver = BackupService._detect_engine()
        assert dialect_name == "postgresql"
        assert driver == "psycopg2"


class TestBackupActiveDatabaseRouting:
    def test_postgresql_engine_routes_to_postgres_backup(self, tmp_path):
        """DATABASE_URL PostgreSQL selects pg_dump — never sqlite3, never clinical_vault.db."""
        fake = _fake_engine("postgresql", "psycopg2")
        with patch("backend.database.engine", fake), \
             patch("backend.services.backup_service.AppPaths.get_user_data_dir", return_value=tmp_path), \
             patch.object(BackupService, "_backup_postgres", return_value={
                 "engine": "postgresql", "status": "SUCCESS", "backup_filename": "x",
                 "size_bytes": 10, "checksum": "abc",
             }) as mock_pg, \
             patch.object(BackupService, "_backup_sqlite_family") as mock_sqlite:
            result = BackupService.backup_active_database()

        mock_pg.assert_called_once()
        mock_sqlite.assert_not_called()
        assert result["status"] == "SUCCESS"

    def test_unknown_engine_fails_explicitly(self, tmp_path):
        """A DB engine that is neither postgresql nor sqlite must never be presented
        as a valid backup — explicit SKIPPED_UNSUPPORTED_ENGINE status."""
        fake = _fake_engine("oracle", "cx_oracle")
        with patch("backend.database.engine", fake), \
             patch("backend.services.backup_service.AppPaths.get_user_data_dir", return_value=tmp_path):
            result = BackupService.backup_active_database()

        assert result["status"] == "SKIPPED_UNSUPPORTED_ENGINE"
        assert result["backup_filename"] is None

    def test_engine_detection_failure_fails_explicitly(self, tmp_path):
        """If the engine can't even be introspected, never fabricate a fake success."""
        with patch("backend.services.backup_service.BackupService._detect_engine", side_effect=RuntimeError("boom")), \
             patch("backend.services.backup_service.AppPaths.get_user_data_dir", return_value=tmp_path):
            result = BackupService.backup_active_database()

        assert result["status"] == "SKIPPED_UNSUPPORTED_ENGINE"
        assert result["error_code"] == "ENGINE_DETECTION_FAILED"


class TestSqliteFamilyBranch:
    def test_pysqlcipher_driver_skips_cleanly_no_exception(self, tmp_path):
        """SQLCipher (Option B): explicit unsupported status, never crashes the scheduler."""
        result = BackupService._backup_sqlite_family(tmp_path, "20260101_000000", driver="pysqlcipher")
        assert result["status"] == "SKIPPED_UNSUPPORTED_ENGINE"
        assert result["error_message"] == "SQLCipher automatic backup unsupported"

    def test_plain_sqlite_backs_up_the_actual_engine_file(self, tmp_path):
        """Legitimate plaintext SQLite: backs up the file the live engine is actually
        connected to (not a separately hardcoded path)."""
        db_file = tmp_path / "real_engine_target.db"
        _make_sqlite_db(db_file)
        fake = _fake_engine("sqlite", "pysqlite", db_path=str(db_file))

        with patch("backend.database.engine", fake), \
             patch("backend.services.backup_service.AppPaths.get_user_data_dir", return_value=tmp_path):
            result = BackupService._backup_sqlite_family(tmp_path, "20260101_000000", driver="pysqlite")

        assert result["status"] == "SUCCESS"
        assert (tmp_path / result["backup_filename"]).exists()

    def test_in_memory_sqlite_skips_cleanly(self, tmp_path):
        fake = _fake_engine("sqlite", "pysqlite", db_path=":memory:")
        with patch("backend.database.engine", fake):
            result = BackupService._backup_sqlite_family(tmp_path, "20260101_000000", driver="pysqlite")
        assert result["status"] == "SKIPPED_UNSUPPORTED_ENGINE"
        assert result["error_code"] == "IN_MEMORY_DB"


class TestPostgresBackup:
    def _patch_common(self, tmp_path, db_url="postgresql://u:p@localhost/testdb"):
        fake_settings = SimpleNamespace(DATABASE_URL=db_url)
        return patch("backend.config.settings", fake_settings)

    def test_pg_dump_failure_returns_failed_no_file(self, tmp_path):
        """pg_dump non-zero exit code -> FAILED, no backup file presented as valid."""
        fake_process = MagicMock(returncode=1, stdout=b"", stderr=b"connection refused")
        with self._patch_common(tmp_path), \
             patch("backend.scripts.backup_db.find_pg_binary", return_value="pg_dump"), \
             patch("backend.services.backup_service.subprocess.run", return_value=fake_process):
            result = BackupService._backup_postgres(tmp_path, "20260101_000000")

        assert result["status"] == "FAILED"
        assert result["error_code"] == "PG_DUMP_FAILED"
        assert list(tmp_path.glob("*.enc")) == []

    def test_empty_dump_refused_before_encryption(self, tmp_path):
        """pg_dump succeeds (code 0) but produces empty stdout -> refused."""
        fake_process = MagicMock(returncode=0, stdout=b"", stderr=b"")
        with self._patch_common(tmp_path), \
             patch("backend.scripts.backup_db.find_pg_binary", return_value="pg_dump"), \
             patch("backend.services.backup_service.subprocess.run", return_value=fake_process):
            result = BackupService._backup_postgres(tmp_path, "20260101_000000")

        assert result["status"] == "FAILED"
        assert result["error_code"] == "EMPTY_DUMP"

    def test_encryption_failure_cleans_up_scoped_temp_only(self, tmp_path):
        """A pre-existing unrelated temp file must survive; only this operation's own
        temp file is ever touched."""
        unrelated_temp = tmp_path / ".tmp_unrelated_leftover.sql.enc"
        unrelated_temp.write_bytes(b"do-not-touch")
        fake_process = MagicMock(returncode=0, stdout=b"-- fake pg_dump output --", stderr=b"")

        with self._patch_common(tmp_path), \
             patch("backend.scripts.backup_db.find_pg_binary", return_value="pg_dump"), \
             patch("backend.services.backup_service.subprocess.run", return_value=fake_process), \
             patch("backend.scripts.backup_db.get_cipher", side_effect=RuntimeError("bad key")):
            result = BackupService._backup_postgres(tmp_path, "20260101_000000")

        assert result["status"] == "FAILED"
        assert result["error_code"] == "ENCRYPTION_FAILED"
        assert unrelated_temp.exists()  # untouched
        assert list(tmp_path.glob(".tmp_*db_backup*")) == []  # this op's own temp cleaned up

    def test_missing_master_key_fails_cleanly_not_sys_exit(self, tmp_path):
        """get_cipher()'s sys.exit(1) (fine for CLI) must never propagate out of this
        server-side call and kill the scheduler thread."""
        fake_process = MagicMock(returncode=0, stdout=b"-- fake pg_dump output --", stderr=b"")

        def _raise_system_exit():
            raise SystemExit(1)

        with self._patch_common(tmp_path), \
             patch("backend.scripts.backup_db.find_pg_binary", return_value="pg_dump"), \
             patch("backend.services.backup_service.subprocess.run", return_value=fake_process), \
             patch("backend.scripts.backup_db.get_cipher", side_effect=_raise_system_exit):
            result = BackupService._backup_postgres(tmp_path, "20260101_000000")  # must not raise

        assert result["status"] == "FAILED"
        assert result["error_code"] == "MISSING_MASTER_KEY"

    def test_full_success_produces_nonempty_file_with_checksum(self, tmp_path):
        dump_bytes = b"-- SQL dump content --\nCREATE TABLE t (id int);\n"
        fake_process = MagicMock(returncode=0, stdout=dump_bytes, stderr=b"")
        cipher = Fernet(Fernet.generate_key())

        with self._patch_common(tmp_path), \
             patch("backend.scripts.backup_db.find_pg_binary", return_value="pg_dump"), \
             patch("backend.services.backup_service.subprocess.run", return_value=fake_process), \
             patch("backend.scripts.backup_db.get_cipher", return_value=cipher):
            result = BackupService._backup_postgres(tmp_path, "20260101_000000")

        assert result["status"] == "SUCCESS"
        final_file = tmp_path / result["backup_filename"]
        assert final_file.exists()
        assert final_file.stat().st_size > 0
        assert result["checksum"] is not None
        assert final_file.name.startswith("db_backup_") and final_file.name.endswith(".sql.enc")
        # No leftover scoped temp file
        assert list(tmp_path.glob(".tmp_*")) == []

    def test_never_calls_sqlite3_connect_or_touches_clinical_vault(self, tmp_path):
        """Never touches clinical_vault.db while on the PostgreSQL route."""
        dump_bytes = b"-- SQL dump --"
        fake_process = MagicMock(returncode=0, stdout=dump_bytes, stderr=b"")
        cipher = Fernet(Fernet.generate_key())

        with self._patch_common(tmp_path), \
             patch("backend.scripts.backup_db.find_pg_binary", return_value="pg_dump"), \
             patch("backend.services.backup_service.subprocess.run", return_value=fake_process), \
             patch("backend.scripts.backup_db.get_cipher", return_value=cipher), \
             patch("backend.services.backup_service.sqlite3.connect") as mock_sqlite_connect:
            result = BackupService._backup_postgres(tmp_path, "20260101_000000")

        mock_sqlite_connect.assert_not_called()
        assert result["status"] == "SUCCESS"

    def test_no_secrets_in_log_messages(self, tmp_path, caplog):
        """DATABASE_URL, PGPASSWORD, and CABINET_MASTER_KEY_HEX must never appear in
        logged text, success or failure."""
        fake_process = MagicMock(returncode=1, stdout=b"", stderr=b"pg_dump: error")
        secret_url = "postgresql://postgres:SuperSecretPass123@localhost/digitalcrown_db"

        with self._patch_common(tmp_path, db_url=secret_url), \
             patch("backend.scripts.backup_db.find_pg_binary", return_value="pg_dump"), \
             patch("backend.services.backup_service.subprocess.run", return_value=fake_process), \
             caplog.at_level("DEBUG"):
            BackupService._backup_postgres(tmp_path, "20260101_000000")

        log_text = caplog.text
        assert "SuperSecretPass123" not in log_text
        assert secret_url not in log_text
