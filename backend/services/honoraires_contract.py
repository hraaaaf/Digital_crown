from __future__ import annotations

import math
from typing import Any


MAX_HONORAIRES_LINE_AMOUNT = 1_000_000.0


def _field_was_explicitly_provided(item: Any, field_name: str) -> bool:
    fields_set = getattr(item, "model_fields_set", None)
    if fields_set is None:
        return True
    return field_name in fields_set


def validate_honoraires_document_data(data: Any) -> Any:
    """Fail closed before PDF generation/archive for P4 financial documents."""
    payments = list(getattr(data, "payments", []) or [])
    if not payments:
        raise ValueError("Une note d'honoraires doit contenir au moins un acte.")

    for index, item in enumerate(payments, start=1):
        label = str(getattr(item, "acte", "") or "").strip()
        if not label:
            raise ValueError(f"Acte #{index} : la description est requise.")

        try:
            amount = float(getattr(item, "montant", None))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Acte #{index} : montant non numérique.") from exc
        if not math.isfinite(amount):
            raise ValueError(f"Acte #{index} : le montant doit être fini.")
        if amount <= 0:
            raise ValueError(f"Acte #{index} : le montant doit être strictement positif.")
        if amount > MAX_HONORAIRES_LINE_AMOUNT:
            raise ValueError(f"Acte #{index} : le montant dépasse la limite autorisée.")

        # PaymentItem historically defaulted to Espèces. The field-set check makes
        # an omitted method distinguishable from an explicit practitioner choice.
        if not _field_was_explicitly_provided(item, "mode_reglement"):
            raise ValueError(f"Acte #{index} : le mode de règlement doit être choisi explicitement.")
        if not str(getattr(item, "mode_reglement", "") or "").strip():
            raise ValueError(f"Acte #{index} : le mode de règlement est requis.")

    return data
