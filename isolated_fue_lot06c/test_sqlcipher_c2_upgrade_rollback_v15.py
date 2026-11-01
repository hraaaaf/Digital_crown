"""LOT06 C05B-03M: real c1/c2 Alembic rehearsal on disposable SQLCipher.

This test exercises existing clinical_assets c1/c2 revisions, not a new
approval/receipt schema. It does not test every legacy binary, perform a
cabinet migration, or provide atomicity across files and SQL.
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import secrets
import shutil

from alembic.migration import MigrationContext
from alembic.operations import Operations
import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

C1 = "c1a55e700001"
C2 = "c2a55e700002"


def _guard() -> None:
    if not (
        os.getenv("ENVIRONMENT") == "test"
        and os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") == "true"
        and os.getenv("DC06C05B03M_TEST_ONLY") == "1"
    ):
        raise RuntimeError("C05B03M_SYNTHETIC_ONLY")


def _engine(root: Path, key: str):
    _guard()
    if not (len(key) == 64 and all(c in "0123456789abcdef" for c in key)):
        raise ValueError("INVALID_SYNTHETIC_CIPHER_KEY")
    from sqlcipher3 import dbapi2 as sqlcipher

    def connect():
        db = sqlcipher.connect(str(root / "c05b03-migration.db"), timeout=20)
        try:
            db.execute("PRAGMA key = '" + key + "'")
            if not db.execute("PRAGMA cipher_version").fetchone():
                raise RuntimeError("NATIVE_SQLCIPHER_REQUIRED")
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("PRAGMA synchronous=NORMAL")
            db.execute("PRAGMA foreign_keys=ON")
            assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
            db.execute("SELECT name FROM sqlite_master LIMIT 1").fetchone()
            return db
        except BaseException:
            db.close()
            raise

    return create_engine("sqlite://", creator=connect, poolclass=NullPool, future=True)


def _revision_file(rev: str) -> Path:
    files = {
        C1: "c1a55e700001_add_clinical_assets.py",
        C2: "c2a55e700002_add_clinical_asset_storage.py",
    }
    return Path(__file__).resolve().parents[1] / "alembic" / "versions" / files[rev]


def _apply_revision(conn, rev: str, direction: str) -> None:
    """Call the actual immutable Alembic revision, not a copied DDL sketch."""
    spec = importlib.util.spec_from_file_location("lot06_c05b03m_" + rev, _revision_file(rev))
    if spec is None or spec.loader is None:
        raise RuntimeError("REVISION_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if module.revision != rev:
        raise RuntimeError("REVISION_IDENTITY_CONFLICT")
    context = MigrationContext.configure(conn)
    with Operations.context(context):
        getattr(module, direction)()


def _version(conn) -> str | None:
    return conn.exec_driver_sql("SELECT version_num FROM alembic_version").scalar_one_or_none()


def _upgrade_c2(conn) -> bool:
    existing = _version(conn)
    if existing == C2:
        return False  # version-gated replay; c2.upgrade() itself is not idempotent
    if existing != C1:
        raise RuntimeError("UNSUPPORTED_MIGRATION_START")
    _apply_revision(conn, C2, "upgrade")
    conn.exec_driver_sql("UPDATE alembic_version SET version_num=?", (C2,))
    return True


def _downgrade_c2(conn) -> bool:
    if _version(conn) != C2:
        raise RuntimeError("UNSUPPORTED_DOWNGRADE_START")
    _apply_revision(conn, C2, "downgrade")
    conn.exec_driver_sql("UPDATE alembic_version SET version_num=?", (C1,))
    return True


def _cols(conn):
    return {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(clinical_assets)")}


def _legacy_create(conn, asset_id: int, digest: str):
    conn.exec_driver_sql(
        "INSERT INTO clinical_assets "
        "(id,employer_id,patient_id,asset_type,source_kind,created_by,byte_size,sha256) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (asset_id, 31, 73, "PHOTO", "UPLOAD", 81, 15, digest),
    )


def _legacy_read(conn):
    return conn.exec_driver_sql(
        "SELECT id,employer_id,patient_id,source_kind,sha256,byte_size "
        "FROM clinical_assets ORDER BY id"
    ).fetchall()


def test_c05b03m_real_c1_c2_sqlcipher_upgrade_rollback_restore(tmp_path, monkeypatch):
    _guard()
    key = secrets.token_hex(32)
    root = tmp_path / "migration-only"
    root.mkdir()
    engine = _engine(root, key)
    before = ("c" * 64, "d" * 64)
    try:
        with engine.begin() as conn:
            conn.exec_driver_sql("CREATE TABLE users(id INTEGER PRIMARY KEY)")
            conn.exec_driver_sql("CREATE TABLE patients(id INTEGER PRIMARY KEY)")
            conn.exec_driver_sql("INSERT INTO users VALUES(31)")
            conn.exec_driver_sql("INSERT INTO users VALUES(81)")
            conn.exec_driver_sql("INSERT INTO patients VALUES(73)")
            _apply_revision(conn, C1, "upgrade")
            conn.exec_driver_sql("CREATE TABLE alembic_version(version_num VARCHAR(32) PRIMARY KEY)")
            conn.exec_driver_sql("INSERT INTO alembic_version VALUES(?)", (C1,))
            _legacy_create(conn, 9001, before[0])
            assert _version(conn) == C1
            assert len(_legacy_read(conn)) == 1
        # Close/checkpoint every connection before copying a WAL-mode encrypted DB.
        with engine.connect() as conn:
            conn.exec_driver_sql("PRAGMA wal_checkpoint(TRUNCATE)")
        engine.dispose()
        original = root / "c05b03-migration.db"
        assert original.read_bytes()[:16] != b"SQLite format 3\\x00"
        snapshot = tmp_path / "preupgrade-sqlcipher-snapshot.db"
        shutil.copy2(original, snapshot)

        engine = _engine(root, key)
        with engine.begin() as conn:
            assert _upgrade_c2(conn) is True
            assert _version(conn) == C2
            assert {"storage_key", "storage_format", "stored_at"}.issubset(_cols(conn))
            assert len(_legacy_read(conn)) == 1
            # Older named-column writes remain valid; old data is never
            # guessed to be encrypted/verified without an actual media blob.
            _legacy_create(conn, 9002, before[1])
            assert conn.exec_driver_sql(
                "SELECT COUNT(*) FROM clinical_assets WHERE storage_key IS NULL"
            ).scalar_one() == 2
            assert _upgrade_c2(conn) is False
            assert len(_legacy_read(conn)) == 2
        with engine.begin() as conn:
            assert _downgrade_c2(conn) is True
            assert _version(conn) == C1
            assert {"storage_key", "storage_format", "stored_at"}.isdisjoint(_cols(conn))
            assert [tuple(r) for r in _legacy_read(conn)] == [
                (9001, 31, 73, "UPLOAD", before[0], 15),
                (9002, 31, 73, "UPLOAD", before[1], 15),
            ]
        engine.dispose()
        # Restore PRE-upgrade encrypted snapshot into an entirely distinct path.
        restored = tmp_path / "restored"
        restored.mkdir()
        shutil.copy2(snapshot, restored / "c05b03-migration.db")
        recovery = _engine(restored, key)
        try:
            with recovery.connect() as conn:
                assert _version(conn) == C1
                assert [tuple(r) for r in _legacy_read(conn)] == [
                    (9001, 31, 73, "UPLOAD", before[0], 15)
                ]
        finally:
            recovery.dispose()
        from sqlcipher3 import dbapi2 as sqlcipher
        wrong = sqlcipher.connect(str(restored / "c05b03-migration.db"))
        try:
            wrong.execute("PRAGMA key = '" + secrets.token_hex(32) + "'")
            with pytest.raises(sqlcipher.DatabaseError):
                wrong.execute("SELECT COUNT(*) FROM clinical_assets").fetchone()
        finally:
            wrong.close()
        evidence = Path(os.getenv("DC06C05B03M_EVIDENCE_DIR", str(tmp_path)))
        evidence.mkdir(parents=True, exist_ok=True)
        (evidence / "lot06c05b03m-c1-c2-migration-fue.json").write_text(
            json.dumps({
                "kind": "LOT06_C05B03M_REAL_ALEMBIC_C1_C2_SYNTHETIC_SQLCIPHER",
                "real_existing_c1_c2_revisions_executed": True,
                "encrypted_onprem_like_fixture_used": True,
                "named_column_legacy_client_roundtrip": True,
                "version_gated_second_upgrade_noop": True,
                "existing_fields_preserved_after_downgrade": True,
                "encrypted_preupgrade_snapshot_restored": True,
                "wrong_cipher_key_rejected": True,
                "production_staff_device_receipt_schema_migrated": False,
                "actual_legacy_client_binary_tested": False,
                "real_cabinet_upgrade_executed": False,
                "product_ready": False,
                "clinical_go": False,
            }, sort_keys=True, indent=2) + "\\n", encoding="utf-8",
        )
        print("C05B03M_SQLCIPHER_REAL_ALEMBIC_C1_C2_REHEARSAL_PASS_NO_PRODUCT_MIGRATION")
    finally:
        engine.dispose()
