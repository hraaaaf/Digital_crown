"""Administrative prefill and completeness policy for dental insurance drafts.

Only values already explicit in Digital Crown are copied. Insured identity/affiliation,
beneficiary CIN, relationship and practitioner INPE are never guessed. Missing required
CNSS fields remain visible in ``unresolved_fields`` for the preparation/review UI.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Iterable

from sqlalchemy.orm import Session

from backend import models
from backend.schemas.insurance_submission import (
    InsuranceAdministrativeSnapshot,
    InsuranceCareType,
    InsuranceDraftStatus,
    InsuranceMappingStatus,
    InsuranceOrganization,
    InsuranceSubmissionDraft,
)


CNSS_REQUIRED_ADMIN_FIELDS = (
    "request_nature",
    "insured_full_name",
    "insured_registration_number",
    "insured_national_id",
    "insured_address",
    "relationship_to_insured",
    "beneficiary_full_name",
    "beneficiary_birth_date",
    "beneficiary_national_id",
    "beneficiary_sex",
    "practitioner_full_name",
    "practitioner_inpe",
    "care_type",
)

_EXPLICIT_INPE_KEYS = {
    "inpe",
    "inp",
    "numero_inpe",
    "numero_inp",
    "n_inpe",
    "n_inp",
}

_ACTE_TO_CARE_TYPE = {
    "SOIN": InsuranceCareType.SOINS,
    "PROTHESE": InsuranceCareType.PROTHESE,
    "ORTHO_SEMESTRE": InsuranceCareType.ORTHODONTIE_FACIALE,
    "ORTHO_CONTENTION": InsuranceCareType.ORTHODONTIE_FACIALE,
}


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _full_name(prenom: Any, nom: Any) -> str | None:
    parts = [_clean_text(prenom), _clean_text(nom)]
    values = [value for value in parts if value]
    return " ".join(values) if values else None


def _birth_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return None


def _beneficiary_sex(value: Any) -> str | None:
    normalized = str(value or "").strip().upper()
    if normalized in {"M", "F"}:
        return normalized
    return None


def _explicit_practitioner_inpe(practitioner: models.User) -> str | None:
    identifiers = getattr(practitioner, "identifiants_legaux", None)
    if not isinstance(identifiers, dict):
        return None
    for raw_key, raw_value in identifiers.items():
        key = str(raw_key or "").strip().lower().replace("-", "_").replace(" ", "_")
        if key not in _EXPLICIT_INPE_KEYS:
            continue
        value = _clean_text(raw_value)
        if value:
            return value
    return None


def _infer_single_care_type(db: Session, draft: InsuranceSubmissionDraft) -> InsuranceCareType | None:
    acte_ids = [line.source.acte_id for line in draft.lines if line.source.acte_id is not None]
    if not acte_ids or len(acte_ids) != len(draft.lines):
        return None
    rows = db.query(models.Acte).filter(
        models.Acte.id.in_(acte_ids),
        models.Acte.deleted_at.is_(None),
    ).all()
    if len(rows) != len(set(acte_ids)):
        return None

    care_types: set[InsuranceCareType] = set()
    for acte in rows:
        raw_type = getattr(acte.type_acte, "value", acte.type_acte)
        care_type = _ACTE_TO_CARE_TYPE.get(str(raw_type or ""))
        if care_type is None:
            return None
        care_types.add(care_type)
    if len(care_types) != 1:
        return None
    return next(iter(care_types))


def missing_cnss_administrative_fields(
    administrative: InsuranceAdministrativeSnapshot,
) -> list[str]:
    missing: list[str] = []
    for field_name in CNSS_REQUIRED_ADMIN_FIELDS:
        value = getattr(administrative, field_name)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(f"administrative.{field_name}")
    return missing


def prefill_cnss_administrative(
    db: Session,
    *,
    draft: InsuranceSubmissionDraft,
    patient: models.Patient,
    practitioner: models.User,
) -> InsuranceSubmissionDraft:
    """Prefill only explicit patient/practitioner facts and expose every missing field.

    Existing manually entered draft values always win. Patient address is deliberately
    not copied to the insured address because the beneficiary may not be the insured.
    No insured identity, relationship, CIN or affiliation number is inferred.
    """
    if draft.organization != InsuranceOrganization.CNSS:
        raise ValueError("CNSS administrative prefill requires a CNSS draft")
    if int(patient.id) != int(draft.patient_id):
        raise ValueError("Patient/draft mismatch")

    current = draft.administrative
    updates = current.model_dump()

    if not current.beneficiary_full_name:
        updates["beneficiary_full_name"] = _full_name(patient.prenom, patient.nom)
    if current.beneficiary_birth_date is None:
        updates["beneficiary_birth_date"] = _birth_date(patient.date_naissance)
    if not current.beneficiary_sex:
        updates["beneficiary_sex"] = _beneficiary_sex(patient.sexe)
    if not current.practitioner_full_name:
        updates["practitioner_full_name"] = _clean_text(practitioner.nom_complet)
    if not current.practitioner_inpe:
        updates["practitioner_inpe"] = _explicit_practitioner_inpe(practitioner)
    if current.care_type is None:
        updates["care_type"] = _infer_single_care_type(db, draft)

    administrative = InsuranceAdministrativeSnapshot(**updates)
    unresolved = [
        value for value in draft.unresolved_fields
        if not value.startswith("administrative.")
    ]
    unresolved.extend(missing_cnss_administrative_fields(administrative))

    all_exact = all(
        line.mapping_status == InsuranceMappingStatus.EXACT for line in draft.lines
    )
    status = (
        InsuranceDraftStatus.READY_FOR_REVIEW
        if all_exact and not unresolved
        else InsuranceDraftStatus.INCOMPLETE
    )

    return draft.model_copy(update={
        "administrative": administrative,
        "unresolved_fields": unresolved,
        "status": status,
        "validated_by_practitioner_id": None,
        "validated_at": None,
    })
