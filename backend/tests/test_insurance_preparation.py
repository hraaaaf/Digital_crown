import uuid

import pytest
from sqlalchemy.orm.attributes import flag_modified

from backend import models
from backend.schemas.insurance_submission import (
    InsuranceDraftStatus,
    InsuranceOrganization,
)
from backend.services.insurance_preparation import prepare_insurance_draft_from_honoraires
from backend.services.insurance_template_registry import (
    CNOPS_DENTAL_PENDING,
    LockedInsuranceTemplate,
)


def _make_patient(client, auth_headers, *, name="PREP", assurance="CNSS"):
    response = client.post(
        "/api/patients/",
        json={
            "nom": name,
            "prenom": "Insurance",
            "date_naissance": "1990-01-01",
            "sexe": "M",
            "telephone": "0612345678",
            "assurance": assurance,
        },
        headers=auth_headers,
    )
    assert response.status_code in (200, 201), response.text
    return response.json()["id"]


def _generate_honoraires(client, auth_headers, patient_id):
    response = client.post(
        "/api/documents/generate",
        json={
            "type": "note",
            "patient_id": patient_id,
            "is_accounted": True,
            "payment_status": "EN_ATTENTE",
            "data": {
                "payments": [{
                    "date": "2026-09-14",
                    "acte": "Detartrage",
                    "dent": "11",
                    "montant": 500.0,
                }],
                "doc_date": "2026-09-14",
                "teeth_data": [],
            },
        },
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text


def _document(db, patient_id):
    return db.query(models.DocumentArchive).filter(
        models.DocumentArchive.patient_id == patient_id,
        models.DocumentArchive.document_type == models.DocumentType.NOTE_HONORAIRES,
    ).one()


def test_prepare_cnss_draft_from_real_archived_honoraires(client, auth_headers, db, dentiste):
    patient_id = _make_patient(client, auth_headers)
    dentiste.nom_complet = "Dr Preparation"
    dentiste.identifiants_legaux = {"inpe": "INPE-777"}
    db.commit()
    _generate_honoraires(client, auth_headers, patient_id)
    document = _document(db, patient_id)

    draft = prepare_insurance_draft_from_honoraires(
        db,
        honoraires_document_id=document.id,
        organization=InsuranceOrganization.CNSS,
    )

    assert draft.patient_id == patient_id
    assert draft.organization == InsuranceOrganization.CNSS
    assert draft.lines[0].source.source_line_uid
    assert draft.lines[0].source.acte_id is not None
    assert draft.lines[0].teeth == ["11"]
    assert draft.template.template_version == "CNSS-610-1-04"
    assert draft.template.template_hash is None
    assert draft.template.trust is None
    assert draft.administrative.beneficiary_full_name == "Insurance PREP"
    assert draft.administrative.practitioner_full_name == "Dr Preparation"
    assert draft.administrative.practitioner_inpe == "INPE-777"
    assert draft.administrative.insured_registration_number is None
    assert "administrative.insured_registration_number" not in draft.unresolved_fields
    assert "administrative.beneficiary_national_id" in draft.unresolved_fields
    assert draft.status == InsuranceDraftStatus.INCOMPLETE


def test_prepare_rejects_patient_insurer_mismatch(client, auth_headers, db):
    patient_id = _make_patient(client, auth_headers, name="MISMATCH", assurance="CNOPS")
    _generate_honoraires(client, auth_headers, patient_id)
    document = _document(db, patient_id)

    with pytest.raises(ValueError, match="does not match"):
        prepare_insurance_draft_from_honoraires(
            db,
            honoraires_document_id=document.id,
            organization=InsuranceOrganization.CNSS,
        )


def test_prepare_rejects_locked_template_from_other_organization(client, auth_headers, db):
    patient_id = _make_patient(client, auth_headers, name="TEMPLATE")
    _generate_honoraires(client, auth_headers, patient_id)
    document = _document(db, patient_id)
    wrong = LockedInsuranceTemplate(
        definition=CNOPS_DENTAL_PENDING,
        source_url="cabinet://reference/cnops.pdf",
        sha256="a" * 64,
        page_count=2,
    )

    with pytest.raises(ValueError, match="organization mismatch"):
        prepare_insurance_draft_from_honoraires(
            db,
            honoraires_document_id=document.id,
            organization=InsuranceOrganization.CNSS,
            locked_template=wrong,
        )


def test_prepare_rejects_uid_linkage_mismatch(client, auth_headers, db):
    patient_id = _make_patient(client, auth_headers, name="UIDBAD")
    _generate_honoraires(client, auth_headers, patient_id)
    document = _document(db, patient_id)
    snapshot = dict(document.clinical_data or {})
    payments = [dict(item) for item in snapshot["payments"]]
    payments[0]["source_line_uid"] = str(uuid.uuid4())
    snapshot["payments"] = payments
    document.clinical_data = snapshot
    flag_modified(document, "clinical_data")
    db.flush()

    with pytest.raises(ValueError, match="UID linkage mismatch"):
        prepare_insurance_draft_from_honoraires(
            db,
            honoraires_document_id=document.id,
            organization=InsuranceOrganization.CNSS,
        )
