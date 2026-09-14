import math
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


MedicationAllergyStatus = Literal["UNKNOWN", "NONE_KNOWN", "PRESENT"]
PenicillinAllergyStatus = Literal["UNKNOWN", "NONE_KNOWN", "PRESENT"]
OrganContextStatus = Literal["UNKNOWN", "NO_KNOWN_IMPAIRMENT", "IMPAIRMENT_REPORTED"]
IECardiacRiskCategory = Literal[
    "UNKNOWN",
    "NONE_REPORTED",
    "OTHER_CARDIAC_CONDITION",
    "PROSTHETIC_CARDIAC_VALVE",
    "PROSTHETIC_MATERIAL_FOR_CARDIAC_VALVE_REPAIR",
    "PREVIOUS_INFECTIVE_ENDOCARDITIS",
    "UNREPAIRED_CYANOTIC_CONGENITAL_HEART_DISEASE",
    "REPAIRED_CHD_WITH_RESIDUAL_SHUNT_OR_VALVULAR_REGURGITATION_AT_PROSTHETIC_PATCH_OR_DEVICE",
    "CARDIAC_TRANSPLANT_WITH_VALVE_REGURGITATION_DUE_STRUCTURALLY_ABNORMAL_VALVE",
]


def _clean_optional_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


class PatientClinicalContextUpdate(BaseModel):
    """Full practitioner-entered durable patient context state.

    No field in this schema implies that a prescription rule is clinically ready.
    Prescription-specific indication is intentionally owned by the ordonnance document.
    """

    model_config = ConfigDict(extra="forbid")

    weight_kg: Optional[float] = None
    medication_allergy_status: MedicationAllergyStatus = "UNKNOWN"
    medication_allergies: Optional[List[str]] = None
    penicillin_allergy_status: PenicillinAllergyStatus = "UNKNOWN"
    ie_cardiac_risk_category: IECardiacRiskCategory = "UNKNOWN"
    renal_context_status: OrganContextStatus = "UNKNOWN"
    renal_context_note: Optional[str] = None
    hepatic_context_status: OrganContextStatus = "UNKNOWN"
    hepatic_context_note: Optional[str] = None

    @field_validator("weight_kg")
    @classmethod
    def validate_weight(cls, value: Optional[float]) -> Optional[float]:
        if value is None:
            return None
        if not math.isfinite(value) or value <= 0:
            raise ValueError("Le poids doit être une valeur finie strictement positive")
        return value

    @field_validator("medication_allergies")
    @classmethod
    def normalize_allergies(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is None:
            return None
        cleaned: List[str] = []
        seen = set()
        for item in value:
            label = str(item).strip()
            if not label:
                raise ValueError("Une allergie renseignée ne peut pas être vide")
            key = label.casefold()
            if key not in seen:
                seen.add(key)
                cleaned.append(label)
        return cleaned

    @field_validator("renal_context_note", "hepatic_context_note", mode="before")
    @classmethod
    def normalize_optional_text(cls, value):
        return _clean_optional_text(value)

    @model_validator(mode="after")
    def validate_state_consistency(self):
        allergies = self.medication_allergies or []
        if self.medication_allergy_status == "PRESENT" and not allergies:
            raise ValueError("Le statut PRESENT exige au moins une allergie médicamenteuse explicite")
        if self.medication_allergy_status != "PRESENT" and allergies:
            raise ValueError("Des allergies ne peuvent être listées que lorsque le statut est PRESENT")
        if self.medication_allergy_status == "NONE_KNOWN":
            self.medication_allergies = []
        elif self.medication_allergy_status == "UNKNOWN":
            self.medication_allergies = None

        if self.renal_context_status != "IMPAIRMENT_REPORTED" and self.renal_context_note:
            raise ValueError("Une note rénale exige le statut IMPAIRMENT_REPORTED")
        if self.hepatic_context_status != "IMPAIRMENT_REPORTED" and self.hepatic_context_note:
            raise ValueError("Une note hépatique exige le statut IMPAIRMENT_REPORTED")
        return self


class PatientClinicalContextOut(PatientClinicalContextUpdate):
    patient_id: int
    employer_id: int
    updated_at: Optional[datetime] = None
    updated_by_user_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True, extra="forbid")
