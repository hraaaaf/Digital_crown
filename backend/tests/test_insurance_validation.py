from datetime import date, datetime

import fitz
import pytest

from backend import models
from backend.models_ngap_reference import NgapCatalogMapping
from backend.schemas.insurance_submission import (
    InsuranceCareType,
    InsuranceDraftStatus,
    InsuranceOrganization,
    InsuranceRequestNature,
)
from backend.services.insurance_preparation import prepare_insurance_draft_from_honoraires
from backend.services.insurance_source_store import (
    lock_and_store_insurance_template,
    lock_and_store_ngap_primary,
)
from backend.services.insurance_template_registry import CNSS_610_1_04
from backend.services.insurance_validation import validate_insurance_draft_by_practitioner
from backend.services.ngap_reference import DENTAL_NGAP_PRIMARY_PENDING


def _pdf(*, pages: int, text: str) -> bytes:
    document = fitz.open()
    for index in range(pages):
        page = document.new_page()
        page.insert_text((72, 72), f"{text} {index + 1}")
    payload = document.tobytes()
    document.close()
    return payload


def _catalog_act(db):
    specialty = models.Specialty(name="Validation Insurance")
    db.add(specialty)
    db.flush()
    act = models.CatalogAct(
        specialty_id=specialty.id,
        name="Detartrage validation",
        code="INTERNAL-DET",
        base_price=500.0,
        is_active=True,
    )
    db.add(act)
    db.flush()
    return act


def _patient(client, auth_headers):
    response = client.post(
        "/api/patients/",
        json={
            "nom": "VALIDATION",
            "prenom": "Insurance",
            "date_naissance": "1990-01-01",
            "sexe": "M",
            "telephone": "0612345678",
            "assurance": "CNSS",
        },
        headers=auth_headers,
    )
    assert response.status_code in (200, 201), response.text
    return response.json()["id"]


def _honoraires(client, auth_headers, patient_id, catalog_act_id):
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
                    "catalog_act_id": catalog_act_id,
                }],
                "doc_date": "2026-09-14",
                "teeth_data": [],
            },
        },
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text


def _complete_admin(draft):
    # This test targets the practitioner-validation gate itself. Keep the
    # administrative snapshot explicit and complete instead of depending on
    # unrelated prefill inference details.
    return draft.administrative.model_copy(update={
        "request_nature": InsuranceRequestNature.EXECUTION,
        "insured_full_name": "Insurance VALIDATION",
        "insured_registration_number": "123456789",
        "insured_national_id": "AB123456",
        "insured_address": "Rabat",
        "relationship_to_insured": "LUI_MEME",
        "beneficiary_full_name": "Insurance VALIDATION",
        "beneficiary_birth_date": date(1990, 1, 1),
        "beneficiary_national_id": "AB123456",
        "beneficiary_sex": "M",
        "practitioner_full_name": "Dr Validation",
        "practitioner_inpe": "INPE-VALID",
        "care_type": InsuranceCareType.SOINS,
    })


