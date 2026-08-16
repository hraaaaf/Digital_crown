from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from backend.schemas.installments import InstallmentUpdate
from backend.services.installment_integrity import (
    ensure_installment_plan_deletable,
    validate_updated_installment_amounts,
)


def _rows():
    return [
        SimpleNamespace(id=1, amount=400, status="EN_ATTENTE"),
        SimpleNamespace(id=2, amount=600, status="EN_ATTENTE"),
    ]


def test_update_amount_must_remain_positive_finite_and_bounded():
    for amount in (0, -1, 1_000_001, float("nan"), float("inf")):
        with pytest.raises(ValidationError):
            InstallmentUpdate(amount=amount)


def test_update_status_is_bounded_to_pending_or_paid():
    assert InstallmentUpdate(status="EN_ATTENTE").status == "EN_ATTENTE"
    assert InstallmentUpdate(status="PAYE", payment_method="TPE").status == "PAYE"
    with pytest.raises(ValidationError):
        InstallmentUpdate(status="ANNULE")


def test_payment_method_is_only_valid_on_paid_transition_payload():
    with pytest.raises(ValidationError):
        InstallmentUpdate(payment_method="CARTE")
    with pytest.raises(ValidationError):
        InstallmentUpdate(status="EN_ATTENTE", payment_method="CARTE")
    assert InstallmentUpdate(status="PAYE", payment_method="TPE").payment_method == "TPE"


def test_client_cannot_inject_paid_date():
    with pytest.raises(ValidationError):
        InstallmentUpdate(paid_date="2026-08-16T10:00:00")


def test_amount_edit_must_keep_plan_exactly_reconciled():
    validate_updated_installment_amounts(1000, _rows(), 1, 400)
    with pytest.raises(ValueError):
        validate_updated_installment_amounts(1000, _rows(), 1, 450)


def test_amount_edit_rejects_unknown_installment():
    with pytest.raises(ValueError):
        validate_updated_installment_amounts(1000, _rows(), 999, 400)


def test_plan_with_paid_history_cannot_be_deleted():
    with pytest.raises(ValueError):
        ensure_installment_plan_deletable(["EN_ATTENTE", "PAYE"], 0)
    with pytest.raises(ValueError):
        ensure_installment_plan_deletable(["EN_ATTENTE"], 1)


def test_fully_unpaid_plan_without_payment_history_can_be_deleted():
    ensure_installment_plan_deletable(["EN_ATTENTE", "EN_ATTENTE"], 0)
