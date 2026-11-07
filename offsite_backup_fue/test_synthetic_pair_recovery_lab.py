"""Synthetic encrypted DB+media offsite recovery rehearsal on an isolated path.

This validates recoverable *bytes* and SQLite/ZIP semantics using a TEST key.
It does NOT exercise the real cabinet restore service, PostgreSQL, a second
machine, an actual NAS/SMB share, or clinical recovery. Never label it as such.
"""
import hashlib
import importlib.util
import io
import os
import sqlite3
import zipfile
from pathlib import Path

import pytest
from cryptography.fernet import Fernet, InvalidToken

_SOURCE_PATH = Path(__file__).resolve().parents[1] / "backend" / "scripts" / "backup_offsite.py"
_SPEC = importlib.util.spec_from_file_location("_dc_recovery_offsite_source", _SOURCE_PATH)
assert _SPEC and _SPEC.loader
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while block := source.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _fixture(tmp_path):
    """Create an independent SQLite snapshot and ZIP, then encrypt both."""
    source_root = tmp_path / "synthetic_source"
    source_root.mkdir()
    db = source_root / "cabinet_synthetic.sqlite"
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE fake_patients (id INTEGER PRIMARY KEY, token TEXT NOT NULL)")
        conn.execute("INSERT INTO fake_patients VALUES (1, 'SYNTHETIC_ONLY_8472')")
        conn.commit()
    media = io.BytesIO()
    with zipfile.ZipFile(media, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("radiographs/SYNTHETIC_ONLY_8472.txt", b"synthetic radiograph placeholder")
    cipher = Fernet(Fernet.generate_key())  # ephemeral TEST key, not a cabinet key
    local = tmp_path / "encrypted_local"
    local.mkdir()
    db_source = local / "db_backup_synthetic.sql.enc"
    media_source = local / "media_backup_synthetic.zip.enc"
    db_source.write_bytes(cipher.encrypt(db.read_bytes()))
    media_source.write_bytes(cipher.encrypt(media.getvalue()))
    return cipher, db_source, media_source


def _copy_pair(tmp_path):
    cipher, db_source, media_source = _fixture(tmp_path)
    offsite = tmp_path / "isolated_offsite"
    result = _MODULE.copy_to_offsite(
        db_source, _sha256(db_source), media_source, _sha256(media_source), offsite
    )
    assert result["status"] == "SUCCESS", result
    return cipher, db_source, media_source, offsite


def _recover(cipher, db_source, media_source, offsite, target):
    """Restore synthetic bytes into a distinct directory, never an active DB."""
    assert not target.exists()
    db_copy = offsite / "db" / db_source.name
    media_copy = offsite / "media" / media_source.name
    assert _sha256(db_copy) == _sha256(db_source)
    assert _sha256(media_copy) == _sha256(media_source)
    # Authentication must succeed BEFORE writing recovered files.
    db_plain = cipher.decrypt(db_copy.read_bytes())
    media_plain = cipher.decrypt(media_copy.read_bytes())
    # Do not create a recovery target until both encrypted artifacts have
    # passed integrity and authentication checks.
    target.mkdir(parents=True)
    restored_db = target / "restored_synthetic.sqlite"
    restored_db.write_bytes(db_plain)
    with zipfile.ZipFile(io.BytesIO(media_plain)) as archive:
        names = archive.namelist()
        assert names == ["radiographs/SYNTHETIC_ONLY_8472.txt"]
        assert all(not Path(name).is_absolute() and ".." not in Path(name).parts for name in names)
        recovered_media = archive.read(names[0])
    restored_media = target / names[0]
    restored_media.parent.mkdir(parents=True)
    restored_media.write_bytes(recovered_media)
    return restored_db, restored_media


def test_synthetic_encrypted_pair_recovers_sqlite_and_media_in_isolated_root(tmp_path):
    cipher, db_source, media_source, offsite = _copy_pair(tmp_path)
    target = tmp_path / "different_recovery_root"
    restored_db, restored_media = _recover(
        cipher, db_source, media_source, offsite, target
    )
    with sqlite3.connect(f"file:{restored_db}?mode=ro", uri=True) as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conn.execute("SELECT token FROM fake_patients WHERE id=1").fetchone()[0] == "SYNTHETIC_ONLY_8472"
    assert restored_media.read_bytes() == b"synthetic radiograph placeholder"
    assert restored_db.resolve().is_relative_to(target.resolve())
    assert restored_media.resolve().is_relative_to(target.resolve())


def test_synthetic_recovery_refuses_tampered_offsite_ciphertext(tmp_path):
    cipher, db_source, media_source, offsite = _copy_pair(tmp_path)
    altered = offsite / "media" / media_source.name
    altered.write_bytes(altered.read_bytes() + b"tamper")
    target = tmp_path / "recovery_must_not_be_created"
    with pytest.raises(AssertionError):
        _recover(cipher, db_source, media_source, offsite, target)
    assert not target.exists()


def test_synthetic_recovery_wrong_key_never_writes_plaintext(tmp_path):
    _, db_source, media_source, offsite = _copy_pair(tmp_path)
    target = tmp_path / "wrong_key_target"
    with pytest.raises(InvalidToken):
        _recover(Fernet(Fernet.generate_key()), db_source, media_source, offsite, target)
    assert not (target / "restored_synthetic.sqlite").exists()
    assert not (target / "radiographs").exists()
