from datetime import date, datetime

import fitz
import pytest

from backend import models
from backend.schemas.insurance_submission import (
    InsuranceAdministrativeSnapshot,
    InsuranceClaimContext,
    InsuranceLineSource,
    InsuranceMappingStatus,
    InsuranceOrganization,
    InsuranceSubmissionDraft,
    InsuranceSubmissionLine,
    InsuranceTemplateSnapshot,
    InsuranceTemplateTrust,
)
from backend.services.insurance_administrative import prefill_far_administrative
from backend.services.insurance_far_2021_1_profile import (
    FAR_2021_1_DERIVED_MAX_LINES,
    FAR_2021_1_DERIVED_PROFILE,
    FAR_2021_1_DERIVED_TEMPLATE_SHA256,
)
from backend.services.insurance_pdf_overlay import _field_value
from backend.services.insurance_source_store import lock_and_store_insurance_template
from backend.services.insurance_template_registry import FAR_2021_1
from backend.services.insurance_validation import assert_insurance_template_source


def _pdf_bytes(*, pages: int) -> bytes:
    document = fitz.open()
    for index in range(pages):
        page = document.new_page(width=841.8898, height=595.2756)
        page.insert_text((72, 72), f"FAR derived test page {index + 1}")
    payload = document.tobytes()
    document.close()
    return payload


def _line(*, exact: bool = True) -> InsuranceSubmissionLine:
    return InsuranceSubmissionLine(
        source=InsuranceLineSource(
            honoraires_document_id=42,
            honoraires_line_index=0,
            acte_id=1,
        ),
        service_date=date(2026, 9, 17),
        label="Detartrage",
        teeth=["11"],
        amount_mad=500.0,
        mapping_status=(InsuranceMappingStatus.EXACT if exact else InsuranceMappingStatus.NOT_EVALUATED),
        ngap_code=("D1" if exact else None),
        ngap_coefficient=(10.0 if exact else None),
        mapping_rule_id=("test:D1" if exact else None),
    )


def _draft(*, patient_id: int = 1, administrative=None, template=None) -> InsuranceSubmissionDraft:
    return InsuranceSubmissionDraft(
        patient_id=patient_id,
        organization=InsuranceOrganization.FAR,
        honoraires_document_id=42,
        lines=[_line()],
        administrative=administrative or InsuranceAdministrativeSnapshot(),
        template=template or InsuranceTemplateSnapshot(template_version=FAR_2021_1.version),
    )


def test_far_template_definition_is_explicitly_derived_and_two_pages():
    assert FAR_2021_1.trust == InsuranceTemplateTrust.CABINET_VALIDATED_DERIVED_REFERENCE
    assert FAR_2021_1.expected_page_count == 2
    assert "DERIVED" in FAR_2021_1.version
    assert FAR_2021_1_DERIVED_TEMPLATE_SHA256 == "c953d74f25ee5e3160683f16c45783448d55ea89640c710653a3e2cbf782bf42"


def test_far_derived_source_requires_validator_and_preserves_trust(tmp_path):
    payload = _pdf_bytes(pages=2)
    with pytest.raises(ValueError, match="validator identity"):
        lock_and_store_insurance_template(
            root=tmp_path,
            definition=FAR_2021_1,
            pdf_bytes=payload,
            source_url="cabinet://derived/FAR-2021-1.pdf",
        )

    locked, _ = lock_and_store_insurance_template(
        root=tmp_path,
        definition=FAR_2021_1,
        pdf_bytes=payload,
        source_url="cabinet://derived/FAR-2021-1.pdf",
        cabinet_validated_by="Cabinet Test",
    )
    draft = _draft(template=locked.as_submission_snapshot())
    assert draft.template.trust == InsuranceTemplateTrust.CABINET_VALIDATED_DERIVED_REFERENCE
    assert_insurance_template_source(source_store_root=tmp_path, draft=draft)


def test_far_derived_source_rejects_wrong_page_count(tmp_path):
    with pytest.raises(ValueError, match="page count mismatch"):
        lock_and_store_insurance_template(
            root=tmp_path,
            definition=FAR_2021_1,
            pdf_bytes=_pdf_bytes(pages=1),
            source_url="cabinet://derived/FAR-2021-1.pdf",
            cabinet_validated_by="Cabinet Test",
        )


