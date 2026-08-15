from decimal import Decimal

import pytest

from backend.services.payment_allocation import (
    allocated_total,
    build_full_payment_allocations,
)


def test_full_payment_allocates_exact_amount_per_positive_act_line():
    allocations = build_full_payment_allocations([700, 300.5, 0])

    assert [(item.line_index, item.amount) for item in allocations] == [
        (0, Decimal("700.00")),
        (1, Decimal("300.50")),
    ]
    assert allocated_total(allocations) == Decimal("1000.50")


def test_full_payment_preserves_cent_precision():
    allocations = build_full_payment_allocations([333.33, 333.33, 333.34])
    assert allocated_total(allocations) == Decimal("1000.00")


def test_full_payment_rejects_invalid_or_negative_amount():
    with pytest.raises(ValueError):
        build_full_payment_allocations([-1])
    with pytest.raises(ValueError):
        build_full_payment_allocations([float("nan")])
