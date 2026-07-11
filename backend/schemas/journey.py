import enum
import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class MilestoneType(str, enum.Enum):
    DIAGNOSTIC = "DIAGNOSTIC"
    DEVIS_VALIDE = "DEVIS_VALIDE"
    CONTROLE = "CONTROLE"
    CLOTURE = "CLOTURE"


class NavigationTarget(str, enum.Enum):
    DOCUMENT = "DOCUMENT"                    # ouverture via fetch authentifié + blob, jamais URL directe
    RADIOLOGY_TAB = "RADIOLOGY_TAB"
    TREATMENT_PLAN_TAB = "TREATMENT_PLAN_TAB"
    ACCOUNTING_TAB = "ACCOUNTING_TAB"
    LAB_PAGE = "LAB_PAGE"
    INLINE = "INLINE"                        # expansion locale, pas de navigation


class JourneyMilestoneCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    milestone_type: MilestoneType
    milestone_date: datetime.datetime
    note: Optional[str] = None
    confirm_duplicate: bool = False


class JourneyMilestoneOut(BaseModel):
    id: int
    milestone_type: MilestoneType
    milestone_date: datetime.datetime
    note: Optional[str] = None
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)


class JourneyMilestoneCreateResponse(BaseModel):
    milestone: Optional[JourneyMilestoneOut] = None
    possible_duplicate: bool = False
    existing_milestone_id: Optional[int] = None


class JourneyEventResponse(BaseModel):
    event_key: str          # ex. "document_archive:456" — stable, unique par ligne source
    source: str              # "appointment" | "treatment_plan_step" | "document_archive" |
                              # "panoramic_analysis" | "cephalo_analysis" | "payment" |
                              # "installment" | "lab_job" | "journey_milestone"
    type: str                 # sous-type lisible (ex. document_type pour un document)
    ref_id: int                # identité de la ligne source, utilisée par navigation_target
    date: datetime.datetime
    title: str
    status: str
    phase_hint: str
    navigation_target: NavigationTarget
    related_event_key: Optional[str] = None  # affichage groupé optionnel (radios), jamais un masquage


class JourneySummaryResponse(BaseModel):
    active_plan_steps: int
    total_plan_steps: int
    remaining_due: float
    has_billing_data: bool  # False si le patient n'a aucune ligne Acte — remaining_due n'est alors pas fiable
    next_appointment: Optional[datetime.datetime] = None
    last_document_date: Optional[datetime.datetime] = None


class PatientJourneyResponse(BaseModel):
    patient_id: int
    window_months: int
    truncated: bool
    total_events_available: int
    summary: JourneySummaryResponse
    events: List[JourneyEventResponse]
