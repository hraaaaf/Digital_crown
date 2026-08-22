"""P4B schemas for the canonical practitioner identity owned by User."""
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional


class PractitionerIdentityUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nom_complet: Optional[str] = Field(default=None, min_length=2, max_length=255)
    nom_complet_ar: Optional[str] = Field(default=None, max_length=255)
    inpe_professionnel: Optional[str] = Field(default=None, max_length=50)

    @field_validator("nom_complet", "nom_complet_ar", "inpe_professionnel")
    @classmethod
    def normalize_text(cls, value: Optional[str], info):
        if value is None:
            return None
        normalized = value.strip()
        if info.field_name == "nom_complet" and not normalized:
            raise ValueError("Le nom du praticien ne peut pas être vide.")
        return normalized or None


class PractitionerIdentityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    nom_complet: Optional[str] = None
    nom_complet_ar: Optional[str] = None
    inpe_professionnel: Optional[str] = None
