from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Iterable

from sqlalchemy.orm import Session

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
    """Return the document business date, preserving fallback time when absent.

    Document Studio writes the selected document date on every Honoraires line.
    That date is the accounting truth: editing a note from one day/month to
    another must move the same Acte/Payment rather than create a second entry.
    """
    raw = item.get("date")
    if raw in (None, ""):
        return fallback
    if isinstance(raw, datetime):
        return raw
    try:
        parsed = datetime.fromisoformat(str(raw).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError("La date de la note d'honoraires est invalide.") from exc
    return parsed


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

    The DocumentArchive is canonical. Re-generating the same archive id updates the
    derived Acte rows instead of duplicating them. The selected document date is the
    accounting date, so changing it moves the same rows between day/month buckets.
    Payments created manually through another flow are never deleted or rewritten here.

    No commit is performed here. The caller owns the transaction.
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
    # Une ligne déjà sortie par une édition reste un historique immuable. Elle ne
    # doit jamais redevenir la nouvelle ligne active lors d'un shrink -> expand.
    existing_actes = [acte for acte in all_existing_actes if acte.deleted_at is None]

    actes: list[models.Acte] = []
    edit_timestamp = datetime.now()

    for index, ((libelle, amount), item) in enumerate(validated_items):
        business_date = _business_datetime(item, document_created_at)
        if index < len(existing_actes):
            acte = existing_actes[index]
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
        else:
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
            )
            db.add(acte)
        actes.append(acte)

    # Les anciennes lignes surnuméraires restent auditables mais sortent de toutes
    # les vues comptables. Elles ne seront pas restaurées avec une future corbeille
    # du document car leur timestamp diffère de celui de cette suppression future.
    for stale_acte in existing_actes[len(validated_items):]:
        if stale_acte.deleted_at is None:
            stale_acte.deleted_at = edit_timestamp
        stale_acte.is_collected = False

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
                generated = models.Payment(
                    patient_id=patient_id,
                    acte_id=acte.id,
                )
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

    # Toute ligne supprimée par l'édition annule uniquement l'encaissement qui avait
    # été généré par ce document. Un paiement manuel lié au même Acte reste intact.
    active_acte_ids = {acte.id for acte in actes if acte.id is not None}
    for stale_acte in all_existing_actes:
        if stale_acte.id in active_acte_ids:
            continue
        for payment in payments_by_acte.get(stale_acte.id, []):
            if _is_document_generated_payment(payment, document_archive_id):
                payment.notes = _voided_payment_note(document_archive_id)

    return actes, active_generated_payments
