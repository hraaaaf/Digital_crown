from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class PaymentCreate(BaseModel):
    patient_id: int
    amount: float
    payment_method: str = "ESPECES"
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
    
    model_config = ConfigDict(from_attributes=True)
