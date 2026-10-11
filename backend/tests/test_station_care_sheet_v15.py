from datetime import datetime, timedelta
from types import SimpleNamespace
import hashlib

from backend import models
from backend.models_patient_companion import PatientCompanionAccess, PatientCompanionIdentity
from backend.routers.patient_companion_common import create_patient_device_token
from backend.services.archive_service import ArchiveService
from backend.services.station_care_sheet import record_trusted_finalization, verified_care_sheet_bytes, is_finalized_care_sheet


def _login(client, email: str, password: str = "TestPass123!") -> dict[str, str]:
    response = client.post("/api/auth/login", data={"username": email, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    client.cookies.delete("access_token")
    client.cookies.delete("refresh_token")
    return {"Authorization": f"Bearer {token}"}


def _set_mode(client, headers: dict[str, str], mode: str) -> None:
    response = client.post(
        "/api/workstation/mode",
        headers=headers,
        json={"mode": mode, "ownerPin": "2468"},
    )
    assert response.status_code == 200, response.text


def _station(client, owner) -> dict[str, str]:
    headers = _login(client, owner.email)
    assert client.get("/api/workstation/state", headers=headers).status_code == 200
    assert client.post(
        "/api/workstation/owner-pin",
        headers=headers,
        json={"accountPassword": "TestPass123!", "newPin": "2468"},
    ).status_code == 200
    _set_mode(client, headers, "station")
    return headers


def _identified_session(client, db, owner, *, dossier: str = "ST043-001"):
    headers = _station(client, owner)
    created = client.post("/api/workstation/patient-session", headers=headers)
    assert created.status_code == 201, created.text
    session = created.json()
    raw = session["handoffUrl"].split("stationSession=", 1)[1]

    patient = models.Patient(
        numero_dossier=dossier,
        nom="Station",
        prenom="Care",
        date_naissance=datetime(1990, 1, 1),
        sexe="F",
        employer_id=owner.id,
    )
    db.add(patient)
    db.flush()
    identity = PatientCompanionIdentity(
        provider="local_bridge",
        subject=f"device:{dossier}",
        last_seen_at=datetime.utcnow(),
    )
    db.add(identity)
    db.flush()
    access = PatientCompanionAccess(
        identity_id=identity.id,
        employer_id=owner.id,
        patient_id=patient.id,
        relationship_type="SELF",
    )
    db.add(access)
    db.commit()
    db.refresh(access)

    patient_headers = {
        "Authorization": f"Bearer {create_patient_device_token(identity, access)}"
    }
    claimed = client.post(
        "/api/workstation/patient-session/claim",
        headers=patient_headers,
        json={"token": raw, "accessId": access.public_id},
    )
    assert claimed.status_code == 200, claimed.text
    return headers, session["sessionId"], patient


def _care_sheet(db, patient, *, status: str = "VALIDATED", emit_finalization_event: bool = True):
    pdf_content = b"%PDF-1.4\n% station care sheet\n%%EOF\n"
    rendered_hash = hashlib.sha256(pdf_content).hexdigest()
    document, _ = ArchiveService(db).archive_document(
        patient_id=patient.id,
        uploaded_by_id=patient.employer_id,
        file_content=pdf_content,
        filename=f"Feuille_soins_CNSS_{patient.id}.pdf",
        doc_type=models.DocumentType.AUTRE,
        title="Feuille de soins CNSS",
        tags=["insurance_submission", "cnss"],
        clinical_data={
            "kind": "INSURANCE_SUBMISSION",
            "schema_version": "1",
            "validated_by_practitioner_id": patient.employer_id,
            "validated_at": "2026-10-07T12:00:00",
            "draft": {"status": status},
            "render_evidence": {
                "renderer": "PDF_OVERLAY_V1",
                "rendered_pdf_sha256": rendered_hash,
            },
        },
        is_accounted=False,
        is_collected=False,
        payment_status=models.PaiementStatut.EN_ATTENTE,
    )
    if status == "VALIDATED" and emit_finalization_event:
        record_trusted_finalization(
            db, document, employer_id=patient.employer_id,
            practitioner_id=patient.employer_id,
            expected_patient_id=patient.id,
        )
    return document


def test_station_care_sheet_requires_explicit_withdrawal_authorization(client, db, dentiste):
    headers, session_id, patient = _identified_session(client, db, dentiste)
    document = _care_sheet(db, patient)

    denied = client.get(
        f"/api/workstation/patient-session/{session_id}/documents/care-sheet/{document.id}",
        headers=headers,
    )
    assert denied.status_code == 409
    assert denied.json()["detail"] == "STATION_CARE_SHEET_NOT_ELIGIBLE"

    _set_mode(client, headers, "cabinet")
    authorized = client.post(
        f"/api/workstation/documents/care-sheet/{document.id}/authorize-withdrawal",
        headers=headers,
    )
    assert authorized.status_code == 200, authorized.text
    assert authorized.json() == {
        "status": "AUTHORIZED",
        "documentId": document.id,
        "created": True,
    }
    _set_mode(client, headers, "station")

    downloaded = client.get(
        f"/api/workstation/patient-session/{session_id}/documents/care-sheet/{document.id}",
        headers=headers,
    )
    assert downloaded.status_code == 200, downloaded.text
    assert downloaded.headers["content-type"].startswith("application/pdf")
    assert downloaded.headers["cache-control"] == "no-store"
    assert downloaded.content.startswith(b"%PDF")

    actions = {
        row.action for row in db.query(models.AuditLog).filter(
            models.AuditLog.employer_id == dentiste.id,
            models.AuditLog.resource_type == "DocumentArchive",
            models.AuditLog.resource_id == str(document.id),
        ).all()
    }
    assert "STATION_CARE_SHEET_WITHDRAWAL_AUTHORIZED" in actions
    assert "STATION_CARE_SHEET_WITHDRAWN" in actions


def test_station_care_sheet_authorization_is_idempotent(client, db, dentiste):
    headers, _session_id, patient = _identified_session(
        client, db, dentiste, dossier="ST043-IDEMP"
    )
    document = _care_sheet(db, patient)

    _set_mode(client, headers, "cabinet")
    first = client.post(
        f"/api/workstation/documents/care-sheet/{document.id}/authorize-withdrawal",
        headers=headers,
    )
    second = client.post(
        f"/api/workstation/documents/care-sheet/{document.id}/authorize-withdrawal",
        headers=headers,
    )
    assert first.status_code == 200
    assert first.json()["created"] is True
    assert second.status_code == 200
    assert second.json()["created"] is False


def test_station_care_sheet_refuses_non_finalized_archive(client, db, dentiste):
    headers, _session_id, patient = _identified_session(
        client, db, dentiste, dossier="ST043-DRAFT"
    )
    document = _care_sheet(db, patient, status="READY_FOR_REVIEW")

    _set_mode(client, headers, "cabinet")
    denied = client.post(
        f"/api/workstation/documents/care-sheet/{document.id}/authorize-withdrawal",
        headers=headers,
    )
    assert denied.status_code == 409
    assert denied.json()["detail"] == "CARE_SHEET_NOT_FINALIZED"


def test_station_care_sheet_hides_other_patient_document(client, db, dentiste):
    headers, session_id, _patient = _identified_session(
        client, db, dentiste, dossier="ST043-A"
    )
    other = models.Patient(
        numero_dossier="ST043-B",
        nom="Other",
        prenom="Patient",
        date_naissance=datetime(1985, 2, 2),
        sexe="M",
        employer_id=dentiste.id,
    )
    db.add(other)
    db.commit()
    document = _care_sheet(db, other)

    _set_mode(client, headers, "cabinet")
    assert client.post(
        f"/api/workstation/documents/care-sheet/{document.id}/authorize-withdrawal",
        headers=headers,
    ).status_code == 200
    _set_mode(client, headers, "station")

    hidden = client.get(
        f"/api/workstation/patient-session/{session_id}/documents/care-sheet/{document.id}",
        headers=headers,
    )
    assert hidden.status_code == 404
    assert hidden.json()["detail"] == "STATION_CARE_SHEET_NOT_FOUND"


def test_station_care_sheet_authorization_is_invalidated_by_file_replacement(client, db, dentiste):
    headers, session_id, patient = _identified_session(
        client, db, dentiste, dossier="ST043-HASH"
    )
    document = _care_sheet(db, patient)

    _set_mode(client, headers, "cabinet")
    assert client.post(
        f"/api/workstation/documents/care-sheet/{document.id}/authorize-withdrawal",
        headers=headers,
    ).status_code == 200
    _set_mode(client, headers, "station")

    previous_hash = document.file_hash
    replaced_content = b"%PDF-1.4\n% replaced station care sheet\n%%EOF\n"
    replaced_hash = hashlib.sha256(replaced_content).hexdigest()
    replaced_clinical_data = dict(document.clinical_data)
    replaced_clinical_data["render_evidence"] = {
        **dict(replaced_clinical_data["render_evidence"]),
        "rendered_pdf_sha256": replaced_hash,
    }
    ArchiveService(db)._replace_document_in_place(
        document_id=document.id,
        patient_id=patient.id,
        file_content=replaced_content,
        filename=document.original_filename,
        doc_type=document.document_type,
        uploaded_by_id=document.uploaded_by_id,
        title=document.title,
        description=document.description,
        tags=document.tags or [],
        clinical_data=replaced_clinical_data,
        analysis_id=document.analysis_id,
        is_accounted=document.is_accounted,
        is_collected=document.is_collected,
        payment_status=document.payment_status,
    )
    db.refresh(document)
    assert document.file_hash != previous_hash

    denied = client.get(
        f"/api/workstation/patient-session/{session_id}/documents/care-sheet/{document.id}",
        headers=headers,
    )
    assert denied.status_code == 409
    assert denied.json()["detail"] == "STATION_CARE_SHEET_NOT_ELIGIBLE"

    _set_mode(client, headers, "cabinet")
    renewed = client.post(
        f"/api/workstation/documents/care-sheet/{document.id}/authorize-withdrawal",
        headers=headers,
    )
    assert renewed.status_code == 409
    assert renewed.json()["detail"] == "CARE_SHEET_NOT_FINALIZED"


def test_station_care_sheet_rejects_forged_validated_metadata_without_finalizer_hash(client, db, dentiste):
    headers, _session_id, patient = _identified_session(
        client, db, dentiste, dossier="ST043-FORGE"
    )
    document, _ = ArchiveService(db).archive_document(
        patient_id=patient.id,
        file_content=b"%PDF-1.4\n% forged metadata\n%%EOF\n",
        filename="Feuille_soins_forged.pdf",
        doc_type=models.DocumentType.AUTRE,
        title="Feuille de soins forged",
        clinical_data={
            "kind": "INSURANCE_SUBMISSION",
            "validated_by_practitioner_id": dentiste.id,
            "validated_at": "2026-10-07T12:00:00",
            "draft": {"status": "VALIDATED"},
        },
        is_accounted=False,
        is_collected=False,
        payment_status=models.PaiementStatut.EN_ATTENTE,
    )

    _set_mode(client, headers, "cabinet")
    denied = client.post(
        f"/api/workstation/documents/care-sheet/{document.id}/authorize-withdrawal",
        headers=headers,
    )
    assert denied.status_code == 409
    assert denied.json()["detail"] == "CARE_SHEET_NOT_FINALIZED"


def test_station_workstation_cannot_authorize_care_sheet_withdrawal(client, db, dentiste):
    headers, _session_id, patient = _identified_session(
        client, db, dentiste, dossier="ST043-BOUNDARY"
    )
    document = _care_sheet(db, patient)

    denied = client.post(
        f"/api/workstation/documents/care-sheet/{document.id}/authorize-withdrawal",
        headers=headers,
    )
    assert denied.status_code == 423
    assert denied.json()["detail"] == "STAFF_WORKSTATION_REQUIRED"

def test_station_care_sheet_rejects_metadata_that_matches_file_hash_without_trusted_finalizer_event(client, db, dentiste):
    headers, session_id, patient = _identified_session(client, db, dentiste, dossier="ST043-FAKE-EVIDENCE")
    document = _care_sheet(db, patient)
    db.query(models.AuditLog).filter(
        models.AuditLog.resource_type == "DocumentArchive",
        models.AuditLog.resource_id == str(document.id),
        models.AuditLog.action == "STATION_CARE_SHEET_TRUSTED_FINALIZATION_V1",
    ).delete(synchronize_session=False)
    db.commit()
    _set_mode(client, headers, "cabinet")
    denied = client.post(f"/api/workstation/documents/care-sheet/{document.id}/authorize-withdrawal", headers=headers)
    assert denied.status_code == 409
    assert denied.json()["detail"] == "CARE_SHEET_NOT_FINALIZED"


def test_station_care_sheet_refuses_pdf_disk_tampering_after_authorization(client, db, dentiste):
    headers, session_id, patient = _identified_session(client, db, dentiste, dossier="ST043-DISK-TAMPER")
    document = _care_sheet(db, patient)
    _set_mode(client, headers, "cabinet")
    assert client.post(f"/api/workstation/documents/care-sheet/{document.id}/authorize-withdrawal", headers=headers).status_code == 200
    _set_mode(client, headers, "station")
    file_path = ArchiveService(db)._resolve_archive_storage_path(document)
    original = file_path.read_bytes()
    altered = bytearray(original)
    altered[10] ^= 1
    file_path.write_bytes(bytes(altered))
    assert file_path.stat().st_size == document.file_size
    try:
        denied = client.get(f"/api/workstation/patient-session/{session_id}/documents/care-sheet/{document.id}", headers=headers)
        assert denied.status_code == 409
        assert denied.json()["detail"] == "STATION_CARE_SHEET_FILE_UNTRUSTED"
    finally:
        file_path.write_bytes(original)


def test_station_care_sheet_refuses_storage_traversal_after_authorization(client, db, dentiste):
    headers, session_id, patient = _identified_session(client, db, dentiste, dossier="ST043-TRAVERSAL")
    document = _care_sheet(db, patient)
    _set_mode(client, headers, "cabinet")
    assert client.post(f"/api/workstation/documents/care-sheet/{document.id}/authorize-withdrawal", headers=headers).status_code == 200
    _set_mode(client, headers, "station")
    original = document.file_path
    document.file_path = "static/archives/../../external.pdf"
    db.commit()
    try:
        denied = client.get(f"/api/workstation/patient-session/{session_id}/documents/care-sheet/{document.id}", headers=headers)
        assert denied.status_code == 409
        assert denied.json()["detail"] == "STATION_CARE_SHEET_FILE_UNTRUSTED"
    finally:
        document.file_path = original
        db.commit()


def test_station_care_sheet_verified_snapshot_equals_actual_response(client, db, dentiste):
    headers, session_id, patient = _identified_session(client, db, dentiste, dossier="ST043-EXACT-HASH")
    document = _care_sheet(db, patient)
    expected = verified_care_sheet_bytes(document)
    _set_mode(client, headers, "cabinet")
    assert client.post(f"/api/workstation/documents/care-sheet/{document.id}/authorize-withdrawal", headers=headers).status_code == 200
    _set_mode(client, headers, "station")
    delivered = client.get(f"/api/workstation/patient-session/{session_id}/documents/care-sheet/{document.id}", headers=headers)
    assert delivered.status_code == 200
    assert delivered.content == expected
    assert hashlib.sha256(delivered.content).hexdigest() == document.file_hash
    assert delivered.headers["x-content-type-options"] == "nosniff"

def test_station_care_sheet_rejects_symlinked_archive_even_to_same_pdf(client, db, dentiste):
    headers, session_id, patient = _identified_session(client, db, dentiste, dossier="ST043-SYMLINK")
    document = _care_sheet(db, patient)
    _set_mode(client, headers, "cabinet")
    assert client.post(f"/api/workstation/documents/care-sheet/{document.id}/authorize-withdrawal", headers=headers).status_code == 200
    _set_mode(client, headers, "station")
    archive_path = ArchiveService(db)._resolve_archive_storage_path(document)
    backup = archive_path.with_name(archive_path.name + ".test-original")
    archive_path.rename(backup)
    try:
        try:
            archive_path.symlink_to(backup)
        except (OSError, NotImplementedError):
            import pytest
            pytest.skip("Runner does not permit filesystem symlinks")
        denied = client.get(f"/api/workstation/patient-session/{session_id}/documents/care-sheet/{document.id}", headers=headers)
        assert denied.status_code == 409
        assert denied.json()["detail"] == "STATION_CARE_SHEET_FILE_UNTRUSTED"
    finally:
        if archive_path.is_symlink():
            archive_path.unlink()
        backup.rename(archive_path)


def test_care_sheet_expired_identified_session_fails_closed(client, db, dentiste):
    headers, session_id, patient = _identified_session(
        client, db, dentiste, dossier="ST043-EXPIRED"
    )
    document = _care_sheet(db, patient)
    _set_mode(client, headers, "cabinet")
    assert client.post(
        f"/api/workstation/documents/care-sheet/{document.id}/authorize-withdrawal",
        headers=headers,
    ).status_code == 200
    _set_mode(client, headers, "station")
    session = db.query(models.WorkstationPatientSession).filter(
        models.WorkstationPatientSession.id == session_id,
    ).one()
    session.expires_at = datetime.utcnow() - timedelta(seconds=1)
    db.commit()

    denied = client.get(
        f"/api/workstation/patient-session/{session_id}/documents/care-sheet/{document.id}",
        headers=headers,
    )
    assert denied.status_code == 409
    assert denied.json()["detail"] == "STATION_SESSION_INVALID_OR_USED"
    db.refresh(session)
    assert session.purged_at is not None
    assert session.patient_id is None


def test_care_sheet_previous_version_fails_closed_after_authorization(client, db, dentiste):
    headers, session_id, patient = _identified_session(
        client, db, dentiste, dossier="ST043-OLD-VERSION"
    )
    document = _care_sheet(db, patient)
    _set_mode(client, headers, "cabinet")
    assert client.post(
        f"/api/workstation/documents/care-sheet/{document.id}/authorize-withdrawal",
        headers=headers,
    ).status_code == 200
    document.is_latest_version = False
    db.commit()
    _set_mode(client, headers, "station")

    denied = client.get(
        f"/api/workstation/patient-session/{session_id}/documents/care-sheet/{document.id}",
        headers=headers,
    )
    assert denied.status_code == 409
    assert denied.json()["detail"] == "STATION_CARE_SHEET_NOT_ELIGIBLE"


def test_official_finalize_route_records_provenance_before_authorization(
    client, db, dentiste, monkeypatch,
):
    """Route-wiring regression: do not mistake a mocked renderer for a full rendering E2E."""
    headers, session_id, patient = _identified_session(
        client, db, dentiste, dossier="ST043-OFFICIAL-ROUTE"
    )
    document = _care_sheet(db, patient, emit_finalization_event=False)
    assert not is_finalized_care_sheet(db, document, employer_id=dentiste.id)
    _set_mode(client, headers, "cabinet")

    monkeypatch.setattr(
        "backend.routers.insurance_submissions._template_config_for",
        lambda organization: (SimpleNamespace(version="CNSS-610-1-04"), "a" * 64, None),
    )
    monkeypatch.setattr(
        "backend.routers.insurance_submissions.finalize_insurance_submission_pdf",
        lambda *args, **kwargs: (document, False, b"%PDF-1.4\\nfixture\\n%%EOF\\n"),
    )
    draft = {
        "patient_id": patient.id,
        "organization": "CNSS",
        "honoraires_document_id": 42,
        "lines": [{
            "source": {"honoraires_document_id": 42, "honoraires_line_index": 0},
            "service_date": "2026-09-14",
            "label": "Detartrage",
            "amount_mad": 500.0,
            "mapping_status": "EXACT",
            "ngap_code": "D1",
            "ngap_coefficient": 10.0,
            "mapping_rule_id": "ngap-test:d1",
        }],
        "status": "VALIDATED",
        "template": {
            "template_version": "CNSS-610-1-04",
            "template_hash": "a" * 64,
            "source_url": "cabinet://validated/CNSS-610-1-04.pdf",
            "trust": "CABINET_VALIDATED_BINARY",
        },
        "reference": {"ngap_reference_version": "ngap-test", "ngap_reference_hash": "b" * 64},
        "validated_by_practitioner_id": dentiste.id,
        "validated_at": "2026-10-11T08:00:00",
    }
    finalized = client.post(
        "/api/documents/insurance-submissions/finalize",
        headers=headers,
        json=draft,
    )
    assert finalized.status_code == 200, finalized.text
    assert finalized.json()["document_id"] == document.id
    assert is_finalized_care_sheet(db, document, employer_id=dentiste.id)
    assert client.post(
        f"/api/workstation/documents/care-sheet/{document.id}/authorize-withdrawal",
        headers=headers,
    ).status_code == 200
    _set_mode(client, headers, "station")
    retrieved = client.get(
        f"/api/workstation/patient-session/{session_id}/documents/care-sheet/{document.id}",
        headers=headers,
    )
    assert retrieved.status_code == 200
    assert hashlib.sha256(retrieved.content).hexdigest() == document.file_hash


def test_official_finalize_api_records_request_bound_provenance(client, db, dentiste, monkeypatch):
    """Exercise the actual HTTP finalize route; canonical renderer is stubbed here."""
    from types import SimpleNamespace

    from backend.tests.test_insurance_finalization import _validated_draft

    headers, session_id, patient = _identified_session(
        client, db, dentiste, dossier="ST043-FINALIZE-ROUTE"
    )
    document = _care_sheet(db, patient)
    db.query(models.AuditLog).filter(
        models.AuditLog.action == "STATION_CARE_SHEET_TRUSTED_FINALIZATION_V1",
        models.AuditLog.resource_type == "DocumentArchive",
        models.AuditLog.resource_id == str(document.id),
    ).delete(synchronize_session=False)
    db.commit()

    draft = _validated_draft("a" * 64).model_copy(update={
        "patient_id": patient.id,
        "validated_by_practitioner_id": dentiste.id,
    })
    monkeypatch.setattr(
        "backend.routers.insurance_submissions._template_config_for",
        lambda _organization: (SimpleNamespace(version=draft.template.template_version), draft.template.template_hash, None),
    )

    def verified_service_stub(_db, **kwargs):
        assert kwargs["draft"].patient_id == patient.id
        assert kwargs["uploaded_by_id"] == dentiste.id
        return document, False, b"%PDF-1.4\\n%%EOF\\n"

    monkeypatch.setattr(
        "backend.routers.insurance_submissions.finalize_insurance_submission_pdf",
        verified_service_stub,
    )

    _set_mode(client, headers, "cabinet")
    finalized = client.post(
        "/api/documents/insurance-submissions/finalize",
        headers=headers, json=draft.model_dump(mode="json"),
    )
    assert finalized.status_code == 200, finalized.text
    assert finalized.json()["document_id"] == document.id

    provenance = db.query(models.AuditLog).filter(
        models.AuditLog.action == "STATION_CARE_SHEET_TRUSTED_FINALIZATION_V1",
        models.AuditLog.resource_type == "DocumentArchive",
        models.AuditLog.resource_id == str(document.id),
    ).all()
    assert len(provenance) == 1
    assert provenance[0].user_id == dentiste.id
    assert f"patient_id={patient.id};sha256={document.file_hash}" in provenance[0].details
    authorized = client.post(
        f"/api/workstation/documents/care-sheet/{document.id}/authorize-withdrawal",
        headers=headers,
    )
    assert authorized.status_code == 200, authorized.text
    _set_mode(client, headers, "station")
    delivered = client.get(
        f"/api/workstation/patient-session/{session_id}/documents/care-sheet/{document.id}",
        headers=headers,
    )
    assert delivered.status_code == 200, delivered.text
    assert hashlib.sha256(delivered.content).hexdigest() == document.file_hash


def test_official_finalize_api_rejects_mismatched_patient_archive(client, db, dentiste, monkeypatch):
    """A service contract regression cannot authorize a different patient's PDF."""
    from types import SimpleNamespace

    from backend.tests.test_insurance_finalization import _validated_draft

    headers, _session_id, patient = _identified_session(
        client, db, dentiste, dossier="ST043-REQUEST-PATIENT"
    )
    other = models.Patient(
        numero_dossier="ST043-RETURNED-OTHER", nom="Other", prenom="Patient",
        date_naissance=datetime(1980, 1, 1), sexe="F", employer_id=dentiste.id,
    )
    db.add(other)
    db.commit()
    foreign_document = _care_sheet(db, other, status="READY_FOR_REVIEW")

    draft = _validated_draft("a" * 64).model_copy(update={
        "patient_id": patient.id,
        "validated_by_practitioner_id": dentiste.id,
    })
    monkeypatch.setattr(
        "backend.routers.insurance_submissions._template_config_for",
        lambda _organization: (SimpleNamespace(version=draft.template.template_version), draft.template.template_hash, None),
    )
    monkeypatch.setattr(
        "backend.routers.insurance_submissions.finalize_insurance_submission_pdf",
        lambda _db, **_kwargs: (foreign_document, False, b"%PDF-1.4\\n%%EOF\\n"),
    )

    _set_mode(client, headers, "cabinet")
    response = client.post(
        "/api/documents/insurance-submissions/finalize",
        headers=headers, json=draft.model_dump(mode="json"),
    )
    assert response.status_code == 422, response.text
    assert response.json()["detail"] == "CARE_SHEET_FINALIZATION_SOURCE_MISMATCH"
    assert db.query(models.AuditLog).filter(
        models.AuditLog.action == "STATION_CARE_SHEET_TRUSTED_FINALIZATION_V1",
        models.AuditLog.resource_type == "DocumentArchive",
        models.AuditLog.resource_id == str(foreign_document.id),
    ).count() == 0
