from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Literal, Optional
from datetime import datetime

PaymentMethodCode = Literal["ESPECES", "CARTE", "VIREMENT", "CHEQUE"]

_PAYMENT_METHOD_ALIASES = {
    "ESPECES": "ESPECES",
    "ESPÈCES": "ESPECES",
    "CARTE": "CARTE",
    "TPE": "CARTE",
    "VIREMENT": "VIREMENT",
    "CHEQUE": "CHEQUE",
    "CHÈQUE": "CHEQUE",
}


class PaymentCreate(BaseModel):
    patient_id: int
    amount: float = Field(gt=0)
    payment_method: PaymentMethodCode = "ESPECES"
    payment_date: Optional[datetime] = None
    acte_id: Optional[int] = None
    installment_id: Optional[int] = None
    notes: Optional[str] = None

    @field_validator("payment_method", mode="before")
    @classmethod
    def normalize_payment_method(cls, value):
        if value is None:
            return "ESPECES"
        normalized = str(value).strip().upper()
        if normalized not in _PAYMENT_METHOD_ALIASES:
            raise ValueError("Mode de paiement invalide")
        return _PAYMENT_METHOD_ALIASES[normalized]


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
