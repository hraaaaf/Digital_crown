from pydantic import BaseModel, ConfigDict
from typing import List, Literal, Optional
from datetime import datetime


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
    pass


class InstallmentUpdate(BaseModel):
    label: Optional[str] = None
    amount: Optional[float] = None
    due_date: Optional[datetime] = None
    paid_date: Optional[datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    payment_method: Optional[Literal["ESPECES", "CARTE", "CHEQUE", "VIREMENT"]] = None


class InstallmentResponse(InstallmentBase):
    id: int
    plan_id: int
    model_config = ConfigDict(from_attributes=True)


class InstallmentPlanBase(BaseModel):
    patient_id: int
    title: str
    total_amount: float


class InstallmentPlanCreate(InstallmentPlanBase):
    installments: List[InstallmentCreate]


class InstallmentPlanResponse(InstallmentPlanBase):
    id: int
    created_at: datetime
    updated_at: datetime
    installments: List[InstallmentResponse] = []
    model_config = ConfigDict(from_attributes=True)
