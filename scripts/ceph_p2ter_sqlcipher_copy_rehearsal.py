"""Synthetic SQLCipher pre-existing-schema COPY rehearsal for cephalo claim migration.

Never reads, opens or writes a real cabinet file. The original encrypted
fixture remains SHA-identical and migration runs on a physically separate copy.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile

assert os.getenv("ENVIRONMENT") == "test"
assert os.getenv("DIGITALCROWN_ISOLATED_RUNTIME") in ("1", "true")
key = os.environ["SQLCIPHER_KEY_HEX"]
assert len(key) == 64 and all(c in "0123456789abcdef" for c in key.lower())
assert os.getenv("DATABASE_URL", "").startswith("sqlite:///")
from sqlcipher3 import dbapi2 as cipher

def open_cipher(path: Path):
    db = cipher.connect(str(path))
    db.execute("PRAGMA key = '" + key + "'")
    db.execute("PRAGMA foreign_keys = ON")
    db.execute("SELECT count(*) FROM sqlite_master").fetchone()
    return db

with tempfile.TemporaryDirectory(prefix="p2ter-cipher-") as directory:
    root = Path(directory).resolve()
    original = root / "legacy-opaque-synthetic.db"
    backup = root / "sealed-backup-synthetic.db"
    copied = root / "restored-migration-synthetic.db"
    source_media = root / "media-source" / "1717" / "RAPPORT_CEPHALO" / "2026" / "10" / "original.pdf"
    restored_media = root / "media-restored" / "1717" / "RAPPORT_CEPHALO" / "2026" / "10" / "original.pdf"
    source_media.parent.mkdir(parents=True)
    source_media.write_bytes(b"%PDF-1.4\\nSYNTHETIC_OFFLINE_MEDIA\\n")
    media_hash = hashlib.sha256(source_media.read_bytes()).hexdigest()
    with open_cipher(original) as conn:
        conn.executescript("""
            CREATE TABLE alembic_version(version_num varchar(32) NOT NULL);
            INSERT INTO alembic_version VALUES ('neo000000027');
            CREATE TABLE patients(id INTEGER PRIMARY KEY, marker text NOT NULL);
            INSERT INTO patients VALUES (1717,'SYNTHETIC PATIENT ONLY');
            CREATE TABLE cephalo_analyses(id INTEGER PRIMARY KEY,patient_id INTEGER NOT NULL REFERENCES patients(id));
            INSERT INTO cephalo_analyses VALUES (2727,1717);
            CREATE TABLE document_archives(id INTEGER PRIMARY KEY, patient_id INTEGER REFERENCES patients(id), file_path TEXT);
            INSERT INTO document_archives VALUES (91,1717,'static/archives/1717/RAPPORT_CEPHALO/2026/10/original.pdf');
            CREATE TABLE cabinet_configs(id INTEGER PRIMARY KEY, owner_id INTEGER, nom_cabinet TEXT);
            INSERT INTO cabinet_configs VALUES (37,1717,'SYNTHETIC CABINET LAYOUT');
        """)
        conn.commit()
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
    conn.close()  # quiesced source before a byte-for-byte encrypted backup
    original_bytes = original.read_bytes()
    original_hash = hashlib.sha256(original_bytes).hexdigest()
    # SQLite may not parse encrypted SQLCipher as a plaintext DB.
    try:
        with sqlite3.connect(str(original)) as plain:
            plain.execute("SELECT marker FROM patients").fetchone()
    except sqlite3.DatabaseError:
        pass
    else:
        raise AssertionError("SYNTHETIC_SQLCIPHER_NOT_ENCRYPTED")
    # Offline immutable backup + independent restore. Both DB and media must
    # be preserved; never run migrations against either protected source.
    shutil.copy2(original, backup)
    assert backup.read_bytes() == original_bytes
    restored_media.parent.mkdir(parents=True)
    shutil.copy2(source_media, restored_media)
    shutil.copy2(backup, copied)
    assert copied.read_bytes() == original_bytes
    assert hashlib.sha256(restored_media.read_bytes()).hexdigest() == media_hash
    with open_cipher(copied) as restored:
        assert restored.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert restored.execute("PRAGMA foreign_key_check").fetchall() == []
        assert restored.execute("SELECT count(*) FROM document_archives").fetchone()[0] == 1

    # Explicit migration. Never AUTO-migrate or touch the original.
    env = os.environ.copy()
    env["DATABASE_URL"] = "sqlite:///" + str(copied)
    env["ENVIRONMENT"] = "test"
    env["DIGITALCROWN_ISOLATED_RUNTIME"] = "1"
    outcome = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "ceparch0002"],
        env=env, text=True, capture_output=True, timeout=120,
        check=False,
    )
    if outcome.returncode:
        print(outcome.stderr[-2800:], file=sys.stderr)
        raise AssertionError("SQLCIPHER_COPY_MIGRATION_FAILED")

    with open_cipher(copied) as conn:
        head=conn.execute("SELECT version_num FROM alembic_version").fetchone()[0]
        assert head=="ceparch0002",head
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
        assert conn.execute("SELECT file_path FROM document_archives WHERE id=91").fetchone()[0] == "static/archives/1717/RAPPORT_CEPHALO/2026/10/original.pdf"
        assert conn.execute("SELECT nom_cabinet FROM cabinet_configs WHERE id=37").fetchone()[0]=="SYNTHETIC CABINET LAYOUT"
        assert conn.execute("SELECT content_offset_y FROM cabinet_configs WHERE id=37").fetchone()[0]==0.0
        assert conn.execute("SELECT marker FROM patients WHERE id=1717").fetchone()[0]=="SYNTHETIC PATIENT ONLY"
        conn.execute("INSERT INTO cephalo_archive_claims(patient_id,analysis_id,revision) VALUES(1717,2727,2)")
        conn.commit()
        try:
            conn.execute("INSERT INTO cephalo_archive_claims(patient_id,analysis_id,revision) VALUES(1717,2727,2)")
            conn.commit()
        except cipher.IntegrityError:
            conn.rollback()
        else:
            raise AssertionError("SQLCIPHER_UNIQUE_CLAIM_NOT_ENFORCED")
        assert conn.execute("SELECT count(*) FROM cephalo_archive_claims").fetchone()[0]==1

    assert hashlib.sha256(original.read_bytes()).hexdigest()==original_hash
    assert hashlib.sha256(backup.read_bytes()).hexdigest()==original_hash
    assert hashlib.sha256(source_media.read_bytes()).hexdigest()==media_hash
    assert hashlib.sha256(restored_media.read_bytes()).hexdigest()==media_hash
    print("SQLCIPHER_SYNTHETIC_PREEXISTING_DB_COPY_UPGRADE_PASS",
          {"head":head,"legacy_rows_retained":1,"unique_claim_rows":1,
           "original_fixture_unchanged":True,"sealed_backup_unchanged":True,
           "media_restore_hash_verified":True,"integrity_check":"ok",
           "real_cabinet_used":False})
