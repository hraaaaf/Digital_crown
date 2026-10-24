"""LOT07 R2 — synthetic HTTP coverage for document W/X permission boundaries.

This is NOT a certification of a general per-slot MultiView W/X capability.
Test-created document rows have no physical PDFs; all attempted mutations are
expected to fail before touching files or changing records.
"""
from datetime import datetime

import pytest
from fastapi import HTTPException

from backend import models
from backend.routers.documents import require_document_permission
from backend.security import get_password_hash


def _actor(db, email, owner_id, permissions):
    actor = models.User(
        email=email,
        hashed_password=get_password_hash("SyntheticR2DocPass123!"),
        role="DENTISTE",
        nom_complet="Synthetic document actor",
        is_active=True,
        is_licensed=True,
        employer_id=owner_id,
        permissions=permissions,
    )
    db.add(actor)
    db.commit()
    db.refresh(actor)
    return actor


def _patient(db, employer_id, suffix):
    patient = models.Patient(
        numero_dossier=f"R2-DOC-{suffix}",
        nom="Synthetic",
        prenom="R2",
        date_naissance=datetime(2000, 1, 1),
        sexe="M",
        employer_id=employer_id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def _archived_row(db, patient, kind):
    # Mirror the archive service's mandatory SQL metadata without writing a PDF.
    # A missing document_group_id/file_hash/file_size aborts at INSERT before any
    # of the HTTP authorization assertions can execute.
    from hashlib import sha256

    synthetic_content = b"synthetic-r2-metadata-only"
    doc = models.DocumentArchive(
        patient_id=patient.id,
        document_type=kind,
        filename="r2-synthetic-unavailable.pdf",
        original_filename="r2-synthetic-unavailable.pdf",
        document_group_id=f"r2-{patient.id}-{kind.value.lower()}",
        file_hash=sha256(synthetic_content).hexdigest(),
        file_size=len(synthetic_content),
        file_path="nonexistent-synthetic-only/r2.pdf",
        title="Synthetic R2 document",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def _credentials(client, actor, password="SyntheticR2DocPass123!"):
    login = client.post(
        "/api/auth/login",
        data={"username": actor.email, "password": password},
    )
    assert login.status_code == 200, login.text
    jwt = login.json()["access_token"]
    client.cookies.delete("access_token")
    client.cookies.delete("refresh_token")
    return {"Authorization": f"Bearer {jwt}"}


def _mapped_read_only_actor(db, dentiste, suffix):
    return _actor(
        db, f"r2-doc-staff-{suffix}@example.test", dentiste.id,
        {"patients": True, "prescriptions": False, "clinical": False, "accounting": False},
    )


def test_r2_unmapped_document_type_is_denied_by_server_permission_function(db, dentiste):
    staff = _mapped_read_only_actor(db, dentiste, "unmapped")
    for document_kind in ("BILAN", "unsupported_future_kind", ""):
        with pytest.raises(HTTPException) as exc:
            require_document_permission(document_kind, staff)
        assert exc.value.status_code == 403


def test_r2_unmapped_bilan_is_hidden_and_all_document_actions_fail_closed(client, db, dentiste):
    patient = _patient(db, dentiste.id, "BILAN")
    doc = _archived_row(db, patient, models.DocumentType.BILAN)
    staff = _mapped_read_only_actor(db, dentiste, "bilan")
    headers = _credentials(client, staff)

    listing = client.get("/api/documents/", params={"patient_id": patient.id}, headers=headers)
    assert listing.status_code == 200, listing.text
    assert all(item["id"] != doc.id for item in listing.json()["documents"])
    patient_listing = client.get(f"/api/patients/{patient.id}/documents", headers=headers)
    assert patient_listing.status_code == 200, patient_listing.text
    assert all(str(item["id"]) != str(doc.id) for item in patient_listing.json())

    attempted = (
        client.get(f"/api/documents/{doc.id}/download", headers=headers),
        client.post(f"/api/documents/{doc.id}/trash", headers=headers),
        client.post(f"/api/documents/{doc.id}/restore", headers=headers),
        client.delete(f"/api/documents/{doc.id}", params={"confirm": "true"}, headers=headers),
        client.post(f"/api/documents/{doc.id}/sign", headers=headers),
    )
    assert [result.status_code for result in attempted] == [403] * len(attempted)
    db.refresh(doc)
    assert doc.status == models.DocumentStatus.ACTIF


def test_r2_document_mutations_require_the_actual_document_permission(client, db, dentiste):
    patient = _patient(db, dentiste.id, "DOCUMENT")
    doc = _archived_row(db, patient, models.DocumentType.ORDONNANCE)
    staff = _mapped_read_only_actor(db, dentiste, "mapped")
    headers = _credentials(client, staff)

    attempted = (
        client.get(f"/api/documents/{doc.id}/download", headers=headers),
        client.post(f"/api/documents/{doc.id}/trash", headers=headers),
        client.post(f"/api/documents/{doc.id}/restore", headers=headers),
        client.delete(f"/api/documents/{doc.id}", params={"confirm": "true"}, headers=headers),
        client.post(f"/api/documents/{doc.id}/sign", headers=headers),
    )
    assert [result.status_code for result in attempted] == [403] * len(attempted)
    db.refresh(doc)
    assert doc.status == models.DocumentStatus.ACTIF


def test_r2_cannot_access_or_mutate_cross_tenant_document_even_with_right_role(client, db, dentiste):
    other_owner = _actor(
        db, "r2-other-doc-owner@example.test", None,
        {"patients": True, "prescriptions": True, "clinical": True, "accounting": True},
    )
    patient = _patient(db, other_owner.id, "ALIEN")
    doc = _archived_row(db, patient, models.DocumentType.ORDONNANCE)
    headers = _credentials(client, dentiste, password="TestPass123!")

    read = client.get("/api/documents/", params={"patient_id": patient.id}, headers=headers)
    download = client.get(f"/api/documents/{doc.id}/download", headers=headers)
    trash = client.post(f"/api/documents/{doc.id}/trash", headers=headers)
    archive = client.post(
        "/api/documents/archive",
        params={"patient_id": patient.id, "doc_type": "ORDONNANCE"},
        headers=headers,
        files={"file": ("r2-no-real.pdf", b"%PDF-synthetic", "application/pdf")},
    )
    assert all(result.status_code in (403, 404) for result in (read, download, trash, archive))
    db.refresh(doc)
    assert doc.status == models.DocumentStatus.ACTIF
    assert db.query(models.DocumentArchive).count() == 1


def test_r2_revocation_of_prescription_permission_blocks_existing_document_jwt(client, db, dentiste):
    patient = _patient(db, dentiste.id, "REVOKE")
    doc = _archived_row(db, patient, models.DocumentType.ORDONNANCE)
    staff = _actor(
        db, "r2-doc-revocation@example.test", dentiste.id,
        {"patients": True, "prescriptions": True, "accounting": False},
    )
    headers = _credentials(client, staff)
    initial = client.get(
        "/api/documents/", params={"patient_id": patient.id, "doc_type": "ORDONNANCE"},
        headers=headers,
    )
    assert initial.status_code == 200, initial.text

    staff.permissions = {"patients": True, "prescriptions": False, "accounting": False}
    db.commit()
    db.expire_all()
    assert client.get(
        "/api/documents/", params={"patient_id": patient.id, "doc_type": "ORDONNANCE"},
        headers=headers,
    ).status_code == 403
    assert client.post(f"/api/documents/{doc.id}/trash", headers=headers).status_code == 403
    db.refresh(doc)
    assert doc.status == models.DocumentStatus.ACTIF


def test_r2_direct_generate_and_upload_refuse_unprivileged_document_writes(client, db, dentiste):
    patient = _patient(db, dentiste.id, "WRITE")
    staff = _mapped_read_only_actor(db, dentiste, "writes")
    headers = _credentials(client, staff)

    for doc_type in ("ordonnance", "devis", "libre"):
        generated = client.post(
            "/api/documents/generate",
            json={"type": doc_type, "patient_id": patient.id, "data": {}},
            headers=headers,
        )
        assert generated.status_code == 403, (doc_type, generated.status_code, generated.text)

    archived = client.post(
        "/api/documents/archive",
        params={"patient_id": patient.id, "doc_type": "ORDONNANCE"},
        headers=headers,
        files={"file": ("r2-no-real.pdf", b"%PDF-synthetic", "application/pdf")},
    )
    assert archived.status_code == 403, archived.text
    assert db.query(models.DocumentArchive).count() == 0


def test_r2_patient_document_route_never_leaks_financial_document_metadata(client, db, dentiste):
    patient = _patient(db, dentiste.id, "FINANCIAL")
    doc = _archived_row(db, patient, models.DocumentType.DEVIS)
    doc.clinical_data = {"synthetic_confidential_billing": "DO_NOT_EXPOSE"}
    db.commit()

    staff = _mapped_read_only_actor(db, dentiste, "financial")
    staff_headers = _credentials(client, staff)
    patient_list = client.get(f"/api/patients/{patient.id}/documents", headers=staff_headers)
    assert patient_list.status_code == 200, patient_list.text
    assert all(str(item["id"]) != str(doc.id) for item in patient_list.json())
    assert "DO_NOT_EXPOSE" not in patient_list.text

    archive_list = client.get("/api/documents/", params={"patient_id": patient.id}, headers=staff_headers)
    assert archive_list.status_code == 200, archive_list.text
    assert all(item["id"] != doc.id for item in archive_list.json()["documents"])
    assert client.get(f"/api/documents/{doc.id}/download", headers=staff_headers).status_code == 403

    # Positive oracle: the legitimate owner still sees the same existing row.
    owner_headers = _credentials(client, dentiste, password="TestPass123!")
    authorized_list = client.get(f"/api/patients/{patient.id}/documents", headers=owner_headers)
    assert authorized_list.status_code == 200, authorized_list.text
    assert any(str(item["id"]) == str(doc.id) for item in authorized_list.json())
