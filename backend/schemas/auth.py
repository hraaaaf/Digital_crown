from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional
import datetime


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str
    nom_complet: Optional[str] = None
    is_active: bool = True
    employer_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


class TeamMemberCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    password: str = Field(min_length=8)
    nom_complet: str = Field(min_length=2)
    telephone_mobile: Optional[str] = None


class TeamMemberUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nom_complet: Optional[str] = None
    email: Optional[EmailStr] = None
    telephone_mobile: Optional[str] = None
    is_active: Optional[bool] = None
    new_password: Optional[str] = Field(None, min_length=8)


class TeamMemberOut(BaseModel):
    id: int
    email: str
    role: str
    nom_complet: Optional[str] = None
    telephone_mobile: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime.datetime] = None
    model_config = ConfigDict(from_attributes=True)
