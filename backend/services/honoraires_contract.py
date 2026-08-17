from __future__ import annotations

import math
from typing import Any


MAX_HONORAIRES_LINE_AMOUNT = 1_000_000.0


def validate_honoraires_document_data(data: Any) -> Any:
    """Fail closed before PDF generation/archive for invariant P4 data.

    Payment-method validation deliberately stays out of this pre-PDF layer because
    an EN_ATTENTE note has no collection yet. The request/persistence boundaries
    require an explicit method only when payment_status is PAYE.

    If a note carries installments, every due date must already be explicit and
    valid at this boundary. Financial dates must never be synthesized from runtime
    time as a fallback.
    """
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

    installments = list(getattr(data, "installments", []) or [])
    for index, installment in enumerate(installments, start=1):
        if getattr(installment, "date", None) is None:
            raise ValueError(
                f"Échéance #{index} : une date explicite est requise ; aucune date financière ne peut être inventée."
            )

    return data