def test_far_prefill_does_not_guess_member_military_facts(db, dentiste):
    patient = models.Patient(
        nom="FAR",
        prenom="Patient",
        date_naissance=datetime(1992, 4, 3),
        sexe="M",
        telephone="0612345678",
        adresse="Patient address must not become member address",
        employer_id=dentiste.id,
        assurance="FAR",
    )
    db.add(patient)
    db.flush()
    acte = models.Acte(
        patient_id=patient.id,
        praticien_id=dentiste.id,
        type_acte=models.ActeType.SOIN,
        libelle="Detartrage",
        montant=500.0,
        date_debut=datetime(2026, 9, 17),
        statut_paiement=models.PaiementStatut.EN_ATTENTE,
        is_accounted=True,
        is_collected=False,
        validated_by="Dr Test",
    )
    db.add(acte)
    dentiste.nom_complet = "Dr FAR"
    dentiste.identifiants_legaux = {"inpe": "INPE-FAR"}
    db.flush()

    draft = _draft(patient_id=patient.id)
    draft.lines[0].source.acte_id = acte.id
    result = prefill_far_administrative(db, draft=draft, patient=patient, practitioner=dentiste)

    assert result.administrative.beneficiary_full_name == "Patient FAR"
    assert result.administrative.practitioner_inpe == "INPE-FAR"
    assert result.administrative.insured_phone is None
    assert result.administrative.insured_address is None
    assert result.administrative.insured_account_number is None
    assert result.administrative.insured_grade is None
    assert result.administrative.insured_unit is None
    assert result.administrative.relationship_to_insured is None
    assert result.administrative.claim_context is None
    for field_name in (
        "insured_national_id",
        "insured_account_number",
        "insured_phone",
        "insured_full_name",
        "insured_grade",
        "insured_unit",
        "insured_address",
        "relationship_to_insured",
        "claim_context",
    ):
        assert f"administrative.{field_name}" in result.unresolved_fields


def test_far_complete_explicit_admin_becomes_ready_and_choices_are_renderable(db, dentiste):
    patient = models.Patient(
        nom="READY",
        prenom="Far",
        date_naissance=datetime(1990, 1, 1),
        sexe="F",
        employer_id=dentiste.id,
        assurance="FAR",
    )
    db.add(patient)
    db.flush()
    acte = models.Acte(
        patient_id=patient.id,
        praticien_id=dentiste.id,
        type_acte=models.ActeType.SOIN,
        libelle="Soin",
        montant=400.0,
        date_debut=datetime(2026, 9, 17),
        statut_paiement=models.PaiementStatut.EN_ATTENTE,
        is_accounted=True,
        is_collected=False,
        validated_by="Dr Test",
    )
    db.add(acte)
    dentiste.identifiants_legaux = {"inpe": "INPE-FAR"}
    db.flush()

    admin = InsuranceAdministrativeSnapshot(
        insured_national_id="AB123456",
        insured_account_number="CPT-001",
        insured_phone="0612345678",
        insured_full_name="Adherent FAR",
        insured_grade="Grade explicite",
        insured_unit="Unite explicite",
        insured_address="Rabat",
        beneficiary_full_name="Far READY",
        beneficiary_birth_date=date(1990, 1, 1),
        relationship_to_insured="ADHERENT",
        claim_context=InsuranceClaimContext.MALADIE,
        practitioner_inpe="INPE-FAR",
    )
    draft = _draft(patient_id=patient.id, administrative=admin)
    draft.lines[0].source.acte_id = acte.id
    result = prefill_far_administrative(db, draft=draft, patient=patient, practitioner=dentiste)

    assert result.unresolved_fields == []
    assert result.status.value == "READY_FOR_REVIEW"
    assert _field_value(result, "choice.relationship_to_insured.ADHERENT") == "X"
    assert _field_value(result, "choice.claim_context.MALADIE") == "X"
    assert _field_value(result, "choice.claim_context.ACCIDENT") == ""


def test_far_profile_never_writes_prescription_or_general_provider_page():
    assert FAR_2021_1_DERIVED_PROFILE.max_lines == FAR_2021_1_DERIVED_MAX_LINES == 6
    assert FAR_2021_1_DERIVED_PROFILE.template_hash == FAR_2021_1_DERIVED_TEMPLATE_SHA256
    assert FAR_2021_1_DERIVED_PROFILE.template_version == FAR_2021_1.version
    assert FAR_2021_1_DERIVED_PROFILE.organization == "FAR"
    assert all(placement.page_index == 0 for placement in FAR_2021_1_DERIVED_PROFILE.placements)
    keys = {placement.field_key.lower() for placement in FAR_2021_1_DERIVED_PROFILE.placements}
    assert not any("prescription" in key or "ordonnance" in key for key in keys)
    assert not any("signature" in key or "cachet" in key or "stamp" in key for key in keys)
    assert "administrative.practitioner_inpe" in keys
    assert "lines[0].label" in keys
