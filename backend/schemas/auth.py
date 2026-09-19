from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional
import datetime

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128


def _password_field(default=...):
    return Field(default, min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1, max_length=4096)


class TokenData(BaseModel):
    email: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserSignup(BaseModel):
    email: EmailStr
    password: str = _password_field()
    nom_complet: str = Field(min_length=2, max_length=160)
    telephone_mobile: Optional[str] = Field(default=None, max_length=40)
    adresse_complete: Optional[str] = Field(default=None, max_length=500)
    accept_terms: bool
    accept_privacy: bool


class TrialActivationRequest(BaseModel):
    code: str = Field(min_length=6, max_length=128)
    email: EmailStr
    password: str = _password_field()
    nom_complet: str = Field(min_length=2, max_length=160)
    cabinet_name: Optional[str] = Field(default=None, max_length=160)
    accept_terms: bool
    accept_privacy: bool


class TrialActivationPreview(BaseModel):
    email: EmailStr
    nom_complet: Optional[str] = None
    cabinet_name: Optional[str] = None
    trial_days: int
    expires_at: datetime.datetime


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str
    is_superadmin: bool = False
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
    password: str = _password_field()
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
    new_password: Optional[str] = _password_field(None)
    permissions: Optional[dict] = None


class TeamMemberOut(BaseModel):
    id: int
    email: str
    role: str
    nom_complet: Optional[str] = None
    telephone_mobile: Optional[str] = None
    is_active: bool
    approval_status: str = "approved"
    approval_note: Optional[str] = None
    created_at: Optional[datetime.datetime] = None
    permissions: Optional[dict] = None
    model_config = ConfigDict(from_attributes=True)


class QuotaOut(BaseModel):
    plan: str
    dentistes_used: int
    dentistes_max: Optional[int] = None
    secretaires_used: int
    secretaires_max: Optional[int] = None
    pending_count: int
    can_add_dentiste: bool
    can_add_secretaire: bool


class SupabaseSyncRequest(BaseModel):
    access_token: str
    email: EmailStr
