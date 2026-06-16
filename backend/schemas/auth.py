from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional
import datetime


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenData(BaseModel):
    email: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserSignup(BaseModel):
    email: EmailStr
    password: str = Field(min_length=4)
    nom_complet: str = Field(min_length=2)
    telephone_mobile: Optional[str] = None
    adresse_complete: Optional[str] = None
    accept_terms: bool
    accept_privacy: bool


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str
    nom_complet: Optional[str] = None
    is_active: bool = True
    employer_id: Optional[int] = None
    permissions: Optional[dict] = None
    is_licensed: Optional[bool] = None
    license_expires_at: Optional[datetime.datetime] = None
    model_config = ConfigDict(from_attributes=True)


class TeamMemberCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    password: str = Field(min_length=4)
    nom_complet: str = Field(min_length=2)
    role: Optional[str] = "SECRETAIRE"
    telephone_mobile: Optional[str] = None
    permissions: Optional[dict] = None


class TeamMemberUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nom_complet: Optional[str] = None
    email: Optional[EmailStr] = None
    telephone_mobile: Optional[str] = None
    is_active: Optional[bool] = None
    new_password: Optional[str] = Field(None, min_length=4)
    permissions: Optional[dict] = None


class TeamMemberOut(BaseModel):
    id: int
    email: str
    role: str
    nom_complet: Optional[str] = None
    telephone_mobile: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime.datetime] = None
    permissions: Optional[dict] = None
    model_config = ConfigDict(from_attributes=True)


class SupabaseSyncRequest(BaseModel):
    access_token: str
    email: EmailStr

