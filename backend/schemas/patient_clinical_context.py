import math
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


MedicationAllergyStatus = Literal["UNKNOWN", "NONE_KNOWN", "PRESENT"]
PenicillinAllergyStatus = Literal["UNKNOWN", "NONE_KNOWN", "PRESENT"]
OrganContextStatus = Literal["UNKNOWN", "NO_KNOWN_IMPAIRMENT", "IMPAIRMENT_REPORTED"]
BinaryFactStatus = Literal["UNKNOWN", "NO", "YES"]
CurrentMedicationsStatus = Literal["UNKNOWN", "NONE_REPORTED", "PRESENT"]
AntithromboticClass = Literal["VKA", "DOAC", "ANTIPLATELET", "LMWH", "OTHER"]
CombinationStatus = Literal["UNKNOWN", "NO", "YES"]
LMWHDoseClass = Literal["UNKNOWN", "PROPHYLACTIC", "TREATMENT"]
MRONJAgentClass = Literal["UNKNOWN", "BISPHOSPHONATE", "DENOSUMAB", "ROMOSOZUMAB", "ANTIANGIOGENIC", "OTHER"]
MRONJIndication = Literal["UNKNOWN", "OSTEOPOROSIS_NONMALIGNANT", "MALIGNANCY", "OTHER"]
MRONJRoute = Literal["UNKNOWN", "ORAL", "PARENTERAL", "OTHER"]
MRONJConcurrentRiskTherapy = Literal["CHEMOTHERAPY", "STEROID", "ANTIANGIOGENIC", "OTHER"]
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


def _clean_string_list(value: Optional[List[str]], message: str) -> Optional[List[str]]:
    if value is None:
        return None
    cleaned: List[str] = []
    seen = set()
    for item in value:
        label = str(item).strip()
        if not label:
            raise ValueError(message)
        key = label.casefold()
        if key not in seen:
            seen.add(key)
            cleaned.append(label)
    return cleaned


