"""Four CPV2-02C pre-audit major findings, all synthetic and non-destructive.

Lab-only: real SQLCipher/DocumentArchive, encrypted portable bundle, actual
GuidedRestore preflight. No live cabinet, replay, deletion, migration or deploy.
"""
from __future__ import annotations

import hashlib
import secrets
import uuid
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool
from sqlcipher3 import dbapi2 as cipher

from backend import models
from backend.core.paths import AppPaths
from backend.services.archive_service import _mirror_pdf_without_overwrite
from backend.services.cabinet_bundle import CabinetBundleService, _export_sqlcipher_plaintext
from backend.services.guided_restore import GuidedRestoreService
from backend.services.guided_restore_archive import _validate_zip_infos, MAX_MEDIA_ARCHIVE_ENTRIES
from backend.services.mobile_document_archive_receipts import (
    PocketReceiptBase, claim_archive_intent, complete_archive_in_current_transaction,
)

OWNER = 97601
PATIENT = 97602
PDF = b"%PDF-1.4\n1 0 obj << /Type /Catalog >> endobj\n%%EOF\n"
CANON = "archives/97602/CERTIFICAT/2026/11/fictional.pdf"
MIRROR = "documents/2026/11/fictional.pdf"
ERROR = "Archive clinique Pocket non vérifiable : revue manuelle requise."


def _engine(path: Path, key: str):
    def connect():
        c = cipher.connect(str(path), timeout=12, check_same_thread=False)
        c.execute("PRAGMA key = '" + key + "'")
        c.execute("SELECT count(*) FROM sqlite_master")
        return c
    return create_engine("sqlite:///" + str(path), creator=connect, poolclass=NullPool)


def test_legacy_mirror_collision_preserves_both_distinct_pdfs(tmp_path):
    """Same historical filename, two fictional patients: NEVER overwrite."""
    first = tmp_path / "patient-A.pdf"
    second = tmp_path / "patient-B.pdf"
    legacy = tmp_path / "documents" / "2026" / "11" / "same-name.pdf"
    legacy.parent.mkdir(parents=True)
    first.write_bytes(PDF)
    second.write_bytes(PDF.replace(b"Catalog", b"Catxlog"))
    _mirror_pdf_without_overwrite(first, legacy)
    before = legacy.read_bytes()
    assert before == first.read_bytes()
    _mirror_pdf_without_overwrite(first, legacy)  # generated earlier, exact bytes
    assert legacy.read_bytes() == before
    with pytest.raises(RuntimeError, match="Collision de fichier historique"):
        _mirror_pdf_without_overwrite(second, legacy)
    assert legacy.read_bytes() == before
    assert second.read_bytes() != before
    # An existing symlink must never be followed/rewritten.
    link = tmp_path / "unsafe-legacy.pdf"
    try:
        link.symlink_to(legacy)
    except (OSError, NotImplementedError):
        pass  # Windows without symlink privileges; collision still covered.
    else:
        with pytest.raises(RuntimeError, match="revue manuelle"):
            _mirror_pdf_without_overwrite(second, link)
        assert legacy.read_bytes() == before


