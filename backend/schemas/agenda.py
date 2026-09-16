from pydantic import BaseModel, ConfigDict, Field, model_validator
import datetime
from typing import Optional, List
from enum import Enum


class AgendaMode(str, Enum):
    EXACT = "EXACT"
    BLOCK = "BLOCK"


def _time_to_minutes(value: str) -> int:
    try:
        hour_text, minute_text = value.split(":", 1)
        hour = int(hour_text)
        minute = int(minute_text)
    except (TypeError, ValueError):
        raise ValueError("Les horaires doivent utiliser le format HH:MM.")
    if not (0 <= hour <= 23 and 0 <= minute <= 59 and len(value) == 5):
        raise ValueError("Les horaires doivent utiliser le format HH:MM.")
    return hour * 60 + minute


class AgendaDaySchedule(BaseModel):
    is_open: bool = True
    is_continuous: bool = False
    morning_start: str = "09:00"
    morning_end: str = "13:00"
    afternoon_start: str = "14:00"
    afternoon_end: str = "18:00"

    @model_validator(mode="after")
    def validate_ranges(self):
        if not self.is_open:
            return self

        morning_start = _time_to_minutes(self.morning_start)
        morning_end = _time_to_minutes(self.morning_end)
        if morning_start >= morning_end:
            raise ValueError("L'heure de fin doit être après l'heure d'ouverture.")

        if self.is_continuous:
            return self

        afternoon_start = _time_to_minutes(self.afternoon_start)
        afternoon_end = _time_to_minutes(self.afternoon_end)
        if afternoon_start >= afternoon_end:
            raise ValueError("La fin d'après-midi doit être après son ouverture.")
        if morning_end > afternoon_start:
            raise ValueError("Les plages matin et après-midi ne peuvent pas se chevaucher.")
        return self


class WeeklyAgendaSchedule(BaseModel):
    monday: AgendaDaySchedule
    tuesday: AgendaDaySchedule
    wednesday: AgendaDaySchedule
    thursday: AgendaDaySchedule
    friday: AgendaDaySchedule
    saturday: AgendaDaySchedule
    sunday: AgendaDaySchedule


class CabinetSettingsBase(BaseModel):
    opening_time_morning: Optional[str] = "09:00"
    closing_time_morning: Optional[str] = "13:00"
    opening_time_afternoon: Optional[str] = "14:00"
    closing_time_afternoon: Optional[str] = "18:00"
    is_continuous: bool = False
    agenda_mode: AgendaMode = AgendaMode.EXACT
    use_tickets: bool = False
    weekly_schedule: Optional[WeeklyAgendaSchedule] = None


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

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("La date de fin doit être postérieure ou égale à la date de début.")
        return self


class AgendaExceptionCreate(AgendaExceptionBase):
    pass


class AgendaExceptionOut(AgendaExceptionBase):
    id: int
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)


class PractitionerTimeInterval(BaseModel):
    start: str
    end: str

    @model_validator(mode="after")
    def validate_interval(self):
        if _time_to_minutes(self.start) >= _time_to_minutes(self.end):
            raise ValueError("La fin d'une plage praticien doit être après son début.")
        return self


class PractitionerDaySchedule(BaseModel):
    intervals: List[PractitionerTimeInterval] = Field(default_factory=list, max_length=8)

    @model_validator(mode="after")
    def validate_intervals(self):
        ordered = sorted(self.intervals, key=lambda item: _time_to_minutes(item.start))
        for previous, current in zip(ordered, ordered[1:]):
            if _time_to_minutes(previous.end) > _time_to_minutes(current.start):
                raise ValueError("Les plages praticien ne peuvent pas se chevaucher.")
        self.intervals = ordered
        return self


class PractitionerWeeklySchedule(BaseModel):
    monday: PractitionerDaySchedule
    tuesday: PractitionerDaySchedule
    wednesday: PractitionerDaySchedule
    thursday: PractitionerDaySchedule
    friday: PractitionerDaySchedule
    saturday: PractitionerDaySchedule
    sunday: PractitionerDaySchedule


class PractitionerAgendaSettingsUpdate(BaseModel):
    weekly_schedule: PractitionerWeeklySchedule


class PractitionerAgendaSettingsOut(BaseModel):
    practitioner_id: int
    practitioner_name: str
    inherits_cabinet: bool
    weekly_schedule: Optional[PractitionerWeeklySchedule] = None
    updated_at: Optional[datetime.datetime] = None


class PractitionerAgendaSummaryOut(BaseModel):
    practitioner_id: int
    practitioner_name: str
    inherits_cabinet: bool


class PractitionerAgendaExceptionBase(BaseModel):
    start_date: datetime.datetime
    end_date: datetime.datetime
    reason: str = Field(default="Indisponibilité praticien", min_length=1, max_length=255)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date <= self.start_date:
            raise ValueError("La fin de l'indisponibilité doit être après son début.")
        return self


class PractitionerAgendaExceptionCreate(PractitionerAgendaExceptionBase):
    pass


class PractitionerAgendaExceptionOut(PractitionerAgendaExceptionBase):
    id: int
    practitioner_id: int
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)
