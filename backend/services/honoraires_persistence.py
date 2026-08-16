from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Iterable

from sqlalchemy.orm import Session

from backend import models
from backend.services.acte_classification import classify_acte_type


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
    """Stage validated Acte rows and exact linked payments in the caller transaction.

    No commit is performed here. The caller owns the transaction and can rollback
    the complete document/accounting mutation if any line or payment is invalid.
    """
    item_list = list(items)
    if not item_list:
        raise ValueError("Une note d'honoraires doit contenir au moins un acte.")

    validated_items = [(_validated_honoraires_item(item), item) for item in item_list]

    # For a real collection, every persisted line must carry an explicit payment
    # method before any Acte/Payment row is staged.
    if payment_status == models.PaiementStatut.PAYE:
        for _, item in validated_items:
            normalize_document_payment_method(item.get("mode_reglement"))

    actes: list[models.Acte] = []
    for (libelle, amount), _item in validated_items:
        acte = models.Acte(
            patient_id=patient_id,
            praticien_id=practitioner_id,
            type_acte=classify_acte_type(libelle),
            libelle=libelle,
            montant=amount,
            date_debut=document_created_at,
            statut_paiement=payment_status,
            is_accounted=is_accounted,
            is_collected=(payment_status == models.PaiementStatut.PAYE),
            document_archive_id=document_archive_id,
        )
        db.add(acte)
        actes.append(acte)

    db.flush()

    payments: list[models.Payment] = []
    if payment_status == models.PaiementStatut.PAYE:
        for ((_, amount), item), acte in zip(validated_items, actes):
            payment = models.Payment(
                patient_id=patient_id,
                amount=amount,
                payment_method=normalize_document_payment_method(item.get("mode_reglement")),
                payment_date=document_created_at,
                acte_id=acte.id,
                notes=f"Lien Doc ID: {document_archive_id}",
                validated_by=validated_by,
            )
            db.add(payment)
            payments.append(payment)

    return actes, payments
