from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

CENT = Decimal("0.01")


def _money(value: float | int | str | Decimal) -> Decimal:
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class InstallmentReconciliation:
    billed_total: Decimal
    installment_total: Decimal
    difference: Decimal

    @property
    def reconciled(self) -> bool:
        return self.difference == Decimal("0.00")


def reconcile_installments(
    billed_total: float | int | str | Decimal,
    installment_amounts: Iterable[float | int | str | Decimal],
) -> InstallmentReconciliation:
    billed = _money(billed_total)
    amounts = [_money(amount) for amount in installment_amounts]
    total = sum(amounts, Decimal("0.00")).quantize(CENT, rounding=ROUND_HALF_UP)
    return InstallmentReconciliation(
        billed_total=billed,
        installment_total=total,
        difference=(total - billed).quantize(CENT, rounding=ROUND_HALF_UP),
    )


def validate_installments(
    billed_total: float | int | str | Decimal,
    installment_amounts: Iterable[float | int | str | Decimal],
) -> InstallmentReconciliation:
    billed = _money(billed_total)
    amounts = [_money(amount) for amount in installment_amounts]
    if billed < 0:
        raise ValueError("Le total facturé est invalide.")
    if not amounts:
        raise ValueError("Ajoutez au moins une échéance.")
    if any(amount <= 0 for amount in amounts):
        raise ValueError("Chaque échéance doit avoir un montant strictement positif.")

    result = reconcile_installments(billed, amounts)
    if not result.reconciled:
        raise ValueError(
            "La somme des échéances doit être exactement égale au total facturé "
            f"(écart: {result.difference} MAD)."
        )
    return result
