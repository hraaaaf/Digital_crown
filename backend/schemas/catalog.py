from pydantic import BaseModel, Field
import datetime
from typing import Optional, List, Literal

# --- Pathologies ---
class PathologyBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True

class PathologyCreate(PathologyBase):
    pass

class PathologyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class PathologyOut(PathologyBase):
    id: int
    specialty_id: int

    class Config:
        from_attributes = True

# --- Catalog Acts ---
class CatalogActApplicability(BaseModel):
    dentitions: List[Literal["PRIMARY", "PERMANENT"]] = Field(default_factory=list)
    tooth_types: List[Literal["INCISOR", "CANINE", "PREMOLAR", "MOLAR"]] = Field(default_factory=list)
    treatment_areas: List[Literal["SURFACE", "TOOTH", "TOOTH_RANGE", "QUADRANT", "ARCH", "MOUTH"]] = Field(default_factory=list)
    selection_modes: List[Literal["INDIVIDUAL", "GROUP", "GENERAL"]] = Field(default_factory=list)
    requires_present_tooth: bool = False
    requires_missing_tooth: bool = False
    min_selected_teeth: int = Field(default=0, ge=0)
    max_selected_teeth: Optional[int] = Field(default=None, ge=1)
    age_min: Optional[int] = Field(default=None, ge=0, le=120)
    age_max: Optional[int] = Field(default=None, ge=0, le=120)
    suggestion_priority: int = Field(default=0, ge=0, le=100)
    searchable_when_not_suggested: bool = True

class CatalogActBase(BaseModel):
    name: str
    code: Optional[str] = None
    base_price: float = 0.0
    color: Optional[str] = None
    is_active: bool = True
    is_favorite: bool = False
    applicability: CatalogActApplicability = Field(default_factory=CatalogActApplicability)

class CatalogActCreate(CatalogActBase):
    pass

class CatalogActUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    base_price: Optional[float] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None
    is_favorite: Optional[bool] = None
    applicability: Optional[CatalogActApplicability] = None

class CatalogActOut(CatalogActBase):
    id: int
    specialty_id: int
    usage_count: int = 0
    last_used_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True

# --- Specialties ---
class SpecialtyBase(BaseModel):
    name: str
    color: Optional[str] = None

class SpecialtyCreate(SpecialtyBase):
    pass

class SpecialtyUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None

class SpecialtyOut(SpecialtyBase):
    id: int
    pathologies: List[PathologyOut] = []
    acts: List[CatalogActOut] = []

    class Config:
        from_attributes = True
