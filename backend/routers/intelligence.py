from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session, joinedload, contains_eager
from sqlalchemy import func, or_
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import logging

from backend import database, models
from backend.routers.auth import get_current_user, require_permission, require_elite_license
from backend.services.elite_manager import elite_manager
from backend.services.habits_engine import habits_engine
from backend.utils.access_control import assert_patient_access

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Elite Intelligence"],
    dependencies=[Depends(require_elite_license)]
)

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

        p_acts = db.query(func.sum(models.Acte.montant)).filter(models.Acte.patient_id == appt.patient_id).scalar() or 0.0
        p_pays = db.query(func.sum(models.Payment.amount)).filter(models.Payment.patient_id == appt.patient_id).scalar() or 0.0
        solde = max(float(p_acts) - float(p_pays), 0.0)

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


@router.get("/briefing-today")
def get_briefing_today(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients"))
):
    """Briefing financier d'aujourd'hui : patients du jour avec leurs soldes impayés."""
    employer_id = current_user.get_employer_id()
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())

    appts = db.query(models.Appointment).filter(
        models.Appointment.employer_id == employer_id,
        models.Appointment.datetime_start >= today_start,
        models.Appointment.datetime_start <= today_end,
        models.Appointment.status != "ANNULÉ"
    ).order_by(models.Appointment.datetime_start).all()

    result = []
    total_outstanding = 0.0
    seen_patient_ids = set()

    for appt in appts:
        if appt.patient_id is None:
            continue
        if appt.patient_id in seen_patient_ids:
            continue
        seen_patient_ids.add(appt.patient_id)

        patient = db.query(models.Patient).filter(models.Patient.id == appt.patient_id).first()
        if not patient:
            continue

        p_acts = db.query(func.sum(models.Acte.montant)).filter(models.Acte.patient_id == appt.patient_id).scalar() or 0.0
        p_pays = db.query(func.sum(models.Payment.amount)).filter(models.Payment.patient_id == appt.patient_id).scalar() or 0.0
        solde = max(float(p_acts) - float(p_pays), 0.0)

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
        "date": today.strftime("%d/%m/%Y"),
        "total_patients": len(result),
        "total_outstanding": round(total_outstanding, 2),
        "patients": sorted(result, key=lambda x: x["solde_attente"], reverse=True),
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
    """E3 — Alertes proactives non lues (patient ou cabinet), tant qu'elles ne sont
    pas expirées. Ne filtre plus sur "créées aujourd'hui" : une alerte non lue créée
    hier ne doit pas disparaître silencieusement avant même d'avoir été vue (bug
    "alertes fantômes", audit fonctionnel 2026-07-12). Exclut aussi les alertes
    pointant vers un patient soft-supprimé et celles actuellement reportées (snooze)."""
    employer_id = current_user.get_employer_id()
    now = datetime.now()
    alerts = db.query(models.ProactiveAlert).outerjoin(
        models.Patient, models.ProactiveAlert.patient_id == models.Patient.id
    ).options(
        contains_eager(models.ProactiveAlert.patient)
    ).filter(
        models.ProactiveAlert.employer_id == employer_id,
        models.ProactiveAlert.is_read == False,
        or_(models.ProactiveAlert.expires_at.is_(None), models.ProactiveAlert.expires_at > now),
        or_(models.ProactiveAlert.patient_id.is_(None), models.Patient.deleted_at.is_(None)),
        or_(models.ProactiveAlert.snoozed_until.is_(None), models.ProactiveAlert.snoozed_until <= now),
    ).order_by(
        models.ProactiveAlert.priority,
        models.ProactiveAlert.created_at.desc()
    ).limit(20).all()

    return {
        "total": len(alerts),
        "alerts": [
            {
                "id": a.id,
                # Alertes cabinet (ex. stock) : patient_id/nom/prenom None par design.
                "patient_id": a.patient_id,
                "nom": a.patient.nom if a.patient else None,
                "prenom": a.patient.prenom if a.patient else None,
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


@router.patch("/alerts/{alert_id}/snooze")
def snooze_alert(
    alert_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients"))
):
    """Reporte une alerte de 24h sans la marquer comme lue définitivement."""
    alert = db.query(models.ProactiveAlert).filter(models.ProactiveAlert.id == alert_id).first()
    if not alert or alert.employer_id != current_user.get_employer_id():
        raise HTTPException(status_code=404, detail="Alert not found")
    now = datetime.now()
    alert.snoozed_until = now + timedelta(hours=24)
    # Ne jamais laisser expires_at purger une alerte encore snoozée (nettoyage
    # quotidien dans daily_scheduler.py).
    if not alert.expires_at or alert.expires_at < alert.snoozed_until + timedelta(days=1):
        alert.expires_at = alert.snoozed_until + timedelta(days=1)
    db.commit()
    return {"status": "ok", "snoozed_until": alert.snoozed_until.isoformat()}


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

    # Précharge en 2 requêtes (au lieu de 2 par devis) tous les Actes/notes
    # d'honoraires pertinents, puis matching en mémoire — évite le N+1.
    patient_ids = {d.patient_id for d in devis_list}
    window_start = min(d.created_at for d in devis_list)
    window_end = max(d.created_at for d in devis_list) + timedelta(days=90)

    all_actes = db.query(models.Acte).filter(
        models.Acte.patient_id.in_(patient_ids),
        models.Acte.date_debut > window_start,
        models.Acte.date_debut <= window_end,
    ).order_by(models.Acte.date_debut).all()
    all_notes = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.patient_id.in_(patient_ids),
        models.DocumentArchive.document_type == "NOTE_HONORAIRES",
        models.DocumentArchive.created_at > window_start,
        models.DocumentArchive.created_at <= window_end,
    ).order_by(models.DocumentArchive.created_at).all()

    actes_by_patient = defaultdict(list)
    for a in all_actes:
        actes_by_patient[a.patient_id].append(a)
    notes_by_patient = defaultdict(list)
    for n in all_notes:
        notes_by_patient[n.patient_id].append(n)

    converted = 0
    total_days = []
    for d in devis_list:
        d_window_end = d.created_at + timedelta(days=90)
        first_acte = next(
            (a for a in actes_by_patient[d.patient_id]
             if a.date_debut > d.created_at and a.date_debut <= d_window_end), None)
        first_note = next(
            (n for n in notes_by_patient[d.patient_id]
             if n.created_at > d.created_at and n.created_at <= d_window_end), None)

        if first_acte or first_note:
            converted += 1
            if first_acte and first_note:
                days = min((first_acte.date_debut - d.created_at).days, (first_note.created_at - d.created_at).days)
            elif first_acte:
                days = (first_acte.date_debut - d.created_at).days
            else:
                days = (first_note.created_at - d.created_at).days
            total_days.append(days)

    avg_days = round(sum(total_days) / len(total_days), 1) if total_days else None
    return {
        "devis_count": len(devis_list),
        "converted_count": converted,
        "taux": round(converted / len(devis_list) * 100, 1),
        "avg_days": avg_days,
    }

@router.get("/latent-cash")
def get_latent_cash(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients"))
):
    """Ghost Re-Call: Trouve le cash latent (Devis non convertis depuis > 15j et échéances en retard)."""
    employer_id = current_user.get_employer_id()
    
    # 1. Devis Dormants (> 15 jours sans actes)
    cutoff_date = datetime.now() - timedelta(days=15)
    devis_list = db.query(models.DocumentArchive).join(models.Patient).filter(
        models.Patient.employer_id == employer_id,
        models.DocumentArchive.document_type == "DEVIS",
        models.DocumentArchive.created_at <= cutoff_date
    ).all()
    
    dormant_devis = []
    total_dormant_amount = 0.0

    # Précharge en une requête les dates d'Actes de tous les patients concernés
    # (au lieu d'un COUNT par devis) — évite le N+1.
    patient_ids = {d.patient_id for d in devis_list}
    all_actes_dates = db.query(models.Acte.patient_id, models.Acte.date_debut).filter(
        models.Acte.patient_id.in_(patient_ids)
    ).all() if patient_ids else []
    actes_dates_by_patient = defaultdict(list)
    for pid, dt in all_actes_dates:
        actes_dates_by_patient[pid].append(dt)

    for d in devis_list:
        # Check si aucun acte n'a été fait après le devis
        acts_after = sum(1 for dt in actes_dates_by_patient[d.patient_id] if dt >= d.created_at)
        if acts_after == 0:
            # Bug historique corrigé : `d.document_data` n'existait pas sur
            # DocumentArchive (AttributeError toujours avalée par un except:pass
            # — dormant_devis restait toujours vide). Le vrai champ, déjà utilisé
            # ailleurs pour la même donnée, est `clinical_data` (voir
            # backend/routers/accounting.py, alimenté par documents.py).
            data = d.clinical_data or {}
            total = sum(item.get("montant", 0) for item in data.get("items", []))
            if total > 0:
                dormant_devis.append({
                    "patient_id": d.patient_id,
                    "patient_name": f"{d.patient.prenom} {d.patient.nom}",
                    "telephone": d.patient.telephone,
                    "date_devis": d.created_at.strftime("%d/%m/%Y"),
                    "montant": total,
                    "type": "Devis En Attente"
                })
                total_dormant_amount += total

    return {
        "total_opportunites": len(dormant_devis),
        "valeur_totale_latente": total_dormant_amount,
        "opportunites": sorted(dormant_devis, key=lambda x: x["montant"], reverse=True)
    }

@router.get("/projection-mensuelle")
def get_projection_mensuelle(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients"))
):
    """C5 — Projection mensuelle des revenus (3 mois historique + 6 mois forecast avec WMA)."""
    employer_id = current_user.get_employer_id()
    now = datetime.now()
    import calendar

    historical = []
    
    def get_month_boundaries(year, month):
        start = datetime(year, month, 1)
        _, last_day = calendar.monthrange(year, month)
        end = datetime(year, month, last_day, 23, 59, 59)
        return start, end

    # 1. Historique (M-3 à M-1)
    for i in range(3, 0, -1):
        target_month = now.month - i
        target_year = now.year
        if target_month <= 0:
            target_month += 12
            target_year -= 1
            
        month_start, month_end = get_month_boundaries(target_year, target_month)
        
        # Revenus purs (Actes, évite le double comptage avec les devis/notes)
        rev_actes = db.query(func.sum(models.Acte.montant)).join(models.Patient).filter(
            models.Patient.employer_id == employer_id,
            models.Acte.date_debut >= month_start,
            models.Acte.date_debut <= month_end,
            models.Acte.montant > 0
        ).scalar() or 0.0
        
        historical.append({
            "month": month_start.strftime("%Y-%m"), 
            "revenue": round(float(rev_actes), 2), 
            "type": "actual"
        })

    # 2. Modèle de Prévision (Moyenne Mobile Pondérée WMA)
    if len(historical) == 3:
        # Poids FP&A standard : M-1=50%, M-2=30%, M-3=20%
        base_forecast = (historical[2]["revenue"] * 0.5) + (historical[1]["revenue"] * 0.3) + (historical[0]["revenue"] * 0.2)
    else:
        base_forecast = sum(h["revenue"] for h in historical) / len(historical) if historical else 0.0

    # Lissage de croissance (CAGR) capé à +/- 5% pour éviter les aberrations
    growth_rate = 1.0
    if len(historical) >= 3 and historical[0]["revenue"] > 0:
        raw_growth = historical[2]["revenue"] / historical[0]["revenue"]
        growth_rate = min(max(raw_growth ** (1/2), 0.95), 1.05)

    projections = []
    current_forecast = base_forecast

    # 3. Projections (M à M+5)
    for i in range(0, 6):
        target_month = now.month + i
        target_year = now.year
        if target_month > 12:
            target_month -= 12
            target_year += 1
            
        proj_month_start, _ = get_month_boundaries(target_year, target_month)
        
        # Application de la tendance sur la base WMA
        if current_forecast > 0:
            current_forecast = current_forecast * growth_rate
            
        projections.append({
            "month": proj_month_start.strftime("%Y-%m"),
            "revenue": round(current_forecast, 2),
            "type": "forecast",
        })

    avg_monthly = sum(h["revenue"] for h in historical) / len(historical) if historical else 0.0

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


@router.get("/distribution-assurances")
def get_distribution_assurances(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients"))
):
    """C6 — Répartition des honoraires par assurance (chiffre d'affaires total)."""
    employer_id = current_user.get_employer_id()
    
    # Depuis les actes
    results_actes = db.query(
        models.Patient.assurance,
        func.sum(models.Acte.montant).label("total_revenue"),
        func.count(models.Acte.id).label("acts_count")
    ).join(models.Acte, models.Acte.patient_id == models.Patient.id).filter(
        models.Patient.employer_id == employer_id
    ).group_by(models.Patient.assurance).all()
    
    assurance_map = {}
    for r in results_actes:
        assur = r[0] if r[0] else "AUCUNE"
        assurance_map[assur] = {"revenue": float(r[1]) if r[1] else 0.0, "count": r[2] or 0}
        
    # Depuis les notes d'honoraires
    docs = db.query(models.DocumentArchive).join(models.Patient).filter(
        models.Patient.employer_id == employer_id,
        models.DocumentArchive.document_type == "NOTE_HONORAIRES"
    ).all()
    
    from backend.routers.documents import extract_amount_from_clinical_data
    for d in docs:
        assur = d.patient.assurance if d.patient.assurance else "AUCUNE"
        amount = extract_amount_from_clinical_data(d.clinical_data)
        if assur not in assurance_map:
            assurance_map[assur] = {"revenue": 0.0, "count": 0}
        assurance_map[assur]["revenue"] += amount
        assurance_map[assur]["count"] += 1

    return [
        {
            "assurance": k,
            "revenue": round(v["revenue"], 2),
            "count": v["count"]
        }
        for k, v in assurance_map.items()
    ]
