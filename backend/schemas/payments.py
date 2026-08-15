from pydantic import BaseModel, ConfigDict, Field
from typing import Literal, Optional
from datetime import datetime

PaymentMethodCode = Literal["ESPECES", "CARTE", "VIREMENT", "CHEQUE"]


class PaymentCreate(BaseModel):
    patient_id: int
    amount: float = Field(gt=0)
    payment_method: PaymentMethodCode = "ESPECES"
    payment_date: Optional[datetime] = None
    acte_id: Optional[int] = None
    installment_id: Optional[int] = None
    notes: Optional[str] = None


class PaymentOut(BaseModel):
    id: int
    patient_id: int
    amount: float
    payment_method: str
    payment_date: datetime
    acte_id: Optional[int]
    installment_id: Optional[int]
    notes: Optional[str]
    validated_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
