from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from backend import database, models
from backend.routers.auth import get_current_user, require_permission
from backend.services.elite_manager import elite_manager
from backend.services.habits_engine import habits_engine
from backend.utils.access_control import assert_patient_access

router = APIRouter(tags=["Elite Intelligence"])

@router.get("/patient/{patient_id}")
async def get_patient_intelligence(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients"))
):
    """
    Récupère l'intelligence globale pour un patient (Résumé + Insights + Score).
    """
    assert_patient_access(patient_id, current_user, db)
    return await elite_manager.get_comprehensive_intelligence(
        db, 
        patient_id, 
        doctor_id=current_user.id
    )

@router.post("/patient/{patient_id}/audit")
async def audit_document_context(
    patient_id: int,
    context_type: str,
    doc_data: Dict[str, Any] = Body(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients"))
):
    """
    Audit spécifique d'un contexte de document (ex: audit d'une ordonnance en cours).
    """
    assert_patient_access(patient_id, current_user, db)
    return await elite_manager.get_comprehensive_intelligence(
        db,
        patient_id,
        context_type=context_type,
        doc_data=doc_data,
        doctor_id=current_user.id
    )

@router.get("/patient/{patient_id}/treatment-plan")
async def get_treatment_plan(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients"))
):
    """
    Génère et récupère le plan de traitement méthodique basé sur les dernières analyses.
    """
    assert_patient_access(patient_id, current_user, db)
    return await elite_manager.get_treatment_plan(db, patient_id)


@router.get("/briefing-j1")
def get_briefing_j1(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients"))
):
    """C2 — Briefing financier J-1 : patients de demain avec leurs soldes impayés."""
    employer_id = current_user.get_employer_id()
    tomorrow = datetime.now().date() + timedelta(days=1)
    tomorrow_start = datetime.combine(tomorrow, datetime.min.time())
    tomorrow_end = datetime.combine(tomorrow, datetime.max.time())

    appts = db.query(models.Appointment).join(models.Patient).filter(
        models.Patient.employer_id == employer_id,
        models.Appointment.datetime_start >= tomorrow_start,
        models.Appointment.datetime_start <= tomorrow_end,
        models.Appointment.status != "ANNULÉ"
    ).order_by(models.Appointment.datetime_start).all()

    result = []
    total_outstanding = 0.0
    seen_patient_ids = set()

    for appt in appts:
        if appt.patient_id in seen_patient_ids:
            continue
        seen_patient_ids.add(appt.patient_id)

        patient = db.query(models.Patient).filter(models.Patient.id == appt.patient_id).first()
        if not patient:
            continue

        solde = db.query(func.sum(models.Acte.montant)).filter(
            models.Acte.patient_id == appt.patient_id,
            models.Acte.statut_paiement == "EN_ATTENTE"
        ).scalar() or 0.0

        total_outstanding += solde
        result.append({
            "patient_id": appt.patient_id,
            "nom": patient.nom,
            "prenom": patient.prenom,
            "appointment_time": appt.datetime_start.strftime("%H:%M"),
            "motif": appt.motif or "",
            "solde_attente": round(float(solde), 2),
        })

    return {
        "date": tomorrow.isoformat(),
        "total_patients": len(result),
        "total_outstanding": round(total_outstanding, 2),
        "patients": result,
    }


@router.get("/forecast-semaine")
def get_forecast_semaine(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients"))
):
    """C1 — Forecast financier de la semaine courante."""
    employer_id = current_user.get_employer_id()
    today = datetime.now().date()
    week_end = today + timedelta(days=7)
    today_start = datetime.combine(today, datetime.min.time())
    week_end_dt = datetime.combine(week_end, datetime.max.time())

    appts = db.query(models.Appointment).join(models.Patient).filter(
        models.Patient.employer_id == employer_id,
        models.Appointment.datetime_start >= today_start,
        models.Appointment.datetime_start <= week_end_dt,
        models.Appointment.status != "ANNULÉ"
    ).all()

    avg_montant = db.query(func.avg(models.Acte.montant)).join(models.Patient).filter(
        models.Patient.employer_id == employer_id,
        models.Acte.date_debut >= datetime.now() - timedelta(days=30)
    ).scalar() or 500.0

    forecast = round(len(appts) * float(avg_montant), 2)
    return {
        "week_start": today.isoformat(),
        "week_end": week_end.isoformat(),
        "rdv_count": len(appts),
        "forecast_revenue": forecast,
        "avg_per_rdv": round(float(avg_montant), 2),
    }


@router.get("/alerts/today")
def get_alerts_today(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients"))
):
    """E3 — Alertes proactives du jour générées par le scheduler."""
    employer_id = current_user.get_employer_id()
    today_start = datetime.combine(datetime.now().date(), datetime.min.time())
    alerts = db.query(models.ProactiveAlert).options(
        joinedload(models.ProactiveAlert.patient)
    ).filter(
        models.ProactiveAlert.employer_id == employer_id,
        models.ProactiveAlert.created_at >= today_start,
        models.ProactiveAlert.is_read == False
    ).order_by(
        models.ProactiveAlert.priority,
        models.ProactiveAlert.created_at.desc()
    ).limit(20).all()

    return {
        "total": len(alerts),
        "alerts": [
            {
                "id": a.id,
                "patient_id": a.patient_id,
                "nom": a.patient.nom,
                "prenom": a.patient.prenom,
                "type": a.alert_type,
                "title": a.title,
                "message": a.message,
                "action": a.action,
                "priority": a.priority,
            }
            for a in alerts
        ],
    }


@router.patch("/alerts/{alert_id}/read")
def mark_alert_read(
    alert_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients"))
):
    """E3 — Marquer une alerte comme lue."""
    alert = db.query(models.ProactiveAlert).filter(models.ProactiveAlert.id == alert_id).first()
    if not alert or alert.employer_id != current_user.get_employer_id():
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_read = True
    db.commit()
    return {"status": "ok"}


@router.get("/patient/{patient_id}/nba")
async def get_patient_nba(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients"))
):
    """D1 — Next Best Action pour un patient (retourne le trigger prioritaire)."""
    assert_patient_access(patient_id, current_user, db)
    triggers = habits_engine.check_proactive_triggers(db, patient_id)
    if not triggers:
        return {"nba": None}
    top = triggers[0]
    return {
        "nba": {
            "type": top["type"],
            "title": top["title"],
            "message": top["message"],
            "action": top.get("action", ""),
        }
    }


@router.get("/taux-conversion")
def get_taux_conversion(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients"))
):
    """C4 — Taux de conversion devis → actes (% devis suivis d'un acte dans 90j)."""
    employer_id = current_user.get_employer_id()
    devis_list = db.query(models.DocumentArchive).join(models.Patient).filter(
        models.Patient.employer_id == employer_id,
        models.DocumentArchive.document_type == "DEVIS"
    ).all()
    if not devis_list:
        return {"devis_count": 0, "converted_count": 0, "taux": 0.0, "avg_days": None}

    converted = 0
    total_days = []
    for d in devis_list:
        first_acte = db.query(models.Acte).filter(
            models.Acte.patient_id == d.patient_id,
            models.Acte.date_debut > d.created_at,
            models.Acte.date_debut <= d.created_at + timedelta(days=90)
        ).order_by(models.Acte.date_debut).first()
        if first_acte:
            converted += 1
            total_days.append((first_acte.date_debut - d.created_at).days)

    avg_days = round(sum(total_days) / len(total_days), 1) if total_days else None
    return {
        "devis_count": len(devis_list),
        "converted_count": converted,
        "taux": round(converted / len(devis_list) * 100, 1),
        "avg_days": avg_days,
    }


@router.get("/projection-mensuelle")
def get_projection_mensuelle(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients"))
):
    """C5 — Projection mensuelle des revenus (3 mois historique + 6 mois forecast)."""
    employer_id = current_user.get_employer_id()
    now = datetime.now()

    historical = []
    for i in range(3, 0, -1):
        month_start = (now.replace(day=1) - timedelta(days=30 * i)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        rev = db.query(func.sum(models.Acte.montant)).join(models.Patient).filter(
            models.Patient.employer_id == employer_id,
            models.Acte.date_debut >= month_start,
            models.Acte.date_debut <= month_end
        ).scalar() or 0.0
        historical.append({"month": month_start.strftime("%Y-%m"), "revenue": round(float(rev), 2), "type": "actual"})

    avg_monthly = sum(h["revenue"] for h in historical) / 3 if historical else 0

    total_rdv_90d = db.query(func.count(models.Appointment.id)).join(models.Patient).filter(
        models.Patient.employer_id == employer_id,
        models.Appointment.datetime_start >= now - timedelta(days=90)
    ).scalar() or 1
    avg_rdv_per_month = max(total_rdv_90d / 3, 1)

    projections = []
    for i in range(1, 7):
        proj_month_start = (now.replace(day=1) + timedelta(days=32 * i)).replace(day=1)
        proj_month_end = (proj_month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        rdv_count = db.query(func.count(models.Appointment.id)).join(models.Patient).filter(
            models.Patient.employer_id == employer_id,
            models.Appointment.datetime_start >= proj_month_start,
            models.Appointment.datetime_start <= proj_month_end,
            models.Appointment.status != "ANNULÉ"
        ).scalar() or 0
        factor = min(rdv_count / avg_rdv_per_month, 1.5) if rdv_count else 1.0
        projections.append({
            "month": proj_month_start.strftime("%Y-%m"),
            "revenue": round(avg_monthly * factor, 2),
            "type": "forecast",
        })

    return {"historical": historical, "projections": projections, "avg_monthly": round(avg_monthly, 2)}


@router.get("/patient/{patient_id}/upcoming-prescription")
async def get_upcoming_prescription(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients"))
):
    """D4 — Ordonnance anticipée : si RDV dans 14j, suggère le protocole à préparer."""
    assert_patient_access(patient_id, current_user, db)
    now = datetime.now()
    next_appt = db.query(models.Appointment).filter(
        models.Appointment.patient_id == patient_id,
        models.Appointment.datetime_start > now,
        models.Appointment.datetime_start <= now + timedelta(days=14),
        models.Appointment.status != "ANNULÉ"
    ).order_by(models.Appointment.datetime_start).first()

    if not next_appt:
        return {"upcoming": None}

    from backend.routers.prescriptions import get_smart_suggestion
    smart = await get_smart_suggestion(patient_id, db, current_user)

    return {
        "upcoming": {
            "appointment_date": next_appt.datetime_start.strftime("%d/%m/%Y à %Hh%M"),
            "motif": next_appt.motif or "",
            "days_until": (next_appt.datetime_start - now).days,
            "prescription_suggestion": smart,
        }
    }
