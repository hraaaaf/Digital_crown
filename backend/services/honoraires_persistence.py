from __future__ import annotations

import math
import uuid
from datetime import datetime
from typing import Any, Iterable

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from backend import models
from backend.services.acte_classification import classify_acte_type
from backend.services.document_provenance_context import effective_document_practitioner_id


_PAYMENT_METHOD_ALIASES = {
    "ESPECES": "ESPECES",
    "ESPÈCES": "ESPECES",
    "TPE": "CARTE",
    "CARTE": "CARTE",
    "CHEQUE": "CHEQUE",
    "CHÈQUE": "CHEQUE",
    "VIREMENT": "VIREMENT",
}
_MAX_HONORAIRES_LINE_AMOUNT = 1_000_000.0
_GENERATED_PAYMENT_PREFIX = "Lien Doc ID: "
_VOIDED_PAYMENT_PREFIX = "ANNULÉ — Lien Doc ID: "


def normalize_document_payment_method(value: Any) -> str:
    if value is None or not str(value).strip():
        raise ValueError("Le mode de paiement est requis pour un encaissement Honoraires.")
    normalized = str(value).strip().upper()
    method = _PAYMENT_METHOD_ALIASES.get(normalized)
    if method is None:
        raise ValueError("Mode de paiement invalide")
    return method


def _validated_honoraires_item(item: dict[str, Any]) -> tuple[str, float]:
    libelle = str(item.get("acte") or "").strip()
    if not libelle:
        raise ValueError("Chaque ligne Honoraires doit contenir un acte explicite.")

    try:
        amount = float(item.get("montant"))
    except (TypeError, ValueError) as exc:
        raise ValueError("Le montant Honoraires doit être numérique.") from exc

    if not math.isfinite(amount):
        raise ValueError("Le montant Honoraires doit être fini.")
    if amount <= 0:
        raise ValueError("Le montant Honoraires doit être strictement positif.")
    if amount > _MAX_HONORAIRES_LINE_AMOUNT:
        raise ValueError("Le montant Honoraires dépasse la limite autorisée par ligne.")
    return libelle, amount