def _prepared_fixture(client, auth_headers, db, dentiste, tmp_path):
    dentiste.nom_complet = "Dr Validation"
    dentiste.identifiants_legaux = {"inpe": "INPE-VALID"}
    db.flush()

    patient_id = _patient(client, auth_headers)
    catalog_act = _catalog_act(db)
    catalog_act_id = catalog_act.id
    # Document generation renders in a separate SessionLocal/thread, so the
    # reference act must be committed before the HTTP call can resolve it.
    db.commit()
    _honoraires(client, auth_headers, patient_id, catalog_act_id)
    document = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.patient_id == patient_id,
        models.DocumentArchive.document_type == models.DocumentType.NOTE_HONORAIRES,
    ).one()

    ngap_pdf = _pdf(
        pages=2,
        text="Arrete 177-06 Nomenclature generale des actes professionnels",
    )
    locked_release, _ = lock_and_store_ngap_primary(
        root=tmp_path,
        release=DENTAL_NGAP_PRIMARY_PENDING,
        pdf_bytes=ngap_pdf,
        source_url="cabinet://official/177-06.pdf",
    )
    db.add(NgapCatalogMapping(
        catalog_act_id=catalog_act_id,
        code_kind="NGAP",
        ngap_code="D1",
        coefficient=10.0,
        official_label="Detartrage test",
        requires_prior_approval=False,
        requires_radiograph=False,
        reference_version=locked_release.version,
        mapping_rule_id=f"{locked_release.version}:{catalog_act_id}",
        verification_status="VERIFIED_PRIMARY",
        source_authority=locked_release.authority,
        source_url=locked_release.source_url,
        source_hash=locked_release.source_hash,
        validated_by_practitioner_id=dentiste.id,
        validated_at=datetime(2026, 9, 14, 20, 0),
    ))
    db.flush()

    template_pdf = _pdf(pages=2, text="CNSS 610-1-04 synthetic validation template")
    locked_template, _ = lock_and_store_insurance_template(
        root=tmp_path,
        definition=CNSS_610_1_04,
        pdf_bytes=template_pdf,
        source_url="cabinet://validated/CNSS-610-1-04.pdf",
        cabinet_validated_by="Dr Validation",
    )

    draft = prepare_insurance_draft_from_honoraires(
        db,
        honoraires_document_id=document.id,
        organization=InsuranceOrganization.CNSS,
        locked_template=locked_template,
        ngap_reference_version=locked_release.version,
    )
    return draft, locked_release


def test_practitioner_validation_gate_builds_validated_snapshot(
    client, auth_headers, db, dentiste, tmp_path
):
    draft, locked_release = _prepared_fixture(client, auth_headers, db, dentiste, tmp_path)
    draft = draft.model_copy(update={"administrative": _complete_admin(draft)})

    validated = validate_insurance_draft_by_practitioner(
        db,
        draft=draft,
        practitioner_id=dentiste.id,
        source_store_root=tmp_path,
        validated_at=datetime(2026, 9, 14, 20, 30),
    )

    assert validated.status == InsuranceDraftStatus.VALIDATED
    assert validated.validated_by_practitioner_id == dentiste.id
    assert validated.lines[0].ngap_code == "D1"
    assert validated.reference.ngap_reference_hash == locked_release.source_hash
    assert validated.unresolved_fields == []


def test_validation_gate_ignores_client_ngap_code_and_re_resolves_server_mapping(
    client, auth_headers, db, dentiste, tmp_path
):
    draft, _ = _prepared_fixture(client, auth_headers, db, dentiste, tmp_path)
    draft = draft.model_copy(update={"administrative": _complete_admin(draft)})
    tampered_line = draft.lines[0].model_copy(update={
        "ngap_code": "FAKE",
        "mapping_rule_id": "client:fake",
    })
    draft = draft.model_copy(update={"lines": [tampered_line]})

    validated = validate_insurance_draft_by_practitioner(
        db,
        draft=draft,
        practitioner_id=dentiste.id,
        source_store_root=tmp_path,
    )
    assert validated.lines[0].ngap_code == "D1"
    assert validated.lines[0].mapping_rule_id != "client:fake"


def test_validation_gate_blocks_missing_admin_fields(
    client, auth_headers, db, dentiste, tmp_path
):
    draft, _ = _prepared_fixture(client, auth_headers, db, dentiste, tmp_path)
    with pytest.raises(ValueError, match="unresolved required fields"):
        validate_insurance_draft_by_practitioner(
            db,
            draft=draft,
            practitioner_id=dentiste.id,
            source_store_root=tmp_path,
        )


def test_validation_gate_blocks_non_source_practitioner(
    client, auth_headers, db, dentiste, tmp_path
):
    draft, _ = _prepared_fixture(client, auth_headers, db, dentiste, tmp_path)
    draft = draft.model_copy(update={"administrative": _complete_admin(draft)})
    with pytest.raises(ValueError, match="source Honoraires practitioner"):
        validate_insurance_draft_by_practitioner(
            db,
            draft=draft,
            practitioner_id=dentiste.id + 999,
            source_store_root=tmp_path,
        )