@pytest.mark.parametrize(
    "risk",
    ["legacy_missing_pdf", "legacy_complete", "trash_valid", "processing_orphan", "unlinked_orphan"],
)
def test_real_encrypted_preflight_four_pre_audit_risks(tmp_path, monkeypatch, risk):
    """No-pocket legacy integrity, trashed docs, PROCESSING, orphan PDF inventory."""
    vault = tmp_path / "only-disposable-secret-vault"
    vault.mkdir(mode=0o700)
    monkeypatch.setattr(AppPaths, "get_user_data_dir", staticmethod(lambda: vault))
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME", "true")
    monkeypatch.setenv("SECRET_KEY", "synthetic-security-laboratory-not-a-cabinet-secret")
    monkeypatch.setenv("CABINET_MASTER_KEY_HEX", "86" * 32)
    key = "79" * 32  # Same fixture key as the independent G04 matrix subprocess.
    monkeypatch.setenv("SQLCIPHER_KEY_HEX", key)

    source = tmp_path / "synthetic-source.sqlcipher"
    engine = _engine(source, key)
    models.Base.metadata.create_all(
        engine,
        tables=[models.User.__table__, models.Patient.__table__, models.DocumentArchive.__table__],
    )
    PocketReceiptBase.metadata.create_all(engine)
    media = tmp_path / "synthetic-media"
    mirror = media / MIRROR
    canonical = media / CANON
    mirror.parent.mkdir(parents=True)
    mirror.write_bytes(PDF)
    if risk != "legacy_missing_pdf":
        canonical.parent.mkdir(parents=True)
        canonical.write_bytes(PDF)
    if risk == "unlinked_orphan":
        other = media / "archives" / "99999" / "CERTIFICAT" / "2026" / "11" / "unlinked.pdf"
        other.parent.mkdir(parents=True)
        other.write_bytes(PDF)

    with Session(engine) as db:
        db.add(models.User(
            id=OWNER, email="synthetic@example.invalid",
            hashed_password="not-a-login", role=models.UserRole.DENTISTE,
        ))
        db.add(models.Patient(
            id=PATIENT, employer_id=OWNER,
            nom="FICTION", prenom="ONLY", sexe="F",
            date_naissance=datetime(2000, 1, 1),
        ))
        db.commit()
        if risk != "processing_orphan":
            status = models.DocumentStatus.SUPPRIME if risk == "trash_valid" else models.DocumentStatus.ACTIF
            doc = models.DocumentArchive(
                patient_id=PATIENT, uploaded_by_id=OWNER,
                document_type=models.DocumentType.CERTIFICAT,
                filename="fictional.pdf", original_filename="fictional.pdf",
                document_group_id=str(uuid.uuid4()),
                version_number=1, is_latest_version=True,
                file_hash=hashlib.sha256(PDF).hexdigest(), file_size=len(PDF),
                file_path="static/" + CANON,
                status=status, tags=[], clinical_data={},
            )
            if status == models.DocumentStatus.SUPPRIME:
                doc.deleted_at = datetime.now()
                doc.permanent_delete_at = doc.deleted_at + timedelta(days=365)
            db.add(doc)
            db.commit()
            if risk in {"trash_valid", "unlinked_orphan"}:
                receipt, new = claim_archive_intent(
                    db, tenant_id=OWNER, actor_id=OWNER,
                    device_id="synthetic-device", key=str(uuid.uuid4()),
                    patient_id=PATIENT, document_type="certificat", request_sha256="a" * 64,
                )
                assert new
                db.info["_mobile_document_archive_receipt_id"] = receipt.id
                complete_archive_in_current_transaction(db, archive=doc)
                db.commit()
        else:
            # Never infer that either physical orphan belongs to a receipt:
            # only manual forensics may resolve the PROCESSING crash window.
            receipt, new = claim_archive_intent(
                db, tenant_id=OWNER, actor_id=OWNER,
                device_id="synthetic-device", key=str(uuid.uuid4()),
                patient_id=PATIENT, document_type="certificat", request_sha256="b" * 64,
            )
            assert new and receipt.state == "PROCESSING"
    engine.dispose()

    transit = tmp_path / "disposable-plaintext.sqlite"
    _export_sqlcipher_plaintext(source, transit, key)
    encrypted = tmp_path / "synthetic-valid-crypto.dcbundle"
    package_key = secrets.token_urlsafe(32)
    CabinetBundleService.create_bundle(
        encrypted, package_key, database_path=transit, media_root=media,
    )
    guided = tmp_path / "disposable-guided.zip"
    CabinetBundleService.to_local_guided_restore_archive(
        encrypted, package_key, guided, active_engine=("sqlite", "pysqlcipher"),
    )
    verdict = GuidedRestoreService.preflight_file(
        guided, original_name="synthetic-guided.zip",
        active_engine=("sqlite", "pysqlcipher"), owner_employer_id=OWNER,
    )
    if risk in {"legacy_complete", "trash_valid"}:
        assert verdict["status"] == "preflight_ready"
        assert verdict["compatible"] is True
        assert not verdict["errors"]
    else:
        assert verdict["status"] == "blocked"
        assert verdict["compatible"] is False
        assert verdict["errors"] == [ERROR]
    assert GuidedRestoreService.runtime_apply_supported() is False
    assert mirror.read_bytes() == PDF
    assert canonical.exists() == (risk != "legacy_missing_pdf")


@pytest.mark.parametrize("entries", [
    ["documents/a.pdf", "documents/a.pdf"],
    ["documents/a.pdf", "documents/A.pdf"],
    ["documents/a.pdf", "documents//a.pdf"],
    ["documents/a.pdf", "documents/./a.pdf"],
])
def test_duplicate_or_equivalent_zip_members_rejected_even_without_completed_receipts(entries):
    """ZIP structural check applies before any receipt-dependent semantic logic."""
    infos = [zipfile.ZipInfo(name) for name in entries]
    with pytest.raises(ValueError, match="noms de fichiers ambigus"):
        _validate_zip_infos(infos, max_entries=MAX_MEDIA_ARCHIVE_ENTRIES)