class PatientClinicalContextUpdate(BaseModel):
    """Practitioner-facing durable patient context.

    N4.3B antithrombotic procedure-safety facts are deliberately excluded from
    this contract and live behind the dedicated backoffice contract below.
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
    pregnancy_status: BinaryFactStatus = "UNKNOWN"
    breastfeeding_status: BinaryFactStatus = "UNKNOWN"
    current_medications_status: CurrentMedicationsStatus = "UNKNOWN"
    current_medications: Optional[List[str]] = None

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
        return _clean_string_list(value, "Une allergie renseignée ne peut pas être vide")

    @field_validator("current_medications")
    @classmethod
    def normalize_current_medications(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        return _clean_string_list(value, "Un traitement en cours renseigné ne peut pas être vide")

    @field_validator("renal_context_note", "hepatic_context_note", mode="before")
    @classmethod
    def normalize_optional_text(cls, value):
        return _clean_optional_text(value)

    @model_validator(mode="after")
    def validate_state_consistency(self):
        supplied = self.model_fields_set
        allergies = self.medication_allergies or []
        if {"medication_allergy_status", "medication_allergies"} <= supplied:
            if self.medication_allergy_status == "PRESENT" and not allergies:
                raise ValueError("Le statut PRESENT exige au moins une allergie médicamenteuse explicite")
            if self.medication_allergy_status != "PRESENT" and allergies:
                raise ValueError("Des allergies ne peuvent être listées que lorsque le statut est PRESENT")
        if self.renal_context_status != "IMPAIRMENT_REPORTED" and self.renal_context_note:
            raise ValueError("Une note rénale exige le statut IMPAIRMENT_REPORTED")
        if self.hepatic_context_status != "IMPAIRMENT_REPORTED" and self.hepatic_context_note:
            raise ValueError("Une note hépatique exige le statut IMPAIRMENT_REPORTED")

        treatments = self.current_medications or []
        if {"current_medications_status", "current_medications"} <= supplied:
            if self.current_medications_status == "PRESENT" and not treatments:
                raise ValueError("Le statut PRESENT exige au moins un traitement actuel explicite")
            if self.current_medications_status != "PRESENT" and treatments:
                raise ValueError("Des traitements actuels ne peuvent être listés que lorsque le statut est PRESENT")
        return self


class PatientClinicalContextOut(PatientClinicalContextUpdate):
    patient_id: int
    employer_id: int
    updated_at: Optional[datetime] = None
    updated_by_user_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class PatientProcedureSafetyContextUpdate(BaseModel):
    """Backoffice-only structured facts for N4.3B procedure-sensitive safety."""

    model_config = ConfigDict(extra="forbid")

    anticoagulant_status: CurrentMedicationsStatus = "UNKNOWN"
    anticoagulants: Optional[List[str]] = None
    antiplatelet_status: CurrentMedicationsStatus = "UNKNOWN"
    antiplatelets: Optional[List[str]] = None
    antithrombotic_classes: Optional[List[AntithromboticClass]] = None
    antithrombotic_combination_status: CombinationStatus = "UNKNOWN"
    warfarin_inr: Optional[float] = None
    warfarin_inr_checked_at: Optional[datetime] = None
    warfarin_inr_current: Optional[bool] = None
    lmwh_dose_class: LMWHDoseClass = "UNKNOWN"

    mronj_medication_status: CurrentMedicationsStatus = "UNKNOWN"
    mronj_agents: Optional[List[str]] = None
    mronj_agent_class: MRONJAgentClass = "UNKNOWN"
    mronj_indication: MRONJIndication = "UNKNOWN"
    mronj_route: MRONJRoute = "UNKNOWN"
    mronj_duration_months: Optional[int] = None
    mronj_concurrent_risk_therapy: Optional[List[MRONJConcurrentRiskTherapy]] = None
    active_oral_infection_or_inflammation: BinaryFactStatus = "UNKNOWN"
    suspected_or_known_mronj: BinaryFactStatus = "UNKNOWN"

    @field_validator("anticoagulants", "antiplatelets", "mronj_agents")
    @classmethod
    def normalize_agents(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        return _clean_string_list(value, "Un traitement antithrombotique renseigné ne peut pas être vide")

    @field_validator("antithrombotic_classes", "mronj_concurrent_risk_therapy")
    @classmethod
    def normalize_enum_lists(cls, value):
        if value is None:
            return None
        return list(dict.fromkeys(value))

    @field_validator("mronj_duration_months")
    @classmethod
    def validate_mronj_duration(cls, value: Optional[int]) -> Optional[int]:
        if value is None:
            return None
        if value < 0:
            raise ValueError("Durée MRONJ invalide")
        return value

    @field_validator("warfarin_inr")
    @classmethod
    def validate_warfarin_inr(cls, value: Optional[float]) -> Optional[float]:
        if value is None:
            return None
        if not math.isfinite(value) or value <= 0:
            raise ValueError("INR invalide")
        return value

    @model_validator(mode="after")
    def validate_state_consistency(self):
        for status_field, list_field in (
            ("anticoagulant_status", "anticoagulants"),
            ("antiplatelet_status", "antiplatelets"),
        ):
            status = getattr(self, status_field)
            values = getattr(self, list_field) or []
            if status == "PRESENT" and not values:
                raise ValueError(f"{status_field}=PRESENT exige une liste explicite")
            if status != "PRESENT" and values:
                raise ValueError(f"{list_field} exige {status_field}=PRESENT")

        classes = self.antithrombotic_classes or []
        has_antithrombotic = (
            self.anticoagulant_status == "PRESENT"
            or self.antiplatelet_status == "PRESENT"
        )
        if classes and not has_antithrombotic:
            raise ValueError("Des classes antithrombotiques exigent un traitement antithrombotique PRESENT")
        if self.warfarin_inr is not None and "VKA" not in classes:
            raise ValueError("Un INR exige la classe VKA")
        if self.warfarin_inr_checked_at is not None and self.warfarin_inr is None:
            raise ValueError("La date INR exige une valeur INR")
        if self.warfarin_inr_current is not None and self.warfarin_inr is None:
            raise ValueError("Le statut de validité INR exige une valeur INR")
        if self.lmwh_dose_class != "UNKNOWN" and "LMWH" not in classes:
            raise ValueError("La classe de dose HBPM exige LMWH")
        if self.antithrombotic_combination_status == "YES" and not (
            len(classes) > 1
            or (
                self.anticoagulant_status == "PRESENT"
                and self.antiplatelet_status == "PRESENT"
            )
        ):
            raise ValueError("Le statut combinaison YES exige une combinaison explicite")

        mronj_agents = self.mronj_agents or []
        if self.mronj_medication_status == "PRESENT" and not mronj_agents:
            raise ValueError("Le statut MRONJ PRESENT exige au moins un agent explicite")
        if self.mronj_medication_status != "PRESENT" and mronj_agents:
            raise ValueError("Les agents MRONJ exigent le statut PRESENT")
        if self.mronj_medication_status != "PRESENT":
            if self.mronj_agent_class != "UNKNOWN" or self.mronj_indication != "UNKNOWN" or self.mronj_route != "UNKNOWN":
                raise ValueError("Les détails MRONJ exigent le statut PRESENT")
            if self.mronj_duration_months is not None or self.mronj_concurrent_risk_therapy:
                raise ValueError("Les facteurs MRONJ exigent le statut PRESENT")
        return self


class PatientProcedureSafetyContextOut(PatientProcedureSafetyContextUpdate):
    patient_id: int
    employer_id: int
    updated_at: Optional[datetime] = None
    updated_by_user_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True, extra="forbid")