def _business_datetime(item: dict[str, Any], fallback: datetime) -> datetime:
    raw = item.get("date")
    if raw in (None, ""):
        return fallback
    if isinstance(raw, datetime):
        return raw
    try:
        return datetime.fromisoformat(str(raw).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError("La date de la note d'honoraires est invalide.") from exc


def _normalized_source_line_uid(value: Any) -> str | None:
    if value in (None, ""):
        return None
    try:
        return str(uuid.UUID(str(value).strip()))
    except (ValueError, AttributeError, TypeError) as exc:
        raise ValueError("Identifiant stable de ligne Honoraires invalide") from exc


def _resolved_catalog_act_id(db: Session, item: dict[str, Any], acte) -> int | None:
    if "catalog_act_id" not in item:
        return getattr(acte, "catalog_act_id", None) if acte is not None else None

    raw = item.get("catalog_act_id")
    if raw in (None, ""):
        return None
    try:
        catalog_act_id = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("catalog_act_id invalide") from exc
    if catalog_act_id <= 0:
        raise ValueError("catalog_act_id invalide")

    catalog_act = db.query(models.CatalogAct).filter(
        models.CatalogAct.id == catalog_act_id,
        models.CatalogAct.is_active.is_(True),
    ).first()
    if catalog_act is None:
        raise ValueError("CatalogAct introuvable ou inactif")
    return catalog_act_id


def _generated_payment_note(document_archive_id: int) -> str:
    return f"{_GENERATED_PAYMENT_PREFIX}{document_archive_id}"


def _voided_payment_note(document_archive_id: int) -> str:
    return f"{_VOIDED_PAYMENT_PREFIX}{document_archive_id}"


def _is_document_generated_payment(payment: models.Payment, document_archive_id: int) -> bool:
    note = str(payment.notes or "")
    return note in {
        _generated_payment_note(document_archive_id),
        _voided_payment_note(document_archive_id),
    }


def persist_honoraires_lines(
    db: Session,
    *,
    patient_id: int,
    practitioner_id: int,
    document_archive_id: int,
    document_created_at: datetime,
    items: Iterable[dict[str, Any]],
    payment_status: models.PaiementStatut,
    is_accounted: bool,
    validated_by: str,
) -> tuple[list[models.Acte], list[models.Payment]]:
    """Stage or reconcile Acte rows and exact document-generated payments.

    New lines get a stable UUID mirrored into the canonical Honoraires snapshot when
    the source DocumentArchive exists, and always into the derived Acte. Existing rows
    prefer explicit UID matching; historical rows without UID retain the controlled
    index fallback. Direct service-level callers without a persisted archive remain
    supported. No fuzzy catalogue matching.
    """
    practitioner_id = effective_document_practitioner_id(practitioner_id)
    if practitioner_id is None:
        raise ValueError("Praticien auteur requis pour persister les honoraires")

    item_list = list(items)
    if not item_list:
        raise ValueError("Une note d'honoraires doit contenir au moins un acte.")

    validated_items = [(_validated_honoraires_item(item), item) for item in item_list]
    if payment_status == models.PaiementStatut.PAYE:
        for _, item in validated_items:
            normalize_document_payment_method(item.get("mode_reglement"))

    all_existing_actes = (
        db.query(models.Acte)
        .filter(models.Acte.document_archive_id == document_archive_id)
        .order_by(models.Acte.id.asc())
        .all()
    )
    existing_actes = [acte for acte in all_existing_actes if acte.deleted_at is None]
    existing_by_uid = {
        str(acte.source_line_uid): acte
        for acte in existing_actes
        if getattr(acte, "source_line_uid", None)
    }

    actes: list[models.Acte] = []
    used_existing_ids: set[int] = set()
    edit_timestamp = datetime.now()

    for index, ((libelle, amount), item) in enumerate(validated_items):
        requested_uid = _normalized_source_line_uid(item.get("source_line_uid"))
        acte = existing_by_uid.get(requested_uid) if requested_uid else None
        if acte is not None and acte.id in used_existing_ids:
            raise ValueError("source_line_uid dupliqué dans la note d'honoraires")

        if acte is None and requested_uid is None and index < len(existing_actes):
            candidate = existing_actes[index]
            if candidate.id not in used_existing_ids:
                acte = candidate

        if acte is not None:
            source_line_uid = requested_uid or _normalized_source_line_uid(
                getattr(acte, "source_line_uid", None)
            ) or str(uuid.uuid4())
        else:
            source_line_uid = requested_uid or str(uuid.uuid4())

        catalog_act_id = _resolved_catalog_act_id(db, item, acte)
        item["source_line_uid"] = source_line_uid
        item["catalog_act_id"] = catalog_act_id
        business_date = _business_datetime(item, document_created_at)

        if acte is None:
            acte = models.Acte(
                patient_id=patient_id,
                praticien_id=practitioner_id,
                type_acte=classify_acte_type(libelle),
                libelle=libelle,
                montant=amount,
                date_debut=business_date,
                statut_paiement=payment_status,
                is_accounted=is_accounted,
                is_collected=(payment_status == models.PaiementStatut.PAYE),
                validated_by=validated_by,
                document_archive_id=document_archive_id,
                source_line_uid=source_line_uid,
                catalog_act_id=catalog_act_id,
            )
            db.add(acte)
        else:
            acte.patient_id = patient_id
            acte.praticien_id = practitioner_id
            acte.type_acte = classify_acte_type(libelle)
            acte.libelle = libelle
            acte.montant = amount
            acte.date_debut = business_date
            acte.statut_paiement = payment_status
            acte.is_accounted = is_accounted
            acte.is_collected = payment_status == models.PaiementStatut.PAYE
            acte.validated_by = validated_by
            acte.document_archive_id = document_archive_id
            acte.source_line_uid = source_line_uid
            acte.catalog_act_id = catalog_act_id
            if acte.id is not None:
                used_existing_ids.add(acte.id)
        actes.append(acte)

    active_existing_ids = {acte.id for acte in actes if acte.id is not None}
    for stale_acte in existing_actes:
        if stale_acte.id in active_existing_ids:
            continue
        if stale_acte.deleted_at is None:
            stale_acte.deleted_at = edit_timestamp
        stale_acte.is_collected = False

    archive = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.id == document_archive_id
    ).first()
    if archive is not None:
        snapshot = dict(archive.clinical_data or {})
        snapshot["payments"] = item_list
        archive.clinical_data = snapshot
        # The original archived JSON and ``items`` can share nested dict/list objects.
        # UUID/catalog mutations happen in-place, so SQLAlchemy may otherwise compare
        # equal old/new JSON values and skip the UPDATE. Force persistence explicitly.
        flag_modified(archive, "clinical_data")

    db.flush()

    all_related_actes = all_existing_actes + [a for a in actes if a not in all_existing_actes]
    acte_ids = [a.id for a in all_related_actes if a.id is not None]
    payments_by_acte: dict[int, list[models.Payment]] = {acte_id: [] for acte_id in acte_ids}
    if acte_ids:
        related_payments = db.query(models.Payment).filter(models.Payment.acte_id.in_(acte_ids)).all()
        for payment in related_payments:
            if payment.acte_id is not None:
                payments_by_acte.setdefault(payment.acte_id, []).append(payment)

    active_generated_payments: list[models.Payment] = []
    for ((_, amount), item), acte in zip(validated_items, actes):
        generated = next(
            (
                payment
                for payment in payments_by_acte.get(acte.id, [])
                if _is_document_generated_payment(payment, document_archive_id)
            ),
            None,
        )

        if payment_status == models.PaiementStatut.PAYE:
            if generated is None:
                generated = models.Payment(patient_id=patient_id, acte_id=acte.id)
                db.add(generated)
            generated.patient_id = patient_id
            generated.amount = amount
            generated.payment_method = normalize_document_payment_method(item.get("mode_reglement"))
            generated.payment_date = _business_datetime(item, document_created_at)
            generated.acte_id = acte.id
            generated.notes = _generated_payment_note(document_archive_id)
            generated.validated_by = validated_by
            active_generated_payments.append(generated)
        elif generated is not None:
            generated.notes = _voided_payment_note(document_archive_id)

    active_acte_ids = {acte.id for acte in actes if acte.id is not None}
    for stale_acte in all_existing_actes:
        if stale_acte.id in active_acte_ids:
            continue
        for payment in payments_by_acte.get(stale_acte.id, []):
            if _is_document_generated_payment(payment, document_archive_id):
                payment.notes = _voided_payment_note(document_archive_id)

    return actes, active_generated_payments
