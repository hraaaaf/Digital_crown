from __future__ import annotations

import base64
import hashlib
import uuid
from datetime import datetime, timedelta
from io import BytesIO

from PIL import Image, ImageDraw

from backend import models
from backend.models_patient_companion import (
    PatientCompanionAccess,
    PatientCompanionConsentEvidence,
    PatientCompanionConsentRequest,
    PatientCompanionIdentity,
    PatientCompanionShareGrant,
)
from backend.routers.patient_companion_consents import (
    ConsentCreateRequest,
    create_patient_consent,
    revoke_patient_consent,
)
from backend.services.patient_companion_consents import handle_consent_sign


def _signature_data_url() -> str:
    image = Image.new("RGBA", (360, 210), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    draw.line([(40, 130), (120, 70), (180, 135), (310, 80)], fill=(30, 27, 75, 255), width=6)
    output = BytesIO()
    image.save(output, format="PNG")
    return "data:image/png;base64," + base64.b64encode(output.getvalue()).decode()


def _context(db, dentiste, tmp_path):
    patient = models.Patient(
        numero_dossier=f"PC04-{uuid.uuid4().hex[:8]}",
        nom="Consent",
        prenom="Aya",
        date_naissance=datetime(2010, 1, 1),
        sexe="F",
        employer_id=dentiste.id,
    )
    identity = PatientCompanionIdentity(provider="local_bridge", subject=f"device:{uuid.uuid4()}")
    db.add_all([patient, identity])
    db.flush()
    access = PatientCompanionAccess(
        identity_id=identity.id,
        employer_id=dentiste.id,
        patient_id=patient.id,
        relationship_type="SELF",
    )
    db.add(access)
    db.flush()

    pdf_bytes = b"%PDF-1.4\nPC04 consent fixture\n%%EOF\n"
    pdf_path = tmp_path / "consent.pdf"
    pdf_path.write_bytes(pdf_bytes)
    document = models.DocumentArchive(
        patient_id=patient.id,
        uploaded_by_id=dentiste.id,
        document_type=models.DocumentType.DOCUMENT_LIBRE,
        filename="consent.pdf",
        original_filename="consent.pdf",
        document_group_id=uuid.uuid4().hex,
        version_number=1,
        is_latest_version=True,
        file_hash=hashlib.sha256(pdf_bytes).hexdigest(),
        file_size=len(pdf_bytes),
        file_path=str(pdf_path),
        title="Consentement traitement",
        status=models.DocumentStatus.ACTIF,
    )
    db.add(document)
    db.flush()
    share = PatientCompanionShareGrant(
        employer_id=dentiste.id,
        patient_id=patient.id,
        resource_type="document",
        resource_id=document.id,
        granted_by_user_id=dentiste.id,
    )
    db.add(share)
    db.commit()
    db.refresh(document)
    db.refresh(share)
    db.refresh(access)
    return patient, identity, access, document, share


def test_pc04_consent_is_bound_to_shared_exact_document_and_creates_detached_evidence(db, dentiste, tmp_path):
    patient, _identity, access, document, _share = _context(db, dentiste, tmp_path)
    created = create_patient_consent(
        patient_id=patient.id,
        body=ConsentCreateRequest(document_id=document.id),
        db=db,
        current_user=dentiste,
    )
    assert created["status"] == "PENDING"
    assert created["document_version"] == 1

    result = handle_consent_sign(
        db,
        access,
        {"consent_id": created["consent_id"], "signature_base64": _signature_data_url()},
    )
    assert result.status == "ACCEPTED"
    assert result.response["status"] == "SIGNED"
    assert result.response["qualified_electronic_signature"] is False
    db.commit()

    evidence = db.query(PatientCompanionConsentEvidence).one()
    assert evidence.patient_id == patient.id
    assert evidence.access_id == access.id
    assert evidence.signature_png.startswith(b"\x89PNG")
    assert evidence.signature_sha256 == hashlib.sha256(evidence.signature_png).hexdigest()
    assert evidence.signature_size == len(evidence.signature_png)

    db.refresh(document)
    assert document.file_hash == hashlib.sha256(document.file_path and open(document.file_path, "rb").read()).hexdigest()


def test_pc04_refuses_changed_document_version_and_revoked_share(db, dentiste, tmp_path):
    patient, _identity, access, document, share = _context(db, dentiste, tmp_path)
    created = create_patient_consent(
        patient_id=patient.id,
        body=ConsentCreateRequest(document_id=document.id),
        db=db,
        current_user=dentiste,
    )

    document.version_number = 2
    db.commit()
    changed = handle_consent_sign(
        db,
        access,
        {"consent_id": created["consent_id"], "signature_base64": _signature_data_url()},
    )
    assert changed.status == "REJECTED"
    assert changed.response["code"] == "DOCUMENT_VERSION_CHANGED"

    document.version_number = 1
    share.revoked_at = datetime.utcnow()
    db.commit()
    revoked = handle_consent_sign(
        db,
        access,
        {"consent_id": created["consent_id"], "signature_base64": _signature_data_url()},
    )
    assert revoked.status == "REJECTED"
    assert revoked.response["code"] == "DOCUMENT_NOT_SHARED"


def test_pc04_second_distinct_sign_command_never_replaces_existing_evidence(db, dentiste, tmp_path):
    patient, _identity, access, document, _share = _context(db, dentiste, tmp_path)
    created = create_patient_consent(
        patient_id=patient.id,
        body=ConsentCreateRequest(document_id=document.id),
        db=db,
        current_user=dentiste,
    )
    first = handle_consent_sign(
        db,
        access,
        {"consent_id": created["consent_id"], "signature_base64": _signature_data_url()},
    )
    assert first.status == "ACCEPTED"
    db.commit()
    evidence = db.query(PatientCompanionConsentEvidence).one()
    first_hash = evidence.signature_sha256
    first_signed_at = evidence.signed_at

    second = handle_consent_sign(
        db,
        access,
        {"consent_id": created["consent_id"], "signature_base64": _signature_data_url()},
    )
    assert second.status == "REJECTED"
    assert second.response["code"] == "ALREADY_SIGNED"
    db.refresh(evidence)
    assert evidence.signature_sha256 == first_hash
    assert evidence.signed_at == first_signed_at


def test_pc04_reissue_preserves_revoked_request_history(db, dentiste, tmp_path):
    patient, _identity, _access, document, _share = _context(db, dentiste, tmp_path)
    first = create_patient_consent(
        patient_id=patient.id,
        body=ConsentCreateRequest(document_id=document.id),
        db=db,
        current_user=dentiste,
    )
    revoked = revoke_patient_consent(
        patient_id=patient.id,
        consent_id=first["consent_id"],
        db=db,
        current_user=dentiste,
    )
    assert revoked["status"] == "REVOKED"

    second = create_patient_consent(
        patient_id=patient.id,
        body=ConsentCreateRequest(document_id=document.id),
        db=db,
        current_user=dentiste,
    )
    assert second["consent_id"] != first["consent_id"]
    rows = db.query(PatientCompanionConsentRequest).order_by(PatientCompanionConsentRequest.created_at.asc()).all()
    assert len(rows) == 2
    assert rows[0].public_id == first["consent_id"]
    assert rows[0].status == "REVOKED"
    assert rows[0].revoked_at is not None
    assert rows[1].public_id == second["consent_id"]
    assert rows[1].status == "PENDING"


def test_pc04_rejects_non_pdf_document_even_when_hash_integrity_matches(db, dentiste, tmp_path):
    patient, _identity, _access, document, _share = _context(db, dentiste, tmp_path)
    raw = b"not-a-pdf"
    with open(document.file_path, "wb") as handle:
        handle.write(raw)
    document.file_hash = hashlib.sha256(raw).hexdigest()
    document.file_size = len(raw)
    db.commit()

    import pytest
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        create_patient_consent(
            patient_id=patient.id,
            body=ConsentCreateRequest(document_id=document.id),
            db=db,
            current_user=dentiste,
        )
    assert exc.value.status_code == 409
    assert "PDF" in str(exc.value.detail)


def test_pc04_invalid_signature_is_encrypted_domain_rejection_not_exception(db, dentiste, tmp_path):
    patient, _identity, access, document, _share = _context(db, dentiste, tmp_path)
    created = create_patient_consent(
        patient_id=patient.id,
        body=ConsentCreateRequest(document_id=document.id),
        db=db,
        current_user=dentiste,
    )
    result = handle_consent_sign(
        db,
        access,
        {"consent_id": created["consent_id"], "signature_base64": "data:image/png;base64,***"},
    )
    assert result.status == "REJECTED"
    assert result.response["code"] == "INVALID_SIGNATURE"
    assert db.query(PatientCompanionConsentEvidence).count() == 0


def test_pc04_consent_handler_rejects_extra_payload_fields(db, dentiste, tmp_path):
    patient, _identity, access, document, _share = _context(db, dentiste, tmp_path)
    created = create_patient_consent(
        patient_id=patient.id,
        body=ConsentCreateRequest(document_id=document.id),
        db=db,
        current_user=dentiste,
    )
    result = handle_consent_sign(
        db,
        access,
        {
            "consent_id": created["consent_id"],
            "signature_base64": _signature_data_url(),
            "patient_id": patient.id,
        },
    )
    assert result.status == "REJECTED"
    assert result.response["code"] == "INVALID_REQUEST"
