import datetime
from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic_core import PydanticCustomError


class OdontogramType(str, Enum):
    ADULT = "ADULT"
    PEDIATRIC = "PEDIATRIC"


class SurfaceState(str, Enum):
    HEALTHY = "HEALTHY"
    CARIES = "CARIES"
    CARIES_TO_TREAT = "CARIES_TO_TREAT"
    FILLING_COMPOSITE = "FILLING_COMPOSITE"
    FILLING_AMALGAM = "FILLING_AMALGAM"
    FILLING_GOLD = "FILLING_GOLD"
    FILLING_CERAMIC = "FILLING_CERAMIC"
    RESTORED = "RESTORED"
    CROWN = "CROWN"
    CROWN_CERAMIC = "CROWN_CERAMIC"
    INLAY = "INLAY"
    ONLAY = "ONLAY"
    ROOT_CANAL = "ROOT_CANAL"
    POORLY_TREATED = "POORLY_TREATED"
    IMPLANT = "IMPLANT"
    IMPLANT_CROWN = "IMPLANT_CROWN"
    ABSENT = "ABSENT"
    ABUTMENT = "ABUTMENT"
    FRACTURE = "FRACTURE"
    SEALANT = "SEALANT"
    SELECTED = "SELECTED"


class ToothSurfaceState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    M: SurfaceState
    D: SurfaceState
    O: SurfaceState
    V: SurfaceState
    P: SurfaceState


ADULT_TEETH = {
    11, 12, 13, 14, 15, 16, 17, 18,
    21, 22, 23, 24, 25, 26, 27, 28,
    31, 32, 33, 34, 35, 36, 37, 38,
    41, 42, 43, 44, 45, 46, 47, 48,
}
PEDIATRIC_TEETH = {
    51, 52, 53, 54, 55,
    61, 62, 63, 64, 65,
    71, 72, 73, 74, 75,
    81, 82, 83, 84, 85,
}


class OdontogramUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dentition_type: OdontogramType
    state: Dict[int, ToothSurfaceState]
    expected_revision: int = Field(ge=0)

    @field_validator("state")
    @classmethod
    def reject_empty_or_non_fdi_state(cls, value: Dict[int, ToothSurfaceState]):
        if not value:
            raise PydanticCustomError(
                "odontogram_empty",
                "L'odontogramme ne peut pas être vide",
            )
        return value

    @model_validator(mode="after")
    def validate_tooth_set(self):
        allowed = ADULT_TEETH if self.dentition_type == OdontogramType.ADULT else PEDIATRIC_TEETH
        received = set(self.state.keys())
        if not received.issubset(allowed):
            invalid = sorted(received - allowed)
            raise PydanticCustomError(
                "odontogram_fdi_incompatible",
                "Numéro(s) FDI incompatible(s) avec la dentition: {invalid}",
                {"invalid": invalid},
            )
        return self


class OdontogramOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    dentition_type: OdontogramType
    state: Dict[int, ToothSurfaceState]
    revision: int
    updated_by: Optional[int] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
