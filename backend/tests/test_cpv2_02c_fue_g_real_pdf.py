"""FUE-G: real PDF generation, paired session and in-memory cabinet DB. No PDF mocks."""
from __future__ import annotations
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
import fitz
from backend import models
from backend.routers.mobile import _create_mobile_jwt
# Registers the opt-in receipt schema for this isolated SQLite fixture only.
from backend.services.mobile_document_archive_receipts import MobileDocumentArchiveReceipt
from backend.security import get_password_hash

def paired(db, user):
    device = str(uuid.uuid4())
    db.add(models.MobilePairedDevice(
        device_id=device, user_id=user.id, employer_id=user.get_employer_id(),
        client_public_key_hex="04" + "11" * 64,
        refresh_jti="fue-g-" + uuid.uuid4().hex))
    db.commit()
    role = user.role.value if hasattr(user.role, "value") else str(user.role)
    return _create_mobile_jwt(user.id, role, user.get_employer_id(), device), device

def render_pdf(content, path):
    assert content.startswith(b"%PDF-")
    with fitz.open(stream=content, filetype="pdf") as pdf:
        assert pdf.page_count > 0
        page = pdf[0]
        assert page.get_text().strip()
        # Header must be the configured clinician, not a sample placeholder.
        header = ' '.join(str(block[4]) for block in page.get_text('blocks') if block[1] < 110)
        assert 'Dr Test FUE-G' in header, header
        assert 'Nom Prénom' not in page.get_text()
        pix = page.get_pixmap(matrix=fitz.Matrix(1.75, 1.75), alpha=False)
        pix.save(str(path))
        return {"pages": pdf.page_count, "width": pix.width, "height": pix.height}

