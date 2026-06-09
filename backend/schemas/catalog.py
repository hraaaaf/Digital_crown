from pydantic import BaseModel, Field
from typing import Optional, List

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
class CatalogActBase(BaseModel):
    name: str
    code: Optional[str] = None
    base_price: float = 0.0
    color: Optional[str] = None
    is_active: bool = True

class CatalogActCreate(CatalogActBase):
    pass

class CatalogActUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    base_price: Optional[float] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None

class CatalogActOut(CatalogActBase):
    id: int
    specialty_id: int

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
