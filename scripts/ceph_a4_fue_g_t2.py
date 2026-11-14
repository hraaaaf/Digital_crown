"""FUE-G A4 fixture owner: prepare, verify and scrub a disposable T2 archive.

Never executes on a real cabinet DB. Uses the already-existing isolated
FastAPI/SQLite authentication + calibration seeded by the T2 CI workflow.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

assert os.environ.get("ENVIRONMENT") == "test"
assert os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") == "1"
assert os.environ.get("DATABASE_URL") == "sqlite:///./t2-runtime-cert.db"
assert os.environ.get("CLOUD_AI_ENABLED") == "false"
assert Path("t2-runtime-cert.db").is_file()

from backend import database, models
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY

seed = json.loads(os.environ["CEPH_ODF_CASE_JSON"])
assert seed["fixture_name"] == "T2-CEPH-ODF-E2E-01"
assert seed["clinical_release"] is False
assert len(seed["original_landmarks"]) == 38
assert sys.argv[1:] in (["prepare"], ["verify"], ["cleanup"])

with database.SessionLocal() as db:
    user = db.query(models.User).filter(
        models.User.email == "t2-browser@cabinet.ma",
        models.User.role == models.UserRole.DENTISTE,
    ).one()
    patient = db.get(models.Patient, seed["patient_id"])
    study = db.get(models.CephaloAnalysis, seed["analysis_id"])
    assert patient and patient.employer_id == user.id
    assert patient.numero_dossier == "T2-CEPH-ODF-E2E-01"
    assert study and study.patient_id == patient.id
    operation = sys.argv[1]
    if operation == "prepare":
        assert study.is_calibrated is True and study.mm_per_pixel > 0
        graph = (study.angles_data or {}).get(EVIDENCE_GRAPH_KEY)
        assert isinstance(graph, dict) and type(graph.get("revision")) is int
        assert graph["revision"] > 0
        assert not db.query(models.DocumentArchive).filter(
            models.DocumentArchive.patient_id == patient.id,
            models.DocumentArchive.document_type == models.DocumentType.RAPPORT_CEPHALO,
        ).first()
        cabinet = db.query(models.CabinetConfig).filter(
            models.CabinetConfig.owner_id == user.id,
        ).first()
        if cabinet is None:
            cabinet = models.CabinetConfig(owner_id=user.id)
            db.add(cabinet)
        cabinet.nom_cabinet = "FUE-G CABINET SYNTHETIQUE"
        cabinet.nom_praticien = "Dr T2 Browser"
        cabinet.header_lines_fr = ["FUE-G STUDIO ENTETE", "Chirurgien-dentiste"]
        cabinet.header_lines_ar = ["طبيب الاختبار", "طبيب جراح للأسنان"]
        cabinet.footer_address = "12 RUE TEST UNIQUEMENT — CABINET FICTIF"
        cabinet.footer_phones = "00 00 00 00 00 — SYNTHETIQUE"
        cabinet.qr_code_enabled = False
        cabinet.is_initialized = True
        db.commit()
        print("CEPH_A4_FUE_G_PREPARED_SYNTHETIC_REVISION_" + str(graph["revision"]))
    elif operation == "verify":
        from backend.services.cephalo_document_lock import verified_official_archive_bytes
        from backend.services import archive_service
        from backend.services.cephalo_a4_approval_v1 import VERSION
        import fitz
        rows = db.query(models.DocumentArchive).filter(
            models.DocumentArchive.patient_id == patient.id,
            models.DocumentArchive.analysis_id == study.id,
            models.DocumentArchive.document_type == models.DocumentType.RAPPORT_CEPHALO,
        ).all()
        assert len(rows) == 1, "FUE-G must persist exactly one archive"
        record = rows[0]
        assert record.file_hash and len(record.file_hash) == 64
        data = record.clinical_data
        assert data["document_kind"] == VERSION
        assert data["clinical_diagnosis_validated"] is False
        assert data["approved_by_practitioner_id"] == user.id
        assert data["rendered_identity_sha256"]
        assert data["scientific_source_sha256"]
        assert data["approved_pdf_sha256"] == record.file_hash
        # DocumentArchive has no author_practitioner_id column: the real
        # author is stored as uploaded_by_id and in the immutable approval
        # metadata. Both must match the authenticated dentist.
        assert record.uploaded_by_id == user.id
        assert db.query(models.AuditLog).filter(
            models.AuditLog.action == "CEPH_A4_DESCRIPTIVE_APPROVED",
            models.AuditLog.resource_id == str(study.id),
            models.AuditLog.user_id == user.id,
        ).count() == 1
        pdf = verified_official_archive_bytes(record, db)
        assert hashlib.sha256(pdf).hexdigest() == record.file_hash
        with fitz.open(stream=pdf, filetype="pdf") as report:
            page_text = "\n".join(p.get_text() for p in report)
            assert round(report[0].rect.width) == 595
            assert round(report[0].rect.height) == 842
        assert "FUE-G STUDIO ENTETE" in page_text
        assert "Dr. Nom Prénom" not in page_text
        assert "Votre adresse de cabinet" not in page_text
        assert "12 RUE TEST UNIQUEMENT" in page_text
        assert "DIAGNOSTIC FINAL" not in page_text
        assert "PLAN DE TRAITEMENT" not in page_text
        assert "BROUILLON" not in page_text
        assert record.file_size == len(pdf)
        print("CEPH_A4_FUE_G_SQLITE_AUTH_AUDIT_SHA_ARCHIVE_PASS")
    else:
        from backend.services import archive_service
        # Remove ONLY this disposable synthetic patient's files. CI-runner
        # archive directories and patient IDs must not survive a test run.
        import shutil
        root = archive_service.ARCHIVE_BASE_DIR.resolve()
        patient_root = (root / str(patient.id)).resolve()
        assert patient_root.is_relative_to(root) and patient_root != root
        if patient_root.is_dir() and not patient_root.is_symlink():
            shutil.rmtree(patient_root)
        journal = root / ".cephalo-pending" / str(patient.id)
        if journal.is_dir() and not journal.is_symlink():
            shutil.rmtree(journal)
        print("CEPH_A4_FUE_G_SYNTHETIC_FILES_CLEANED")
