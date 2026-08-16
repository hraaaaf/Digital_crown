from __future__ import annotations

import math
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic_core import PydanticCustomError

from backend.utils.installment_reconciliation import validate_installments


MAX_FINANCIAL_AMOUNT = 1_000_000.0


class InstallmentPreviewItem(BaseModel):
    label: str
    amount: float
    due_date: str
    paid: bool = False


class InstallmentPreviewRequest(BaseModel):
    patient_id: int
    title: str
    total_amount: float
    items: List[InstallmentPreviewItem]


class InstallmentBase(BaseModel):
    label: str
    amount: float
    due_date: datetime
    paid_date: Optional[datetime] = None
    status: str = "EN_ATTENTE"
    notes: Optional[str] = None


class InstallmentCreate(InstallmentBase):
    amount: float = Field(gt=0, le=MAX_FINANCIAL_AMOUNT)
    status: Literal["EN_ATTENTE"] = "EN_ATTENTE"
    paid_date: None = None

    @model_validator(mode="after")
    def validate_new_installment(self):
        self.label = str(self.label or "").strip()
        if not self.label:
            raise PydanticCustomError(
                "installment_empty_label",
                "Le libellé d'une échéance ne peut pas être vide.",
            )
        if not math.isfinite(float(self.amount)):
            raise PydanticCustomError(
                "installment_invalid_amount",
                "Le montant d'une échéance doit être fini.",
            )
        return self


class InstallmentUpdate(BaseModel):
    label: Optional[str] = None
    amount: Optional[float] = Field(default=None, gt=0, le=MAX_FINANCIAL_AMOUNT)
    due_date: Optional[datetime] = None
    paid_date: None = None
    status: Optional[Literal["EN_ATTENTE", "PAYE"]] = None
    notes: Optional[str] = None
    payment_method: Optional[Literal["ESPECES", "CARTE", "TPE", "CHEQUE", "VIREMENT"]] = None

    @model_validator(mode="after")
    def validate_installment_update(self):
        if self.label is not None:
            self.label = self.label.strip()
            if not self.label:
                raise PydanticCustomError(
                    "installment_empty_label",
                    "Le libellé d'une échéance ne peut pas être vide.",
                )
        if self.amount is not None and not math.isfinite(float(self.amount)):
            raise PydanticCustomError(
                "installment_invalid_amount",
                "Le montant d'une échéance doit être fini.",
            )
        if self.payment_method is not None and self.status != "PAYE":
            raise PydanticCustomError(
                "installment_payment_method_without_payment",
                "Un mode de paiement ne peut être fourni que lors du règlement de l'échéance.",
            )
        return self


class InstallmentResponse(InstallmentBase):
    id: int
    plan_id: int
    model_config = ConfigDict(from_attributes=True)


class InstallmentPlanBase(BaseModel):
    patient_id: int
    title: str
    total_amount: float


class InstallmentPlanCreate(InstallmentPlanBase):
    total_amount: float = Field(gt=0, le=MAX_FINANCIAL_AMOUNT)
    installments: List[InstallmentCreate]

    @model_validator(mode="after")
    def validate_new_plan(self):
        self.title = str(self.title or "").strip()
        if not self.title:
            raise PydanticCustomError(
                "installment_plan_empty_title",
                "Le titre du plan de paiement ne peut pas être vide.",
            )
        if not math.isfinite(float(self.total_amount)):
            raise PydanticCustomError(
                "installment_plan_invalid_total",
                "Le total du plan de paiement doit être fini.",
            )
        try:
            validate_installments(
                self.total_amount,
                [installment.amount for installment in self.installments],
            )
        except ValueError as exc:
            raise PydanticCustomError(
                "installment_plan_total_mismatch",
                str(exc),
            ) from exc
        return self


class InstallmentPlanResponse(InstallmentPlanBase):
    id: int
    created_at: datetime
    updated_at: datetime
    installments: List[InstallmentResponse] = []
    model_config = ConfigDict(from_attributes=True)
