from datetime import date, datetime

from backend import models
from backend.schemas.insurance_submission import (
    InsuranceAdministrativeSnapshot,
    InsuranceCareType,
    InsuranceDraftStatus,
    InsuranceLineSource,
    InsuranceMappingStatus,
    InsuranceOrganization,
    InsuranceSubmissionDraft,
    InsuranceSubmissionLine,
    InsuranceTemplateSnapshot,
)
from backend.services.insurance_administrative import prefill_cnss_administrative


def _patient(db, dentiste, *, suffix="ADMIN"):
    patient = models.Patient(
        nom=f"Patient{suffix}",
        prenom="Youssef",
        date_naissance=datetime(1992, 4, 3),
        sexe="M",
        adresse="Adresse beneficiaire qui ne doit pas devenir adresse assure",
        employer_id=dentiste.id,
        assurance="CNSS",
    )
    db.add(patient)
    db.flush()
    return patient


def _acte(db, patient, dentiste, *, acte_type=models.ActeType.SOIN):
    acte = models.Acte(
        patient_id=patient.id,
        praticien_id=dentiste.id,
        type_acte=acte_type,
        libelle="Detartrage",
        montant=500.0,
        date_debut=datetime(2026, 9, 14),
        statut_paiement=models.PaiementStatut.EN_ATTENTE,
        is_accounted=True,
        is_collected=False,
        validated_by="Dr Test",
    )
    db.add(acte)
    db.flush()
    return acte


def _draft(patient_id, acte_id, *, exact=False, administrative=None):
    mapping_status = InsuranceMappingStatus.EXACT if exact else InsuranceMappingStatus.NOT_EVALUATED
    return InsuranceSubmissionDraft(
        patient_id=patient_id,
        organization=InsuranceOrganization.CNSS,
        honoraires_document_id=42,
        lines=[InsuranceSubmissionLine(
            source=InsuranceLineSource(
                honoraires_document_id=42,
                honoraires_line_index=0,
                acte_id=acte_id,
            ),
            service_date=date(2026, 9, 14),
            label="Detartrage",
            teeth=["11"],
            amount_mad=500.0,
            mapping_status=mapping_status,
            ngap_code="D1" if exact else None,
            mapping_rule_id="test:D1" if exact else None,
        )],
        administrative=administrative or InsuranceAdministrativeSnapshot(),
        template=InsuranceTemplateSnapshot(template_version="CNSS-610-1-04"),
    )


def test_cnss_prefill_uses_only_explicit_patient_and_practitioner_facts(db, dentiste):
    patient = _patient(db, dentiste)
    acte = _acte(db, patient, dentiste)
    dentiste.nom_complet = "Dr Test Dentiste"
    dentiste.identifiants_legaux = {"inpe": "INPE-12345", "ice": "DO-NOT-USE"}
    db.flush()

    result = prefill_cnss_administrative(
        db,
        draft=_draft(patient.id, acte.id),
        patient=patient,
        practitioner=dentiste,
    )

    admin = result.administrative
    assert admin.beneficiary_full_name == f"Youssef PatientADMIN"
    assert admin.beneficiary_birth_date == date(1992, 4, 3)
    assert admin.beneficiary_sex == "M"
    assert admin.practitioner_full_name == "Dr Test Dentiste"
    assert admin.practitioner_inpe == "INPE-12345"
    assert admin.care_type == InsuranceCareType.SOINS

    # Never infer the upper insured section from beneficiary data/address.
    assert admin.insured_full_name is None
    assert admin.insured_address is None
    assert admin.relationship_to_insured is None

    # The cabinet-validated CNSS profile deliberately leaves the insured section
    # untouched, so these fields are not blockers for practitioner validation.
    assert "administrative.insured_full_name" not in result.unresolved_fields
    assert "administrative.insured_registration_number" not in result.unresolved_fields
    assert "administrative.insured_national_id" not in result.unresolved_fields
    assert "administrative.insured_address" not in result.unresolved_fields
    assert "administrative.relationship_to_insured" not in result.unresolved_fields
    assert "administrative.request_nature" not in result.unresolved_fields

    assert "administrative.beneficiary_national_id" in result.unresolved_fields
    assert "administrative.practitioner_inpe" not in result.unresolved_fields
    assert result.status == InsuranceDraftStatus.INCOMPLETE


def test_unknown_legal_identifier_is_not_guessed_as_inpe(db, dentiste):
    patient = _patient(db, dentiste, suffix="NOINPE")
    acte = _acte(db, patient, dentiste)
    dentiste.nom_complet = "Dr Sans INPE explicite"
    dentiste.identifiants_legaux = {"numero_professionnel": "SHOULD-NOT-BE-GUESSED"}
    db.flush()

    result = prefill_cnss_administrative(
        db,
        draft=_draft(patient.id, acte.id),
        patient=patient,
        practitioner=dentiste,
    )
    assert result.administrative.practitioner_inpe is None
    assert "administrative.practitioner_inpe" in result.unresolved_fields


def test_validated_cnss_zone_plus_exact_mapping_becomes_ready_for_review(db, dentiste):
    patient = _patient(db, dentiste, suffix="READY")
    acte = _acte(db, patient, dentiste)
    complete_validated_zone = InsuranceAdministrativeSnapshot(
        beneficiary_full_name="Youssef PatientREADY",
        beneficiary_birth_date=date(1992, 4, 3),
        beneficiary_national_id="AB123456",
        beneficiary_sex="M",
        practitioner_full_name="Dr Test",
        practitioner_inpe="123456",
        care_type=InsuranceCareType.SOINS,
        attachments_count=0,
    )
    result = prefill_cnss_administrative(
        db,
        draft=_draft(patient.id, acte.id, exact=True, administrative=complete_validated_zone),
        patient=patient,
        practitioner=dentiste,
    )
    assert result.administrative.insured_full_name is None
    assert result.administrative.request_nature is None
    assert result.unresolved_fields == []
    assert result.status == InsuranceDraftStatus.READY_FOR_REVIEW


def test_mixed_care_types_remain_manual_instead_of_guessing(db, dentiste):
    patient = _patient(db, dentiste, suffix="MIXED")
    soin = _acte(db, patient, dentiste, acte_type=models.ActeType.SOIN)
    prothese = _acte(db, patient, dentiste, acte_type=models.ActeType.PROTHESE)
    draft = InsuranceSubmissionDraft(
        patient_id=patient.id,
        organization=InsuranceOrganization.CNSS,
        honoraires_document_id=42,
        lines=[
            InsuranceSubmissionLine(
                source=InsuranceLineSource(honoraires_document_id=42, honoraires_line_index=0, acte_id=soin.id),
                service_date=date(2026, 9, 14), label="Soin", amount_mad=300,
            ),
            InsuranceSubmissionLine(
                source=InsuranceLineSource(honoraires_document_id=42, honoraires_line_index=1, acte_id=prothese.id),
                service_date=date(2026, 9, 14), label="Prothese", amount_mad=1200,
            ),
        ],
        template=InsuranceTemplateSnapshot(template_version="CNSS-610-1-04"),
    )
    result = prefill_cnss_administrative(
        db,
        draft=draft,
        patient=patient,
        practitioner=dentiste,
    )
    assert result.administrative.care_type is None
    assert "administrative.care_type" in result.unresolved_fields
