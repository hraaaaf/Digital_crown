from datetime import datetime

import pytest
from pydantic import ValidationError

from backend.schemas.installments import (
    InstallmentPlanCreate,
    InstallmentPreviewRequest,
    InstallmentUpdate,
)


def _item(amount: float, status: str = "EN_ATTENTE"):
    return {
        "label": "Mensualité",
        "amount": amount,
        "due_date": datetime(2026, 9, 1),
        "status": status,
    }


def test_plan_requires_exact_reconciliation():
    valid = InstallmentPlanCreate(
        patient_id=1,
        title="Plan orthodontique",
        total_amount=1000,
        installments=[_item(333.33), _item(333.33), _item(333.34)],
    )
    assert sum(item.amount for item in valid.installments) == pytest.approx(1000)

    with pytest.raises(ValidationError, match="total"):
        InstallmentPlanCreate(
            patient_id=1,
            title="Plan orthodontique",
            total_amount=1000,
            installments=[_item(400), _item(400)],
        )


def test_plan_rejects_non_positive_or_unknown_status():
    with pytest.raises(ValidationError):
        InstallmentPlanCreate(
            patient_id=1,
            title="Plan",
            total_amount=100,
            installments=[_item(0)],
        )
    with pytest.raises(ValidationError):
        InstallmentPlanCreate(
            patient_id=1,
            title="Plan",
            total_amount=100,
            installments=[_item(100, "ANNULE")],
        )


def test_update_contract_is_closed():
    with pytest.raises(ValidationError):
        InstallmentUpdate(amount=-10)
    with pytest.raises(ValidationError):
        InstallmentUpdate(status="PARTIEL")
    assert InstallmentUpdate(status="PAYE", payment_method="CARTE").status == "PAYE"


def test_preview_is_also_reconciled():
    InstallmentPreviewRequest(
        patient_id=1,
        title="Plan",
        total_amount=200,
        items=[
            {"label": "A", "amount": 100, "due_date": "2026-09-01"},
            {"label": "B", "amount": 100, "due_date": "2026-10-01"},
        ],
    )
    with pytest.raises(ValidationError):
        InstallmentPreviewRequest(
            patient_id=1,
            title="Plan",
            total_amount=200,
            items=[{"label": "A", "amount": 150, "due_date": "2026-09-01"}],
        )
