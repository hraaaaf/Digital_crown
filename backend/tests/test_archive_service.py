"""Tests for services/archive_service.py — document archiving, conflict detection."""
import pytest
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from backend import models
from backend.models import DocumentType, DocumentStatus
from backend.services.archive_service import ArchiveService
from backend.schemas import ConflictResolution


def _make_patient(db, dentiste, nom="ARCHPAT"):
    pat = models.Patient(
        nom=nom, prenom="Test",
        date_naissance=datetime(1985, 3, 10),
        sexe="M",
        employer_id=dentiste.id,
    )
    db.add(pat)
    db.flush()
    db.add(models.DossierClinique(patient_id=pat.id, is_ortho_active=False))
    db.commit()
    db.refresh(pat)
    return pat


def _make_doc(db, patient_id, filename="test.pdf", file_hash=None):
    if file_hash is None:
        file_hash = hashlib.sha256(filename.encode()).hexdigest()
    doc = models.DocumentArchive(
        patient_id=patient_id,
        document_type=DocumentType.ORDONNANCE,
        filename=filename,
        original_filename=filename,
        document_group_id=str(uuid.uuid4()),
        file_hash=file_hash,
        file_size=1024,
        file_path=f"/tmp/{filename}",
        status=DocumentStatus.ACTIF,
        created_at=datetime.now(),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


class TestArchiveServiceHelpers:
    def test_calculate_file_hash(self, db):
        svc = ArchiveService(db)
        content = b"hello world"
        h = svc._calculate_file_hash(content)
        assert h == hashlib.sha256(content).hexdigest()
        assert len(h) == 64

    def test_generate_document_group_id_is_uuid(self, db):
        svc = ArchiveService(db)
        gid = svc._generate_document_group_id()
        assert len(gid) == 36
        assert "-" in gid

    def test_get_storage_path_creates_dir(self, db, tmp_path, monkeypatch):
        import backend.services.archive_service as archive_mod
        monkeypatch.setattr(archive_mod, "ARCHIVE_BASE_DIR", tmp_path / "archives")
        svc = ArchiveService(db)
        path = svc._get_storage_path(1, DocumentType.ORDONNANCE, "test.pdf", version=1)
        assert path.parent.exists()
        assert path.name == "test.pdf"

    def test_get_storage_path_version_suffix(self, db, tmp_path, monkeypatch):
        import backend.services.archive_service as archive_mod
        monkeypatch.setattr(archive_mod, "ARCHIVE_BASE_DIR", tmp_path / "archives")
        svc = ArchiveService(db)
        path = svc._get_storage_path(1, DocumentType.ORDONNANCE, "test.pdf", version=2)
        assert "_v2" in path.name


class TestCheckConflicts:
    def test_no_conflict_new_doc(self, db, dentiste):
        pat = _make_patient(db, dentiste, "NOCONF")
        svc = ArchiveService(db)
        result = svc.check_conflicts(
            patient_id=pat.id,
            file_hash="uniquehash123",
            filename="new_doc.pdf",
            doc_type=DocumentType.ORDONNANCE,
        )
        assert result["has_conflict"] is False

    def test_conflict_same_hash(self, db, dentiste):
        pat = _make_patient(db, dentiste, "HASHCONF")
        svc = ArchiveService(db)
        file_hash = "samehash456"
        _make_doc(db, pat.id, "doc.pdf", file_hash=file_hash)

        result = svc.check_conflicts(
            patient_id=pat.id,
            file_hash=file_hash,
            filename="doc.pdf",
            doc_type=DocumentType.ORDONNANCE,
        )
        assert result["has_conflict"] is True
        assert result["conflict_reason"] == "same_hash"

    def test_conflict_same_name_same_day(self, db, dentiste):
        pat = _make_patient(db, dentiste, "NAMECONF")
        svc = ArchiveService(db)
        _make_doc(db, pat.id, "ordonnance.pdf")

        result = svc.check_conflicts(
            patient_id=pat.id,
            file_hash="differenthash789",
            filename="ordonnance.pdf",
            doc_type=DocumentType.ORDONNANCE,
        )
        assert result["has_conflict"] is True
        assert result["conflict_reason"] == "same_name_same_day"

    def test_conflict_duplicate_content(self, db, dentiste):
        pat = _make_patient(db, dentiste, "CONTENTCONF")
        svc = ArchiveService(db)
        clinical_data = {"items": [{"nom": "Composite", "montant": 500}]}
        # Create a doc with this clinical_data
        doc = _make_doc(db, pat.id, "note.pdf")
        doc.clinical_data = clinical_data
        db.commit()

        result = svc.check_conflicts(
            patient_id=pat.id,
            file_hash="anotherHash",
            filename="note2.pdf",
            doc_type=DocumentType.ORDONNANCE,
            clinical_data=clinical_data,
        )
        assert result["has_conflict"] is True


class TestArchiveDocument:
    def test_archive_document_creates_db_record(self, db, dentiste, tmp_path, monkeypatch):
        import backend.services.archive_service as archive_mod
        monkeypatch.setattr(archive_mod, "ARCHIVE_BASE_DIR", tmp_path / "archives")
        monkeypatch.setattr(archive_mod, "LEGACY_DOCS_DIR", tmp_path / "docs")
        pat = _make_patient(db, dentiste, "ARCHCREATE")
        svc = ArchiveService(db)
        content = b"PDF content here"
        doc, is_new_version = svc.archive_document(
            patient_id=pat.id,
            file_content=content,
            filename="ordonnance.pdf",
            doc_type=DocumentType.ORDONNANCE,
            uploaded_by_id=dentiste.id,
        )
        assert doc.id is not None
        assert doc.patient_id == pat.id
        assert is_new_version is False

    def test_archive_document_duplicate_cancel_raises(self, db, dentiste, tmp_path, monkeypatch):
        import backend.services.archive_service as archive_mod
        monkeypatch.setattr(archive_mod, "ARCHIVE_BASE_DIR", tmp_path / "archives")
        monkeypatch.setattr(archive_mod, "LEGACY_DOCS_DIR", tmp_path / "docs")
        pat = _make_patient(db, dentiste, "ARCHDUP")
        content = b"Same PDF content"
        file_hash = hashlib.sha256(content).hexdigest()
        _make_doc(db, pat.id, "dup.pdf", file_hash=file_hash)

        svc = ArchiveService(db)
        with pytest.raises(ValueError):
            svc.archive_document(
                patient_id=pat.id,
                file_content=content,
                filename="dup.pdf",
                doc_type=DocumentType.ORDONNANCE,
                on_conflict=ConflictResolution.CANCEL,
            )


class TestVersionsAndTrash:
    def test_get_document_versions(self, db, dentiste):
        pat = _make_patient(db, dentiste, "VERSIONS")
        group_id = str(uuid.uuid4())
        for i in range(3):
            doc = models.DocumentArchive(
                patient_id=pat.id,
                document_type=DocumentType.ORDONNANCE,
                filename=f"doc_v{i+1}.pdf",
                original_filename="doc.pdf",
                document_group_id=group_id,
                file_hash=f"hash{i}",
                file_size=100 + i,
                file_path=f"/tmp/doc_v{i+1}.pdf",
            )
            db.add(doc)
        db.commit()

        svc = ArchiveService(db)
        versions = svc.get_document_versions(group_id)
        assert len(versions) == 3

    def test_move_to_trash(self, db, dentiste):
        pat = _make_patient(db, dentiste, "TRASH")
        doc = _make_doc(db, pat.id, "to_trash.pdf")
        svc = ArchiveService(db)
        result = svc.move_to_trash(doc.id)
        assert result.status == DocumentStatus.SUPPRIME

    def test_move_nonexistent_to_trash_raises(self, db):
        svc = ArchiveService(db)
        with pytest.raises(Exception):
            svc.move_to_trash(999999)

    def test_restore_from_trash(self, db, dentiste):
        pat = _make_patient(db, dentiste, "RESTORE")
        doc = _make_doc(db, pat.id, "restore.pdf")
        svc = ArchiveService(db)
        # Move to trash first
        svc.move_to_trash(doc.id)
        # Then restore
        result = svc.restore_from_trash(doc.id)
        assert result.status == DocumentStatus.ACTIF

    def test_restore_nonexistent_raises(self, db):
        svc = ArchiveService(db)
        with pytest.raises(Exception):
            svc.restore_from_trash(999999)

    def test_permanent_delete(self, db, dentiste):
        pat = _make_patient(db, dentiste, "PERMDELETE")
        doc = _make_doc(db, pat.id, "delete.pdf")
        svc = ArchiveService(db)
        result = svc.permanent_delete(doc.id)
        assert result is True

    def test_permanent_delete_nonexistent_returns_false(self, db):
        svc = ArchiveService(db)
        result = svc.permanent_delete(999999)
        assert result is False

    def test_cleanup_expired_trash(self, db):
        svc = ArchiveService(db)
        count = svc.cleanup_expired_trash()
        assert isinstance(count, int)


class TestSearchDocuments:
    def test_search_all_returns_list(self, db, dentiste):
        pat = _make_patient(db, dentiste, "SEARCHALL")
        _make_doc(db, pat.id, "search_doc.pdf")
        svc = ArchiveService(db)
        results, total = svc.search_documents(patient_id=pat.id)
        assert len(results) >= 1
        assert total >= 1

    def test_search_by_type(self, db, dentiste):
        pat = _make_patient(db, dentiste, "SEARCHTYPE")
        _make_doc(db, pat.id, "ord.pdf")
        svc = ArchiveService(db)
        results, total = svc.search_documents(patient_id=pat.id, doc_type=DocumentType.ORDONNANCE)
        assert all(r.document_type == DocumentType.ORDONNANCE for r in results)

    def test_search_empty_result(self, db, dentiste):
        pat = _make_patient(db, dentiste, "SEARCHEMPTY")
        svc = ArchiveService(db)
        results, total = svc.search_documents(patient_id=pat.id, doc_type=DocumentType.DEVIS)
        assert results == []
        assert total == 0