def test_fue_g_real_preview_archive_isolated(client, db, dentiste, tmp_path, monkeypatch):
    from backend.routers import documents
    from backend.services import archive_service
    from backend.services.document_factory import DocumentFactory
    assert os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") == "true"
    assert os.environ.get("DATABASE_URL") == "sqlite:///:memory:"
    assert os.environ.get("ENVIRONMENT") == "test"
    # Dedicated FUE-G uploads to the configured artifact directory; the full
    # regression suite uses a disposable test directory without that CI env var.
    output = Path(os.environ.get("CPV2_FUE_G_ARTIFACT_DIR") or (tmp_path / "fue-g-artifacts"))
    output.mkdir(parents=True, exist_ok=True)
    media = tmp_path / "fue-g-media"
    media.mkdir()
    monkeypatch.setattr(documents, "MEDIA_DIR", media)
    monkeypatch.setattr(documents, "DOCS_DIR", str(media / "documents"))
    monkeypatch.setattr(documents, "doc_factory", DocumentFactory(
        output_dir=str(media / "documents"), static_dir=str(media)))
    monkeypatch.setattr(archive_service, "MEDIA_DIR", media)
    monkeypatch.setattr(archive_service, "ARCHIVE_BASE_DIR", media / "archives")
    monkeypatch.setattr(archive_service, "LEGACY_DOCS_DIR", media / "documents")
    dentiste.nom_complet = "Dr Test FUE-G"
    db.add(models.CabinetConfig(
        owner_id=dentiste.id, nom_cabinet="Cabinet Fictif FUE-G",
        nom_praticien="Dr Test FUE-G", nom_praticien_ar=""))
    patient = models.Patient(
        nom="FUEG", prenom="Fictif", date_naissance=datetime(1991, 5, 10),
        sexe="M", employer_id=dentiste.id)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    token, device_id = paired(db, dentiste)
    auth = {"Authorization": "Bearer " + token}
    intent_key = str(uuid.uuid4())
    archive_auth = {**auth, "Idempotency-Key": intent_key}
    payload = {"patient_id": patient.id, "type": "certificat",
               "data": {"reason": "Certificat de Présence", "doc_date": "2026-11-06"}}
    records = []
    def passed(label, status, **evidence):
        records.append({"case": label, "passed": True, "status": status, **evidence})

    no_auth = client.post("/api/mobile/documents/preview", json=payload)
    assert no_auth.status_code == 422, no_auth.text
    assert any(item.get("loc") == ["header", "authorization"]
               for item in no_auth.json().get("detail", [])), no_auth.text
    invalid_bearer = client.post("/api/mobile/documents/preview",
                                 headers={"Authorization": "Bearer invalid-pocket-token"},
                                 json=payload)
    assert invalid_bearer.status_code == 401, invalid_bearer.text
    passed("no_token_denied", no_auth.status_code,
           invalid_bearer_status=invalid_bearer.status_code)
    before = db.query(models.DocumentArchive).count()
    preview = client.post("/api/mobile/documents/preview", headers=auth, json=payload)
    assert preview.status_code == 200, preview.text
    assert preview.headers["content-type"].startswith("application/pdf")
    assert preview.headers["cache-control"] == "no-store, private"
    assert preview.headers["x-content-type-options"] == "nosniff"
    assert db.query(models.DocumentArchive).count() == before
    passed("real_preview_no_archive_row", 200, pdf_bytes=len(preview.content))
    passed("real_preview_pdf_rendered", 200,
           **render_pdf(preview.content, output / "01-real-pdf-preview.png"))

    outsider = models.User(
        email="fueg-" + uuid.uuid4().hex[:8] + "@example.invalid",
        hashed_password=get_password_hash("test-isolated-only"),
        role=models.UserRole.DENTISTE, is_active=True, is_licensed=True,
        approval_status="approved")
    db.add(outsider)
    db.commit()
    foreign = models.Patient(
        nom="FOREIGN", prenom="Fictif", date_naissance=datetime(1990, 1, 1),
        sexe="F", employer_id=outsider.id)
    db.add(foreign)
    db.commit()
    other = client.post("/api/mobile/documents/preview", headers=auth,
                        json={**payload, "patient_id": foreign.id})
    assert other.status_code == 404, other.text
    assert db.query(models.DocumentArchive).count() == before
    passed("cross_tenant_patient_denied", 404)

    assistant = models.User(
        email="fueg-assistant-" + uuid.uuid4().hex[:8] + "@example.invalid",
        hashed_password=get_password_hash("test-isolated-only"),
        role=models.UserRole.SECRETAIRE, employer_id=dentiste.id,
        permissions={"patients": False, "agenda": True},
        is_active=True, is_licensed=False, approval_status="approved")
    db.add(assistant)
    db.commit()
    assistant_token, _ = paired(db, assistant)
    lack = client.post("/api/mobile/documents/preview",
                       headers={"Authorization": "Bearer " + assistant_token},
                       json=payload)
    assert lack.status_code == 403, lack.text
    passed("no_patient_grant_denied", 403)

    note = client.post("/api/mobile/documents/archive", headers=archive_auth,
                       json={**payload, "type": "note", "data": {
                           "payments": [{"acte": "Acte fictif FUE-G", "montant": 100,
                                         "date": "2026-11-06"}],
                           "doc_date": "2026-11-06", "teeth_data": [],
                           "installments": [], "is_global_note": False}})
    assert note.status_code == 403, note.text
    passed("honoraires_archive_denied", 403)
    paid = client.post("/api/mobile/documents/archive", headers=archive_auth,
                       json={**payload, "payment_status": "PAYE"})
    assert paid.status_code == 403, paid.text
    assert db.query(models.DocumentArchive).count() == before
    passed("payment_mutation_denied", 403)

    archive = client.post("/api/mobile/documents/archive", headers=archive_auth, json=payload)
    assert archive.status_code == 200, archive.text
    assert archive.headers["content-type"].startswith("application/pdf")
    assert archive.headers["cache-control"] == "no-store, private"
    doc_id = int(archive.headers["x-document-id"])
    row = db.query(models.DocumentArchive).filter_by(id=doc_id).one()
    assert row.patient_id == patient.id and row.uploaded_by_id == dentiste.id
    assert row.status == models.DocumentStatus.ACTIF
    assert row.file_path.startswith("static/archives/")
    file = media / row.file_path[len("static/"):]
    assert file.is_file() and file.read_bytes() == archive.content
    assert db.query(models.DocumentArchive).count() == before + 1
    replay = client.post("/api/mobile/documents/archive", headers=archive_auth, json=payload)
    assert replay.status_code == 200, replay.text
    assert replay.content == archive.content
    assert replay.headers["x-document-id"] == str(doc_id)
    assert replay.headers["x-idempotent-replay"] == "true"
    mismatched = client.post(
        "/api/mobile/documents/archive", headers=archive_auth,
        json={**payload, "data": {**payload["data"], "reason": "Different document"}},
    )
    assert mismatched.status_code == 409, mismatched.text
    assert db.query(models.DocumentArchive).count() == before + 1
    recovered = client.get(f"/api/mobile/documents/archive/receipt/{intent_key}", headers=auth)
    assert recovered.status_code == 200, recovered.text
    assert recovered.content == archive.content
    assert db.query(models.DocumentArchive).count() == before + 1
    passed("real_archive_db_and_pdf_bytes_verified", 200, id=doc_id,
           pdf_bytes=len(archive.content))
    passed("real_archived_pdf_rendered", 200,
           **render_pdf(archive.content, output / "02-real-pdf-archived.png"))

    device = db.query(models.MobilePairedDevice).filter_by(device_id=device_id).one()
    device.revoked_at = datetime.utcnow()
    db.commit()
    revoked = client.post("/api/mobile/documents/archive", headers=archive_auth, json=payload)
    assert revoked.status_code == 401, revoked.text
    revoked_get = client.get(f"/api/mobile/documents/archive/receipt/{intent_key}", headers=auth)
    assert revoked_get.status_code == 401, revoked_get.text
    assert db.query(models.DocumentArchive).count() == before + 1
    passed("revoked_paired_device_denied", 401)

    assert len(records) == 10
    data = {"head": os.environ.get("CPV2_FUE_G_SHA", "full-regression-unscoped"), "type": "FUE-G",
            "backend": "actual FastAPI TestClient + ReportLab generator, no PDF mocks",
            "database": "isolated SQLite in-memory; synthetic identities only",
            "cases": records, "all_passed": True,
            "screenshots": ["01-real-pdf-preview.png", "02-real-pdf-archived.png"]}
    (output / "fue-g-evidence.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("FUE-G ACTUAL PDF + ISOLATED DB: 10/10 PASS")
