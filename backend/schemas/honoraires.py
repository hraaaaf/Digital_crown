from __future__ import annotations

import datetime
import math
from typing import List, Union

from pydantic import BaseModel, Field, model_validator
from pydantic_core import PydanticCustomError

from backend.utils.installment_reconciliation import validate_installments
from .documents import (
    DocumentRequest as LegacyDocumentRequest,
    InstallmentItem,
    ToothData,
)


_VALID_HONORAIRES_FDI = {
    *range(11, 19), *range(21, 29), *range(31, 39), *range(41, 49),
    *range(51, 56), *range(61, 66), *range(71, 76), *range(81, 86),
}

_PAYMENT_METHOD_CANONICAL = {
    "ESPECES": "Espèces",
    "ESPÈCES": "Espèces",
    "CASH": "Espèces",
    "TPE": "TPE",
    "CARTE": "TPE",
    "CHEQUE": "Chèque",
    "CHÈQUE": "Chèque",
    "VIREMENT": "Virement",
    "EN ATTENTE": "EN ATTENTE",
}


def _is_phase_separator(value: str) -> bool:
    normalized = (value or "").strip()
    return normalized.startswith("--- ") and normalized.endswith(" ---")


class PaymentItem(BaseModel):
    date: datetime.date | None = None
    acte: str = ""
    dent: str = "-"
    dents: List[Union[int, str]] = []
    montant: float = Field(default=0.0, ge=0, le=1_000_000)
    mode_reglement: str = "Espèces"

    @model_validator(mode="after")
    def validate_payment_item(self):
        self.acte = str(self.acte or "").strip()
        if not self.acte or _is_phase_separator(self.acte):
            raise PydanticCustomError(
                "honoraires_invalid_act",
                "Une ligne d'honoraires doit contenir un acte réel.",
            )

        amount = float(self.montant)
        if not math.isfinite(amount):
            raise PydanticCustomError(
                "honoraires_invalid_amount",
                "Le montant d'une ligne d'honoraires doit être fini.",
            )
        self.montant = amount

        normalized_dents: list[int] = []
        for value in self.dents:
            try:
                tooth = int(value)
            except (TypeError, ValueError) as exc:
                raise PydanticCustomError(
                    "honoraires_invalid_tooth",
                    f"Numéro de dent invalide : {value}.",
                ) from exc
            if tooth not in _VALID_HONORAIRES_FDI:
                raise PydanticCustomError(
                    "honoraires_invalid_tooth",
                    f"Numéro FDI hors référentiel adulte/pédiatrique : {tooth}.",
                )
            normalized_dents.append(tooth)

        self.dents = sorted(set(normalized_dents))
        if self.dents:
            self.dent = ", ".join(str(tooth) for tooth in self.dents)

        raw_method = str(self.mode_reglement or "Espèces").strip().upper()
        canonical_method = _PAYMENT_METHOD_CANONICAL.get(raw_method)
        if canonical_method is None:
            raise PydanticCustomError(
                "honoraires_invalid_payment_method",
                "Mode de paiement invalide.",
            )
        self.mode_reglement = canonical_method
        return self


class HonorairesData(BaseModel):
    payments: List[PaymentItem] = []
    doc_date: datetime.date | None = None
    teeth_data: List[ToothData] = []
    age: int | None = None
    gender: str | None = None
    installments: List[InstallmentItem] = []
    is_global_note: bool = False

    @model_validator(mode="before")
    @classmethod
    def isolate_unique_note_installments(cls, value):
        if not isinstance(value, dict):
            return value
        sanitized = dict(value)
        if not bool(sanitized.get("is_global_note", False)):
            sanitized["installments"] = []
        return sanitized

    @model_validator(mode="after")
    def require_real_payment_lines(self):
        if not self.payments:
            raise PydanticCustomError(
                "honoraires_empty_payments",
                "La note d'honoraires doit contenir au moins un acte réel.",
            )
        return self

    @model_validator(mode="after")
    def require_consistent_teeth_data(self):
        if not self.teeth_data:
            return self

        item_pairs: dict[tuple[int, str], float] = {}
        for item in self.payments:
            normalized_name = item.acte.strip().casefold()
            for tooth in item.dents:
                item_pairs[(tooth, normalized_name)] = float(item.montant)

        for tooth_data in self.teeth_data:
            if tooth_data.tooth_number not in _VALID_HONORAIRES_FDI:
                raise PydanticCustomError(
                    "honoraires_invalid_teeth_data_tooth",
                    f"teeth_data contient un numéro FDI invalide : {tooth_data.tooth_number}.",
                )
            if not tooth_data.treatments:
                raise PydanticCustomError(
                    "honoraires_orphan_teeth_data",
                    f"teeth_data pour la dent {tooth_data.tooth_number} ne contient aucun acte de la note d'honoraires.",
                )
            for treatment in tooth_data.treatments:
                normalized_name = treatment.name.strip().casefold()
                key = (tooth_data.tooth_number, normalized_name)
                if not normalized_name or key not in item_pairs:
                    raise PydanticCustomError(
                        "honoraires_orphan_teeth_data",
                        f"teeth_data ne correspond à aucune ligne d'honoraires : dent {tooth_data.tooth_number}, acte '{treatment.name}'.",
                    )
                if abs(float(treatment.price) - item_pairs[key]) > 0.01:
                    raise PydanticCustomError(
                        "honoraires_teeth_data_price_mismatch",
                        f"Prix incohérent entre payments et teeth_data pour la dent {tooth_data.tooth_number}, acte '{treatment.name}'.",
                    )
        return self

    @model_validator(mode="after")
    def reconcile_global_installments(self):
        if not self.is_global_note or not self.installments:
            return self
        try:
            validate_installments(
                sum(float(payment.montant) for payment in self.payments),
                [float(item.amount) for item in self.installments],
            )
        except (TypeError, ValueError) as exc:
            raise PydanticCustomError("installment_total_mismatch", str(exc)) from exc
        return self


class DocumentRequest(LegacyDocumentRequest):
    """Document request with fail-closed Honoraires financial semantics.

    Unique notes must not inherit an installment plan previously loaded in the
    shared frontend store. A collection method is meaningful only for PAYE;
    pending notes are rendered/archived as EN ATTENTE instead of default cash.
    """

    @model_validator(mode="before")
    @classmethod
    def sanitize_honoraires_request(cls, value):
        if not isinstance(value, dict):
            return value
        if value.get("type") not in {"note", "honoraires"}:
            return value
        data = value.get("data")
        if not isinstance(data, dict):
            return value

        payment_status = str(value.get("payment_status") or "EN_ATTENTE").strip().upper()
        if payment_status not in {"EN_ATTENTE", "PAYE", "PARTIEL"}:
            raise PydanticCustomError(
                "honoraires_invalid_payment_status",
                "Statut de paiement invalide.",
            )

        sanitized_request = dict(value)
        sanitized_data = dict(data)
        if not bool(sanitized_data.get("is_global_note", False)):
            sanitized_data["installments"] = []

        if payment_status != "PAYE":
            sanitized_payments = []
            for payment in sanitized_data.get("payments") or []:
                if isinstance(payment, dict):
                    payment_copy = dict(payment)
                    payment_copy["mode_reglement"] = "EN ATTENTE"
                    sanitized_payments.append(payment_copy)
                else:
                    sanitized_payments.append(payment)
            sanitized_data["payments"] = sanitized_payments

        sanitized_request["data"] = sanitized_data
        return sanitized_request
