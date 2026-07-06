from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional, List
import datetime

class ClientBaseStats(BaseModel):
    total_patients: int = 0
    total_ia_panoramique: int = 0
    total_ia_cephalo: int = 0

class ClientOut(BaseModel):
    id: int
    email: EmailStr
    role: str
    nom_complet: Optional[str] = None
    is_active: bool
    is_licensed: bool
    license_expires_at: Optional[datetime.datetime] = None
    is_archived: bool
    is_suspended: bool
    internal_notes: Optional[str] = None
    last_login_at: Optional[datetime.datetime] = None
    created_at: Optional[datetime.datetime] = None
    
    stats: Optional[ClientBaseStats] = None

    model_config = ConfigDict(from_attributes=True)

class LicenseHistoryOut(BaseModel):
    id: int
    user_id: int
    action: str
    duration: Optional[int] = None
    timestamp: datetime.datetime
    admin_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class UpdateClientNotes(BaseModel):
    internal_notes: str

class SendRenewalEmailRequest(BaseModel):
    message: Optional[str] = None


class TrialActivationCodeCreate(BaseModel):
    email: EmailStr
    nom_complet: Optional[str] = None
    cabinet_name: Optional[str] = None
    trial_days: int = 30
    expires_in_days: int = 14
    notes: Optional[str] = None


class TrialActivationCodeOut(BaseModel):
    id: int
    code: str
    email: EmailStr
    nom_complet: Optional[str] = None
    cabinet_name: Optional[str] = None
    trial_days: int
    notes: Optional[str] = None
    expires_at: datetime.datetime
    consumed_at: Optional[datetime.datetime] = None
    revoked_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime
    activation_url: str

    model_config = ConfigDict(from_attributes=True)
