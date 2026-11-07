"""CPV2-02C J6: characterize a clinically incomplete but valid encrypted restore.

Test-only, isolated and synthetic. A green characterization test is NOT a
certification of restore safety; it proves the current preflight gap exists.
Do not merge this laboratory PR or activate clinical restoration.
"""
from __future__ import annotations

import hashlib
import secrets
import pytest
import sqlite3
import uuid
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool
from sqlcipher3 import dbapi2 as cipher

from backend import models
from backend.core.paths import AppPaths
from backend.services.cabinet_bundle import (
    CabinetBundleService, _export_sqlcipher_plaintext,
)
from backend.services.guided_restore import GuidedRestoreService
from backend.services.mobile_document_archive_receipts import (
    PocketReceiptBase, claim_archive_intent, complete_archive_in_current_transaction,
)

OWNER = 97901
PATIENT = 97902
PDF = b"%PDF-1.4\n1 0 obj << /Type /Catalog >> endobj\n%%EOF\n"
CANONICAL = "archives/97902/CERTIFICAT/2026/11/fictional-document.pdf"
HISTORICAL = "documents/2026/11/fictional-document.pdf"


def _engine(path, passphrase):
    def connect():
        db = cipher.connect(str(path), timeout=10, check_same_thread=False)
        db.execute("PRAGMA key = '" + passphrase + "'")
        db.execute("SELECT count(*) FROM sqlite_master")
        return db
    return create_engine("sqlite:///" + str(path), creator=connect, poolclass=NullPool)


@pytest.mark.parametrize("clinical_fault", ["missing_canonical", "wrong_hash", "missing_mirror", "wrong_mirror", "wrong_patient_path"])
def test_valid_encryption_does_not_mean_complete_pocket_document(tmp_path, monkeypatch, clinical_fault):
    """Fail-closed guard: all four defects must BLOCK a valid encrypted bundle."""
    private = tmp_path / "ephemeral-keys-only"
    private.mkdir(mode=0o700)
    monkeypatch.setattr(
        AppPaths, "get_user_data_dir", staticmethod(lambda: private),
    )
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME", "true")
    monkeypatch.setenv("SECRET_KEY", "synthetic-only-restore-auth-key-32-char")
    monkeypatch.setenv("CABINET_MASTER_KEY_HEX", "86" * 32)
    # backend.database.engine is cached across pytest parameters and its
    # SQLCipher URL password is read by portable conversion. A deterministic
    # FIXTURE-ONLY key keeps all four scenarios consistent in one CI process.
    # The unrelated migration secret remains fresh/random per scenario.
    passphrase = "79" * 32
    monkeypatch.setenv("SQLCIPHER_KEY_HEX", passphrase)

    source = tmp_path / "synthetic-encrypted-db.sqlcipher"
    engine = _engine(source, passphrase)
    models.Base.metadata.create_all(
        engine,
        tables=[
            models.User.__table__,
            models.Patient.__table__,
            models.DocumentArchive.__table__,
        ],
    )
    PocketReceiptBase.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(models.User(
            id=OWNER, email="fictional@example.invalid",
            hashed_password="not-a-login", role=models.UserRole.DENTISTE,
        ))
        db.add(models.Patient(
            id=PATIENT, employer_id=OWNER,
            nom="SYNTHETIC", prenom="ONLY", sexe="F",
            date_naissance=datetime(2000, 1, 1),
        ))
        db.commit()
        key = str(uuid.uuid4())
        receipt, created = claim_archive_intent(
            db, tenant_id=OWNER, actor_id=OWNER, device_id="fictional-device",
            key=key, patient_id=PATIENT,
            document_type="certificat", request_sha256="a" * 64,
        )
        assert created
        document = models.DocumentArchive(
            patient_id=PATIENT, uploaded_by_id=OWNER,
            document_type=models.DocumentType.CERTIFICAT,
            filename="fictional-document.pdf",
            original_filename="fictional-document.pdf",
            document_group_id=str(uuid.uuid4()),
            version_number=1, is_latest_version=True,
            file_hash=hashlib.sha256(PDF).hexdigest(), file_size=len(PDF),
            file_path="static/" + (CANONICAL.replace("/97902/", "/97903/") if clinical_fault == "wrong_patient_path" else CANONICAL),
            status=models.DocumentStatus.ACTIF, tags=[], clinical_data={},
        )
        db.add(document)
        db.flush()
        db.info["_mobile_document_archive_receipt_id"] = receipt.id
        complete_archive_in_current_transaction(db, archive=document)
        db.commit()
        document_id = document.id
    engine.dispose()

    # Build an AUTHENTIC encrypted, internally checksummed cabinet bundle from
    # an already semantically damaged media tree (canonical is missing).
    media = tmp_path / "synthetic-media"
    mirror = media / HISTORICAL
    mirror.parent.mkdir(parents=True)
    mirror.write_bytes(PDF)
    # Change bytes without changing length: this isolates SHA-256 from size.
    tampered = PDF.replace(b"Catalog", b"Catxlog")
    assert len(tampered) == len(PDF) and hashlib.sha256(tampered).digest() != hashlib.sha256(PDF).digest()
    expected_canonical_path = (CANONICAL.replace("/97902/", "/97903/")
                               if clinical_fault == "wrong_patient_path" else CANONICAL)
    canonical_file = media / expected_canonical_path
    if clinical_fault in {"wrong_hash", "missing_mirror", "wrong_mirror", "wrong_patient_path"}:
        canonical_file.parent.mkdir(parents=True)
        canonical_file.write_bytes(tampered if clinical_fault == "wrong_hash" else PDF)
    if clinical_fault == "missing_mirror":
        mirror.unlink()
    if clinical_fault == "wrong_mirror":
        mirror.write_bytes(tampered)
    assert canonical_file.exists() == (clinical_fault != "missing_canonical")
    portable_db = tmp_path / "plaintext-transit-from-fixture.sqlite"
    _export_sqlcipher_plaintext(source, portable_db, passphrase)
    portable_bundle = tmp_path / "fictional-valid-crypto-invalid-clinical.dcbundle"
    migration_secret = secrets.token_urlsafe(32)
    package = CabinetBundleService.create_bundle(
        portable_bundle, migration_secret,
        database_path=portable_db, media_root=media,
    )
    assert package["media_file_count"] == (1 if clinical_fault in {"missing_canonical", "missing_mirror"} else 2)
    guided_zip = tmp_path / "converted-guided-only.zip"
    conversion = CabinetBundleService.to_local_guided_restore_archive(
        portable_bundle, migration_secret, guided_zip,
        active_engine=("sqlite", "pysqlcipher"),
    )
    assert conversion["media_file_count"] == (1 if clinical_fault in {"missing_canonical", "missing_mirror"} else 2)

    preflight = GuidedRestoreService.preflight_file(
        guided_zip, original_name="fictional-bundle.zip",
        active_engine=("sqlite", "pysqlcipher"), owner_employer_id=OWNER,
    )
    assert preflight["compatible"] is False
    assert preflight["restore_media"] is True
    assert preflight["media_file_count"] == (1 if clinical_fault in {"missing_canonical", "missing_mirror"} else 2)
    assert preflight["status"] == "blocked"
    assert preflight["errors"] == [
        "Archive clinique Pocket non vérifiable : revue manuelle requise."
    ]
    assert document_id > 0
    assert GuidedRestoreService.runtime_apply_supported() is False
    # A rejected fixture never changes the user-controlled source media.
    assert canonical_file.exists() == (clinical_fault != "missing_canonical")
    assert mirror.exists() == (clinical_fault != "missing_mirror")
