"""Compatibility facade for prescriptions + tenant-scoped clinical act catalog.

The certified prescription implementation remains byte-for-byte in
``prescriptions_core.py``. Only catalog search/quick-add are replaced so care
flows consume and write the R6 cabinet catalog instead of the legacy global one.

Prescription Intelligence C2 also mounts a read-only rule evaluation endpoint.
It never mutates an ordonnance or patient, never infers from free text and never
reuses the legacy smart-suggest/safety engines.
"""

from datetime import date, datetime
from typing import Optional

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Patient, User
from backend.models_patient_clinical_context import PatientClinicalContext
from backend.routers.auth import get_current_user, require_permission
from backend.schemas.prescription_clinical_rules import (
    ClinicalRuleEvaluationOut,
    IEProphylaxisEvaluationRequest,
)
from backend.services import cabinet_catalog_store as catalog_store
from backend.services import medication_dict
from backend.services.catalog_connected_truth import flatten_catalog_acts
from backend.services.prescription_clinical_rules import (
    IEProphylaxisAdultOralAmoxicillinInput,
    evaluate_ie_prophylaxis_adult_oral_amoxicillin,
)
from backend.utils.access_control import assert_patient_access
from . import prescriptions_core as _core
from .prescriptions_core import *  # noqa: F401,F403 - compatibility facade

prescription_router = _core.prescription_router
actes_router = _core.actes_router

# Replace only the legacy global catalog endpoints. All care persistence,
# attachments, audit and prescription routes stay delegated to the certified core.
actes_router.routes = [
    route
    for route in actes_router.routes
    if not (
        (getattr(route, "path", None) == "/catalog/search" and "GET" in (getattr(route, "methods", set()) or set()))
        or (getattr(route, "path", None) == "/catalog/quick-add" and "POST" in (getattr(route, "methods", set()) or set()))
    )
]


def _age_on_date(date_naissance: Optional[datetime], procedure_date: date) -> Optional[int]:
    if date_naissance is None:
        return None
    born = date_naissance.date() if isinstance(date_naissance, datetime) else date_naissance
    if procedure_date < born:
        return None
    return procedure_date.year - born.year - (
        (procedure_date.month, procedure_date.day) < (born.month, born.day)
    )


def _amoxicillin_active_ingredient_code(presentation: Optional[dict]) -> Optional[str]:
    """Map only a single-ingredient documentary DCI to the C2 canonical code.

    Associations (e.g. amoxicillin/clavulanate), brands without exact DCI, and any
    other documentary value remain blocked.
    """
    if not presentation:
        return None
    dci = str(presentation.get("dci") or "").strip().upper()
    if dci in {"AMOXICILLINE", "AMOXICILLIN"}:
        return "AMOXICILLIN"
    return None


@prescription_router.post(
    "/clinical-rules/ie-prophylaxis/evaluate",
    response_model=ClinicalRuleEvaluationOut,
)
def evaluate_ie_prophylaxis_rule(
    payload: IEProphylaxisEvaluationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("prescriptions")),
):
    """Evaluate C2 rule 1 without persisting or autofilling any prescription.

    Durable cardiac/allergy facts come only from the structured patient context.
    Procedure/route/current-antibiotic facts are explicit request-scoped inputs.
    The selected presentation is resolved server-side by its stable documentary id.
    """
    assert_patient_access(payload.patient_id, current_user, db)
    employer_id = current_user.get_employer_id()

    patient = db.query(Patient).filter(
        Patient.id == payload.patient_id,
        Patient.employer_id == employer_id,
    ).first()
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient introuvable")

    context = db.query(PatientClinicalContext).filter(
        PatientClinicalContext.patient_id == payload.patient_id,
        PatientClinicalContext.employer_id == employer_id,
    ).first()

    presentation = medication_dict.get_presentation(payload.presentation_id)
    active_ingredient_code = _amoxicillin_active_ingredient_code(presentation)

    result = evaluate_ie_prophylaxis_adult_oral_amoxicillin(
        IEProphylaxisAdultOralAmoxicillinInput(
            age_years=_age_on_date(patient.date_naissance, payload.procedure_date),
            cardiac_risk_category=(
                context.ie_cardiac_risk_category if context is not None else "UNKNOWN"
            ),
            dental_procedure_qualifies=payload.dental_procedure_qualifies,
            penicillin_allergy_status=(
                context.penicillin_allergy_status if context is not None else "UNKNOWN"
            ),
            oral_route_possible=payload.oral_route_possible,
            currently_taking_penicillin_or_amoxicillin=payload.currently_taking_penicillin_or_amoxicillin,
            selected_active_ingredient_code=active_ingredient_code,
            selected_presentation_verified=presentation is not None,
        )
    )

    return ClinicalRuleEvaluationOut(
        status=result.status,
        rule_id=result.rule_id,
        rule_version=result.rule_version,
        blockers=list(result.blockers),
        active_ingredient_code=result.active_ingredient_code,
        total_dose_mg=result.total_dose_mg,
        timing_min_minutes_before=result.timing_min_minutes_before,
        timing_max_minutes_before=result.timing_max_minutes_before,
        single_dose=result.single_dose,
        source_ids=list(result.source_ids),
    )


@actes_router.get("/catalog/search")
def search_catalog_acts(
    q: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Preserve the existing q/response contract, backed only by this cabinet."""
    tenant_id = current_user.get_employer_id()
    catalog = catalog_store.list_catalog(db, tenant_id)
    return flatten_catalog_acts(catalog, query=q, limit=20)


@actes_router.post("/catalog/quick-add")
def quick_add_catalog_act(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("agenda")),
):
    """Quick-add into the same tenant catalog read by Settings and clinical care."""
    name = str(payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Nom d'acte requis")
    try:
        base_price = max(0.0, float(payload.get("base_price") or 0.0))
    except (TypeError, ValueError):
        base_price = 0.0

    tenant_id = current_user.get_employer_id()
    catalog = catalog_store.list_catalog(db, tenant_id)
    for specialty in catalog:
        for act in specialty.get("acts") or []:
            if str(act.get("name") or "").strip().casefold() == name.casefold():
                # Preserve the historical quick-add contract: an existing act is
                # returned as-is. Quick-add must never mutate its price or state.
                return {
                    "id": int(act["id"]),
                    "catalog_act_id": int(act["id"]),
                    "name": act["name"],
                    "code": act.get("code"),
                    "base_price": float(act.get("base_price") or 0.0),
                    "category": specialty.get("name") or "DIVERS",
                    "is_habit": False,
                }

    category = str(payload.get("category") or "").strip().upper() or "DIVERS"
    specialty = next(
        (row for row in catalog if str(row.get("name") or "").strip().casefold() == category.casefold()),
        None,
    )
    if specialty is None:
        specialty = catalog_store.create_specialty(db, tenant_id, {"name": category, "color": "#64748B"})

    act = catalog_store.create_act(
        db,
        tenant_id,
        int(specialty["id"]),
        {"name": name, "code": None, "base_price": base_price, "color": None, "is_active": True},
    )
    if not act:
        raise HTTPException(status_code=404, detail="Spécialité catalogue introuvable")
    return {
        "id": int(act["id"]),
        "catalog_act_id": int(act["id"]),
        "name": act["name"],
        "code": act.get("code"),
        "base_price": float(act.get("base_price") or 0.0),
        "category": specialty.get("name") or "DIVERS",
        "is_habit": False,
    }
