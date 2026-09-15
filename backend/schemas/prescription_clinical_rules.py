from datetime import date
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict


class IEProphylaxisEvaluationRequest(BaseModel):
    """Prescription-scoped explicit inputs for read-only C2 evaluation."""

    model_config = ConfigDict(extra="forbid")

    patient_id: int
    procedure_date: date
    dental_procedure_qualifies: Optional[bool] = None
    oral_route_possible: Optional[bool] = None
    currently_taking_penicillin_or_amoxicillin: Optional[bool] = None
    presentation_id: str


class ClinicalRuleEvaluationOut(BaseModel):
    status: Literal["BLOCKED", "READY"]
    rule_id: str
    rule_version: str
    blockers: List[str]
    active_ingredient_code: Optional[str] = None
    total_dose_mg: Optional[int] = None
    timing_min_minutes_before: Optional[int] = None
    timing_max_minutes_before: Optional[int] = None
    single_dose: Optional[bool] = None
    source_ids: List[str]
