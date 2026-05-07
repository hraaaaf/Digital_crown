from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
import datetime
from typing import Optional, Dict, Union


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
    model_config = ConfigDict(from_attributes=True)


class DossierOut(BaseModel):
    id: int
    is_ortho_active: bool
    note_honnetete: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class PatientBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    numero_dossier: Optional[str] = None
    nom: str
    prenom: str
    date_naissance: Union[datetime.datetime, datetime.date, str]
    sexe: str
    email: Optional[EmailStr] = Field(None, validate_default=True)
    telephone: Optional[str] = None
    adresse: Optional[str] = None
    assurance: Optional[str] = "AUCUNE"
    photo_url: Optional[str] = None
    antecedents_medicaux: Optional[str] = None
    employer_id: Optional[int] = None

    @field_validator('sexe', mode='before')
    @classmethod
    def normalize_sexe(cls, v):
        if not v: return "M"
        v_upper = str(v).upper()
        if "HOMME" in v_upper or "MASC" in v_upper or v_upper.startswith("M"):
            return "M"
        if "FEMME" in v_upper or "GARC" in v_upper or v_upper.startswith("F"):
            return "M" if "GARC" in v_upper else "F"
        return "F" if "F" in v_upper else "M"

    @field_validator('date_naissance', mode='before')
    @classmethod
    def parse_date_naissance(cls, v):
        if isinstance(v, datetime.datetime):
            return v
        if isinstance(v, datetime.date):
            return datetime.datetime.combine(v, datetime.time.min)
        if isinstance(v, str):
            try:
                return datetime.datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                try:
                    d = datetime.date.fromisoformat(v)
                    return datetime.datetime.combine(d, datetime.time.min)
                except ValueError:
                    raise ValueError("Format de date invalide (ISO attendu)")
        return v

    @field_validator('email', mode='before')
    @classmethod
    def empty_string_to_none(cls, v):
        if v == "" or v is None:
            return None
        return v


class PatientUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    numero_dossier: Optional[str] = None
    nom: Optional[str] = None
    prenom: Optional[str] = None
    date_naissance: Optional[Union[datetime.datetime, datetime.date, str]] = None
    sexe: Optional[str] = None
    email: Optional[EmailStr] = Field(None, validate_default=True)
    telephone: Optional[str] = None
    adresse: Optional[str] = None
    assurance: Optional[str] = None
    photo_url: Optional[str] = None
    antecedents_medicaux: Optional[str] = None


class PatientCreate(PatientBase):
    pass


class PatientOut(PatientBase):
    id: int
    numero_dossier: Optional[str] = None
    created_at: datetime.datetime
    dossier: Optional[DossierOut] = None
    employer_id: int
    model_config = ConfigDict(from_attributes=True)
