from __future__ import annotations

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


def normalize_document_payment_method(value: Any) -> str:
    normalized = str(value or "Espèces").strip().upper()
    method = _PAYMENT_METHOD_ALIASES.get(normalized)
    if method is None:
        raise ValueError("Mode de paiement invalide")
    return method


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
    """Stage Acte rows and exact linked payments in the caller transaction.

    No commit is performed here. The caller owns the transaction and can rollback
    the complete document/accounting mutation if any line or payment is invalid.
    """
    item_list = list(items)
    actes: list[models.Acte] = []

    for item in item_list:
        libelle = item.get("acte") or "Acte"
        amount = float(item.get("montant", 0))
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
        for item, acte in zip(item_list, actes):
            amount = float(item.get("montant", 0))
            if amount <= 0:
                continue
            payment = models.Payment(
                patient_id=patient_id,
                amount=amount,
                payment_method=normalize_document_payment_method(item.get("mode_reglement", "Espèces")),
                payment_date=document_created_at,
                acte_id=acte.id,
                notes=f"Lien Doc ID: {document_archive_id}",
                validated_by=validated_by,
            )
            db.add(payment)
            payments.append(payment)

    return actes, payments
