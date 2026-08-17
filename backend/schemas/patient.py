from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
import datetime
from typing import Optional, Dict, Union, List


class PraticienProfileOut(BaseModel):
    nom_complet: str
    nom: Optional[str] = None
    specialites: Optional[str] = None
    adresse_complete: Optional[str] = None
    adresse: Optional[str] = None
    telephone_fixe: Optional[str] = None
    telephone: Optional[str] = None
    telephone_mobile: Optional[str] = None
    identifiants_legaux: Optional[Dict[str, str]] = None
    inpe: Optional[str] = None
    header_lines_fr: Optional[List[str]] = None
    header_lines_ar: Optional[List[str]] = None
    specialty_ids: Optional[List[str]] = None
    model_config = ConfigDict(from_attributes=True)


class DossierOut(BaseModel):
    id: int
    is_ortho_active: bool
    note_honnetete: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


def _normalize_explicit_sexe(value: str) -> str:
    """Normalize only explicit, unambiguous sex values.

    Patient identity data must never be inferred from an empty or unknown value.
    """
    normalized = str(value).strip().upper()
    male_values = {"M", "HOMME", "MASCULIN", "GARCON", "GARÇON"}
    female_values = {"F", "FEMME", "FEMININ", "FÉMININ", "FILLE"}
    if normalized in male_values:
        return "M"
    if normalized in female_values:
        return "F"
    raise ValueError("Sexe invalide : valeur explicite M ou F requise")


class PatientBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    numero_dossier: Optional[str] = None
    nom: str
    prenom: str
    date_naissance: Union[datetime.datetime, datetime.date, str]
    sexe: str
    email: Optional[EmailStr] = Field(None, validate_default=True)
    telephone: Optional[str] = None
    telephone_2: Optional[str] = None
    telephone_3: Optional[str] = None
    adresse: Optional[str] = None
    assurance: Optional[str] = "AUCUNE"
    assurance_privee_nom: Optional[str] = None
    assurance_complementaire: Optional[bool] = False
    assurance_complementaire_nom: Optional[str] = None
    photo_url: Optional[str] = None
    antecedents_medicaux: Optional[str] = None
    motif_consultation: Optional[str] = None
    employer_id: Optional[int] = None

    @field_validator("sexe", mode="before")
    @classmethod
    def normalize_sexe(cls, value):
        if value is None or not str(value).strip():
            raise ValueError("Sexe requis : valeur explicite M ou F attendue")
        return _normalize_explicit_sexe(value)

    @field_validator("date_naissance", mode="before")
    @classmethod
    def parse_date_naissance(cls, v):
        if isinstance(v, datetime.datetime):
            return v
        if isinstance(v, datetime.date):
            return datetime.datetime.combine(v, datetime.time.min)
        if isinstance(v, str):
            try:
                return datetime.datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                try:
                    d = datetime.date.fromisoformat(v)
                    return datetime.datetime.combine(d, datetime.time.min)
                except ValueError:
                    raise ValueError("Format de date invalide (ISO attendu)")
        return v

    @field_validator("email", mode="before")
    @classmethod
    def empty_string_to_none(cls, v):
        if v == "" or v is None:
            return None
        return v


class PatientUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    numero_dossier: Optional[str] = None
    nom: Optional[str] = None
    prenom: Optional[str] = None
    date_naissance: Optional[Union[datetime.datetime, datetime.date, str]] = None
    sexe: Optional[str] = None
    email: Optional[EmailStr] = Field(None, validate_default=True)
    telephone: Optional[str] = None
    telephone_2: Optional[str] = None
    telephone_3: Optional[str] = None
    adresse: Optional[str] = None
    assurance: Optional[str] = None
    assurance_privee_nom: Optional[str] = None
    assurance_complementaire: Optional[bool] = None
    assurance_complementaire_nom: Optional[str] = None
    photo_url: Optional[str] = None
    antecedents_medicaux: Optional[str] = None
    motif_consultation: Optional[str] = None
    is_ortho_active: Optional[bool] = None

    @field_validator("sexe", mode="before")
    @classmethod
    def normalize_optional_sexe(cls, value):
        if value is None:
            return None
        if not str(value).strip():
            raise ValueError("Sexe invalide : valeur explicite M ou F attendue")
        return _normalize_explicit_sexe(value)


class PatientCreate(PatientBase):
    is_ortho_active: Optional[bool] = False


class PatientOut(PatientBase):
    id: int
    numero_dossier: Optional[str] = None
    created_at: datetime.datetime
    dossier: Optional[DossierOut] = None
    employer_id: int
    model_config = ConfigDict(from_attributes=True)


class TreatmentPlanStepBase(BaseModel):
    title: str
    assistant: str
    status: str = "pending"
    date_str: str = "Aujourd'hui"
    order_index: int = 0


class TreatmentPlanStepCreate(TreatmentPlanStepBase):
    pass


class TreatmentPlanStepOut(TreatmentPlanStepBase):
    id: int
    plan_id: int
    model_config = ConfigDict(from_attributes=True)


class TreatmentMasterPlanOut(BaseModel):
    id: int
    patient_id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    steps: List[TreatmentPlanStepOut] = []
    model_config = ConfigDict(from_attributes=True)
