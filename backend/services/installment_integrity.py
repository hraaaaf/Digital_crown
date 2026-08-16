from __future__ import annotations

from collections.abc import Iterable

from backend.utils.installment_reconciliation import validate_installments


def validate_updated_installment_amounts(
    plan_total: float,
    installments: Iterable[object],
    target_installment_id: int,
    proposed_amount: float,
) -> None:
    """Require an edited pending installment to keep the whole plan reconciled."""
    amounts: list[float] = []
    found = False
    for installment in installments:
        installment_id = int(getattr(installment, "id"))
        if installment_id == int(target_installment_id):
            amounts.append(float(proposed_amount))
            found = True
        else:
            amounts.append(float(getattr(installment, "amount")))
    if not found:
        raise ValueError("Échéance introuvable dans le plan.")
    validate_installments(plan_total, amounts)


def ensure_installment_plan_deletable(
    installment_statuses: Iterable[str],
    linked_payment_count: int,
) -> None:
    """Never erase the plan structure once real collection history exists."""
    normalized = {str(status or "").strip().upper() for status in installment_statuses}
    if "PAYE" in normalized or int(linked_payment_count) > 0:
        raise ValueError(
            "Un plan contenant un règlement réel ne peut pas être supprimé. "
            "Conservez-le pour la traçabilité financière."
        )
