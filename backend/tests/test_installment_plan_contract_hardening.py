import math

import pytest
from pydantic import ValidationError

from backend.schemas.installments import InstallmentCreate, InstallmentPlanCreate


def _installment(**overrides):
    value = {
        "label": "Versement 1",
        "amount": 500,
        "due_date": "2026-09-01T00:00:00",
        "status": "EN_ATTENTE",
    }
    value.update(overrides)
    return value


def _plan(**overrides):
    value = {
        "patient_id": 1,
        "title": "Plan de paiement",
        "total_amount": 1000,
        "installments": [
            _installment(label="Avance", amount=500),
            _installment(label="Versement 2", amount=500, due_date="2026-10-01T00:00:00"),
        ],
    }
    value.update(overrides)
    return value


def test_new_installment_requires_positive_finite_bounded_amount():
    for amount in (0, -1, 1_000_001, float("nan"), float("inf")):
        with pytest.raises(ValidationError):
            InstallmentCreate(**_installment(amount=amount))


def test_new_installment_requires_real_label():
    with pytest.raises(ValidationError):
        InstallmentCreate(**_installment(label="   "))


def test_new_installment_must_start_pending_without_paid_date():
    with pytest.raises(ValidationError):
        InstallmentCreate(**_installment(status="PAYE"))
    with pytest.raises(ValidationError):
        InstallmentCreate(**_installment(paid_date="2026-08-16T10:00:00"))


def test_plan_requires_positive_finite_bounded_total_and_real_title():
    for total in (0, -1, 1_000_001, float("nan"), float("inf")):
        with pytest.raises(ValidationError):
            InstallmentPlanCreate(**_plan(total_amount=total))
    with pytest.raises(ValidationError):
        InstallmentPlanCreate(**_plan(title="  "))


def test_plan_requires_at_least_one_installment():
    with pytest.raises(ValidationError):
        InstallmentPlanCreate(**_plan(installments=[]))


def test_plan_requires_exact_installment_reconciliation():
    with pytest.raises(ValidationError):
        InstallmentPlanCreate(
            **_plan(
                total_amount=1000,
                installments=[
                    _installment(label="Avance", amount=400),
                    _installment(label="Versement 2", amount=500),
                ],
            )
        )


def test_plan_accepts_exact_cent_reconciliation():
    plan = InstallmentPlanCreate(
        **_plan(
            total_amount=1000,
            installments=[
                _installment(label="Avance", amount=333.33),
                _installment(label="Versement 2", amount=333.33),
                _installment(label="Versement 3", amount=333.34),
            ],
        )
    )
    assert math.isclose(sum(item.amount for item in plan.installments), 1000.0)
    assert all(item.status == "EN_ATTENTE" for item in plan.installments)
