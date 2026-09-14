import pytest

from backend import models
from backend.schemas.insurance_submission import InsuranceOrganization
from backend.services.insurance_consistency import assert_draft_matches_honoraires_source
from backend.services.insurance_preparation import prepare_insurance_draft_from_honoraires


def _patient_and_document(client, auth_headers, db):
    patient_response = client.post(
        "/api/patients/",
        json={
            "nom": "CONSISTENCY",
            "prenom": "Insurance",
            "date_naissance": "1990-01-01",
            "sexe": "M",
            "telephone": "0612345678",
            "assurance": "CNSS",
        },
        headers=auth_headers,
    )
    assert patient_response.status_code in (200, 201), patient_response.text
    patient_id = patient_response.json()["id"]
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
    document = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.patient_id == patient_id,
        models.DocumentArchive.document_type == models.DocumentType.NOTE_HONORAIRES,
    ).one()
    return patient_id, document


def test_prepared_draft_matches_canonical_honoraires(client, auth_headers, db):
    _, document = _patient_and_document(client, auth_headers, db)
    draft = prepare_insurance_draft_from_honoraires(
        db,
        honoraires_document_id=document.id,
        organization=InsuranceOrganization.CNSS,
    )
    source = assert_draft_matches_honoraires_source(db, draft=draft)
    assert source.document.id == document.id
    assert source.acte_ids == [draft.lines[0].source.acte_id]


def test_amount_tampering_is_rejected(client, auth_headers, db):
    _, document = _patient_and_document(client, auth_headers, db)
    draft = prepare_insurance_draft_from_honoraires(
        db,
        honoraires_document_id=document.id,
        organization=InsuranceOrganization.CNSS,
    )
    tampered_line = draft.lines[0].model_copy(update={"amount_mad": 9999.0})
    tampered = draft.model_copy(update={"lines": [tampered_line]})
    with pytest.raises(ValueError, match="amount mismatch"):
        assert_draft_matches_honoraires_source(db, draft=tampered)


def test_teeth_and_label_tampering_are_rejected(client, auth_headers, db):
    _, document = _patient_and_document(client, auth_headers, db)
    draft = prepare_insurance_draft_from_honoraires(
        db,
        honoraires_document_id=document.id,
        organization=InsuranceOrganization.CNSS,
    )
    bad_teeth = draft.model_copy(update={
        "lines": [draft.lines[0].model_copy(update={"teeth": ["48"]})]
    })
    with pytest.raises(ValueError, match="teeth mismatch"):
        assert_draft_matches_honoraires_source(db, draft=bad_teeth)

    bad_label = draft.model_copy(update={
        "lines": [draft.lines[0].model_copy(update={"label": "Implant invente"})]
    })
    with pytest.raises(ValueError, match="label mismatch"):
        assert_draft_matches_honoraires_source(db, draft=bad_label)


def test_source_uid_tampering_is_rejected(client, auth_headers, db):
    _, document = _patient_and_document(client, auth_headers, db)
    draft = prepare_insurance_draft_from_honoraires(
        db,
        honoraires_document_id=document.id,
        organization=InsuranceOrganization.CNSS,
    )
    bad_source = draft.lines[0].source.model_copy(update={
        "source_line_uid": "00000000-0000-0000-0000-000000000001"
    })
    tampered = draft.model_copy(update={
        "lines": [draft.lines[0].model_copy(update={"source": bad_source})]
    })
    with pytest.raises(ValueError, match="UID mismatch"):
        assert_draft_matches_honoraires_source(db, draft=tampered)
