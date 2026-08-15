from decimal import Decimal

import pytest

from backend.utils.installment_reconciliation import (
    reconcile_installments,
    validate_installments,
)


def test_reconcile_installments_is_exact_to_cent():
    result = reconcile_installments(1000, [333.33, 333.33, 333.34])
    assert result.billed_total == Decimal("1000.00")
    assert result.installment_total == Decimal("1000.00")
    assert result.difference == Decimal("0.00")
    assert result.reconciled is True


def test_validate_installments_rejects_under_and_over_allocation():
    with pytest.raises(ValueError, match="exactement égale"):
        validate_installments(1000, [400, 500])
    with pytest.raises(ValueError, match="exactement égale"):
        validate_installments(1000, [600, 500])


def test_validate_installments_rejects_zero_or_negative_line():
    with pytest.raises(ValueError, match="strictement positif"):
        validate_installments(1000, [0, 1000])
    with pytest.raises(ValueError, match="strictement positif"):
        validate_installments(1000, [-50, 1050])


def test_validate_installments_accepts_exact_plan():
    result = validate_installments("999.99", ["333.33", "333.33", "333.33"])
    assert result.reconciled is True
