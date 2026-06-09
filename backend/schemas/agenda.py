from pydantic import BaseModel, ConfigDict
import datetime
from typing import Optional, List
from enum import Enum

class AgendaMode(str, Enum):
    EXACT = "EXACT"
    BLOCK = "BLOCK"

class CabinetSettingsBase(BaseModel):
    opening_time_morning: Optional[str] = "09:00"
    closing_time_morning: Optional[str] = "13:00"
    opening_time_afternoon: Optional[str] = "14:00"
    closing_time_afternoon: Optional[str] = "18:00"
    is_continuous: bool = False
    agenda_mode: AgendaMode = AgendaMode.EXACT
    use_tickets: bool = False

class CabinetSettingsUpdate(CabinetSettingsBase):
    pass

class CabinetSettingsOut(CabinetSettingsBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class AgendaExceptionBase(BaseModel):
    start_date: datetime.datetime
    end_date: datetime.datetime
    reason: str
    is_holiday: bool = False

class AgendaExceptionCreate(AgendaExceptionBase):
    pass

class AgendaExceptionOut(AgendaExceptionBase):
    id: int
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)
