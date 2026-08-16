from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic_core import PydanticCustomError

from backend.utils.installment_reconciliation import validate_installments


InstallmentStatus = Literal["EN_ATTENTE", "PAYE"]
PaymentMethod = Literal["ESPECES", "CARTE", "CHEQUE", "VIREMENT"]


class InstallmentPreviewItem(BaseModel):
    label: str = Field(min_length=1, max_length=200)
    amount: float = Field(gt=0, le=1_000_000, allow_inf_nan=False)
    due_date: str = Field(min_length=10, max_length=40)
    paid: bool = False


class InstallmentPreviewRequest(BaseModel):
    patient_id: int
    title: str = Field(min_length=1, max_length=200)
    total_amount: float = Field(gt=0, le=10_000_000, allow_inf_nan=False)
    items: List[InstallmentPreviewItem] = Field(min_length=1)

    @model_validator(mode="after")
    def reconcile_preview_total(self):
        try:
            validate_installments(self.total_amount, [item.amount for item in self.items])
        except (TypeError, ValueError) as exc:
            raise PydanticCustomError("installment_total_mismatch", str(exc)) from exc
        return self


class InstallmentBase(BaseModel):
    label: str = Field(min_length=1, max_length=200)
    amount: float = Field(gt=0, le=1_000_000, allow_inf_nan=False)
    due_date: datetime
    paid_date: Optional[datetime] = None
    status: InstallmentStatus = "EN_ATTENTE"
    notes: Optional[str] = Field(default=None, max_length=2000)


class InstallmentCreate(InstallmentBase):
    pass


class InstallmentUpdate(BaseModel):
    label: Optional[str] = Field(default=None, min_length=1, max_length=200)
    amount: Optional[float] = Field(default=None, gt=0, le=1_000_000, allow_inf_nan=False)
    due_date: Optional[datetime] = None
    paid_date: Optional[datetime] = None
    status: Optional[InstallmentStatus] = None
    notes: Optional[str] = Field(default=None, max_length=2000)
    payment_method: Optional[PaymentMethod] = None


class InstallmentResponse(InstallmentBase):
    id: int
    plan_id: int
    model_config = ConfigDict(from_attributes=True)


class InstallmentPlanBase(BaseModel):
    patient_id: int
    title: str = Field(min_length=1, max_length=200)
    total_amount: float = Field(gt=0, le=10_000_000, allow_inf_nan=False)


class InstallmentPlanCreate(InstallmentPlanBase):
    installments: List[InstallmentCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def reconcile_plan_total(self):
        try:
            validate_installments(self.total_amount, [item.amount for item in self.installments])
        except (TypeError, ValueError) as exc:
            raise PydanticCustomError("installment_total_mismatch", str(exc)) from exc
        return self


class InstallmentPlanResponse(InstallmentPlanBase):
    id: int
    created_at: datetime
    updated_at: datetime
    installments: List[InstallmentResponse] = []
    model_config = ConfigDict(from_attributes=True)
