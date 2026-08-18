from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_core import PydanticCustomError
from typing import Literal, Optional
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import event
from sqlalchemy.orm import Session

from backend import models

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


@event.listens_for(Session, "before_commit")
def _validate_new_payment_entity_binding(session: Session) -> None:
    """Fail closed before any Payment can reference entities from another patient."""
    for payment in tuple(session.new):
        if not isinstance(payment, models.Payment):
            continue

        if payment.acte_id is not None and payment.installment_id is not None:
            session.expunge(payment)
            raise HTTPException(
                status_code=422,
                detail="Un paiement ne peut pas cibler simultanément un acte et une échéance.",
            )

        if payment.acte_id is not None:
            acte = session.get(models.Acte, payment.acte_id)
            if acte is None:
                session.expunge(payment)
                raise HTTPException(status_code=404, detail="Acte introuvable")
            if acte.patient_id != payment.patient_id:
                session.expunge(payment)
                raise HTTPException(
                    status_code=409,
                    detail="L'acte n'appartient pas au patient du paiement.",
                )

        if payment.installment_id is not None:
            installment = session.get(models.Installment, payment.installment_id)
            if installment is None:
                session.expunge(payment)
                raise HTTPException(status_code=404, detail="Échéance introuvable")
            plan = session.get(models.InstallmentPlan, installment.plan_id)
            if plan is None:
                session.expunge(payment)
                raise HTTPException(
                    status_code=409,
                    detail="Plan d'échéances introuvable pour cette échéance.",
                )
            if plan.patient_id != payment.patient_id:
                session.expunge(payment)
                raise HTTPException(
                    status_code=409,
                    detail="L'échéance n'appartient pas au patient du paiement.",
                )


class PaymentCreate(BaseModel):
    patient_id: int
    amount: float = Field(gt=0)
    payment_method: PaymentMethodCode
    payment_date: Optional[datetime] = None
    acte_id: Optional[int] = None
    installment_id: Optional[int] = None
    notes: Optional[str] = None

    @field_validator("payment_method", mode="before")
    @classmethod
    def normalize_payment_method(cls, value):
        if value is None or not str(value).strip():
            raise PydanticCustomError(
                "payment_method_required",
                "Le mode de paiement doit être choisi explicitement",
            )
        normalized = str(value).strip().upper()
        if normalized not in _PAYMENT_METHOD_ALIASES:
            raise PydanticCustomError(
                "invalid_payment_method",
                "Mode de paiement invalide",
            )
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
