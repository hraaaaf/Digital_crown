from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Iterable

CENT = Decimal("0.01")


def _money(value) -> Decimal:
    try:
        amount = Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("Montant financier invalide.") from exc
    if not amount.is_finite() or amount < 0:
        raise ValueError("Montant financier invalide.")
    return amount


@dataclass(frozen=True)
class FullPaymentAllocation:
    line_index: int
    amount: Decimal


def build_full_payment_allocations(line_amounts: Iterable[float]) -> list[FullPaymentAllocation]:
    allocations: list[FullPaymentAllocation] = []
    for index, raw_amount in enumerate(line_amounts):
        amount = _money(raw_amount)
        if amount <= 0:
            continue
        allocations.append(FullPaymentAllocation(line_index=index, amount=amount))
    return allocations


def allocated_total(allocations: Iterable[FullPaymentAllocation]) -> Decimal:
    return sum((allocation.amount for allocation in allocations), Decimal("0.00")).quantize(
        CENT,
        rounding=ROUND_HALF_UP,
    )
