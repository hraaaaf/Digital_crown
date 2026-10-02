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
    ProcedureSafetyEvaluationOut,
    ProcedureSafetyEvaluationRequest,
)
from backend.services import cabinet_catalog_store as catalog_store
from backend.services import medication_dict
from backend.services.catalog_connected_truth import flatten_catalog_acts
from backend.services.prescription_clinical_rules import (
    IEProphylaxisAdultOralAmoxicillinInput,
    evaluate_ie_prophylaxis_adult_oral_amoxicillin,
)
from backend.services.prescription_procedure_safety import (
    AntithromboticProcedureSafetyInput,
    MRONJProcedureSafetyInput,
    orchestrate_procedure_safety,
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
            generic_medication_allergy_present=(
                context is not None and context.medication_allergy_status == "PRESENT"
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


@prescription_router.post(
    "/clinical-rules/procedure-safety/evaluate",
    response_model=ProcedureSafetyEvaluationOut,
)
def evaluate_procedure_safety_background(
    payload: ProcedureSafetyEvaluationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("prescriptions")),
):
    """Read-only N4.3B orchestration. No prescription or patient state is mutated."""
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

    presentation = (
        medication_dict.get_presentation(payload.presentation_id)
        if payload.presentation_id
        else None
    )
    active_ingredient_code = _amoxicillin_active_ingredient_code(presentation)

    ie_input = IEProphylaxisAdultOralAmoxicillinInput(
        age_years=_age_on_date(patient.date_naissance, payload.procedure_date),
        cardiac_risk_category=(
            context.ie_cardiac_risk_category if context is not None else "UNKNOWN"
        ),
        dental_procedure_qualifies=payload.ie_procedure_qualifies,
        penicillin_allergy_status=(
            context.penicillin_allergy_status if context is not None else "UNKNOWN"
        ),
        generic_medication_allergy_present=(
            context is not None and context.medication_allergy_status == "PRESENT"
        ),
        oral_route_possible=payload.oral_route_possible,
        currently_taking_penicillin_or_amoxicillin=payload.currently_taking_penicillin_or_amoxicillin,
        selected_active_ingredient_code=active_ingredient_code,
        selected_presentation_verified=presentation is not None,
    )

    if context is None:
        antithrombotic_status = "UNKNOWN"
        antithrombotic_classes = ()
        combination_therapy = "UNKNOWN"
        warfarin_inr = None
        warfarin_inr_current = None
        lmwh_dose_class = "UNKNOWN"
    else:
        anticoagulant_status = getattr(context, "anticoagulant_status", "UNKNOWN")
        antiplatelet_status = getattr(context, "antiplatelet_status", "UNKNOWN")
        if "PRESENT" in {anticoagulant_status, antiplatelet_status}:
            antithrombotic_status = "PRESENT"
        elif anticoagulant_status == "NONE_REPORTED" and antiplatelet_status == "NONE_REPORTED":
            antithrombotic_status = "NONE_REPORTED"
        else:
            antithrombotic_status = "UNKNOWN"
        antithrombotic_classes = tuple(getattr(context, "antithrombotic_classes", None) or ())
        combination_therapy = getattr(context, "antithrombotic_combination_status", "UNKNOWN")
        warfarin_inr = getattr(context, "warfarin_inr", None)
        warfarin_inr_current = getattr(context, "warfarin_inr_current", None)
        lmwh_dose_class = getattr(context, "lmwh_dose_class", "UNKNOWN")

    if context is None:
        mronj_medication_status = "UNKNOWN"
        mronj_agent_class = "UNKNOWN"
        mronj_indication = "UNKNOWN"
        mronj_route = "UNKNOWN"
        mronj_duration_months = None
        mronj_concurrent_risk_therapy = ()
        active_oral_infection_or_inflammation = "UNKNOWN"
        suspected_or_known_mronj = "UNKNOWN"
    else:
        mronj_medication_status = getattr(context, "mronj_medication_status", "UNKNOWN")
        mronj_agent_class = getattr(context, "mronj_agent_class", "UNKNOWN")
        mronj_indication = getattr(context, "mronj_indication", "UNKNOWN")
        mronj_route = getattr(context, "mronj_route", "UNKNOWN")
        mronj_duration_months = getattr(context, "mronj_duration_months", None)
        mronj_concurrent_risk_therapy = tuple(
            getattr(context, "mronj_concurrent_risk_therapy", None) or ()
        )
        active_oral_infection_or_inflammation = getattr(
            context, "active_oral_infection_or_inflammation", "UNKNOWN"
        )
        suspected_or_known_mronj = getattr(context, "suspected_or_known_mronj", "UNKNOWN")

    result = orchestrate_procedure_safety(
        AntithromboticProcedureSafetyInput(
            procedure_bleeding_risk=payload.procedure_bleeding_risk,
            antithrombotic_status=antithrombotic_status,
            antithrombotic_classes=antithrombotic_classes,
            combination_therapy=combination_therapy,
            warfarin_inr=warfarin_inr,
            warfarin_inr_current=warfarin_inr_current,
            lmwh_dose_class=lmwh_dose_class,
        ),
        ie_input,
        MRONJProcedureSafetyInput(
            procedure_osseous_risk=payload.procedure_osseous_risk,
            procedure_is_implant=payload.procedure_is_implant,
            medication_status=mronj_medication_status,
            agent_class=mronj_agent_class,
            indication=mronj_indication,
            route=mronj_route,
            duration_months=mronj_duration_months,
            concurrent_risk_therapy=mronj_concurrent_risk_therapy,
            active_oral_infection_or_inflammation=active_oral_infection_or_inflammation,
            suspected_or_known_mronj=suspected_or_known_mronj,
        ),
    )

    return ProcedureSafetyEvaluationOut(
        status=result.status,
        alert_key=result.alert_key,
        read_only=True,
    )




@prescription_router.get(
    "/clinical-rules/procedure-safety/alert/{patient_id}",
    response_model=ProcedureSafetyEvaluationOut,
)
def read_procedure_safety_alert(
    patient_id: int,
    presentation_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("prescriptions")),
):
    """Return only the generic practitioner alert derived from hidden backoffice context."""
    assert_patient_access(patient_id, current_user, db)
    employer_id = current_user.get_employer_id()
    context = db.query(PatientClinicalContext).filter(
        PatientClinicalContext.patient_id == patient_id,
        PatientClinicalContext.employer_id == employer_id,
    ).first()

    if context is None or getattr(context, "procedure_date", None) is None:
        return ProcedureSafetyEvaluationOut(status="READY", alert_key=None, read_only=True)

    payload = ProcedureSafetyEvaluationRequest(
        patient_id=patient_id,
        procedure_date=context.procedure_date,
        procedure_bleeding_risk=getattr(context, "procedure_bleeding_risk", "UNKNOWN"),
        procedure_osseous_risk=getattr(context, "procedure_osseous_risk", "UNKNOWN"),
        procedure_is_implant=getattr(context, "procedure_is_implant", None),
        ie_procedure_qualifies=getattr(context, "ie_procedure_qualifies", None),
        oral_route_possible=getattr(context, "oral_route_possible", None),
        currently_taking_penicillin_or_amoxicillin=getattr(
            context, "currently_taking_penicillin_or_amoxicillin", None
        ),
        presentation_id=presentation_id,
    )
    return evaluate_procedure_safety_background(payload, db=db, current_user=current_user)


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
