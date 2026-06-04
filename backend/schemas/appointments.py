from pydantic import BaseModel, ConfigDict
import datetime
from typing import Optional, List

from .base import AppointmentStatus, SchedulingType


class AppointmentBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    patient_id: Optional[int] = None
    patient_name: Optional[str] = None
    datetime_start: datetime.datetime
    duration_minutes: int = 30
    motif: Optional[str] = None
    status: AppointmentStatus = AppointmentStatus.PREVU
    scheduling_type: SchedulingType = SchedulingType.EXACT_TIME
    notes: Optional[str] = None
    employer_id: Optional[int] = None
    reminder_sent: bool = False
    reminder_sent_at: Optional[datetime.datetime] = None
    ticket_number: Optional[int] = None


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    patient_id: Optional[int] = None
    patient_name: Optional[str] = None
    datetime_start: Optional[datetime.datetime] = None
    duration_minutes: Optional[int] = None
    motif: Optional[str] = None
    status: Optional[AppointmentStatus] = None
    scheduling_type: Optional[SchedulingType] = None
    notes: Optional[str] = None
    reminder_sent: Optional[bool] = None
    reminder_sent_at: Optional[datetime.datetime] = None
    ticket_number: Optional[int] = None


class AppointmentOut(AppointmentBase):
    id: int
    created_at: datetime.datetime
    employer_id: int
    model_config = ConfigDict(from_attributes=True)


class AppointmentImportItem(BaseModel):
    patient_name: str
    datetime_start: datetime.datetime
    duration_minutes: int
    notes: Optional[str] = None
    patient_id: Optional[int] = None
    status: AppointmentStatus = AppointmentStatus.PREVU
    scheduling_type: SchedulingType = SchedulingType.EXACT_TIME


class AppointmentBulkCreate(BaseModel):
    appointments: List[AppointmentImportItem]

class AppointmentSuggestionOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    patient_id: int
    motif: Optional[str] = None
    duration_minutes: int = 15
    notes: Optional[str] = None
