from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import List, Dict, Any
from datetime import datetime, timedelta
import calendar

from backend import models, database
from backend.routers.auth import get_current_user

router = APIRouter(tags=["Analytics & Finance"])

@router.get("/financial")
def get_financial_analytics(
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """
    Récupère les données analytiques financières du cabinet pour le tableau de bord (Phase 1).
    Filtre automatiquement par l'employer_id du cabinet.
    """
    employer_id = current_user.get_employer_id()
    now = datetime.now()
    
    # Dates limites pour ce mois et le mois précédent
    first_day_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    last_month = now.replace(day=1) - timedelta(days=1)
    first_day_last_month = last_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # REVENU CE MOIS
    revenue_this_month = db.query(func.sum(models.Payment.amount))\
        .join(models.Patient)\
        .filter(models.Patient.employer_id == employer_id)\
        .filter(models.Payment.payment_date >= first_day_this_month)\
        .scalar() or 0.0

    # REVENU MOIS DERNIER
    revenue_last_month = db.query(func.sum(models.Payment.amount))\
        .join(models.Patient)\
        .filter(models.Patient.employer_id == employer_id)\
        .filter(models.Payment.payment_date >= first_day_last_month)\
        .filter(models.Payment.payment_date < first_day_this_month)\
        .scalar() or 0.0

    # REVENU MENSUEL (6 derniers mois)
    monthly_revenue = []
    for i in range(5, -1, -1):
        target_month = now.replace(day=1) - timedelta(days=30*i)
        # Gestion précise des fins de mois
        first_day = target_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        
        val = db.query(func.sum(models.Payment.amount))\
            .join(models.Patient)\
            .filter(models.Patient.employer_id == employer_id)\
            .filter(models.Payment.payment_date >= first_day)\
            .filter(models.Payment.payment_date <= last_day)\
            .scalar() or 0.0
            
        month_name = calendar.month_abbr[first_day.month]
        monthly_revenue.append({
            "name": f"{month_name} {first_day.year}",
            "revenue": val
        })

    # TAUX DE RECOUVREMENT (Total Payé vs Total Facturé Global)
    total_paid = db.query(func.sum(models.Payment.amount))\
        .join(models.Patient)\
        .filter(models.Patient.employer_id == employer_id)\
        .scalar() or 0.0
        
    total_billed = db.query(func.sum(models.Acte.montant))\
        .join(models.Patient)\
        .filter(models.Patient.employer_id == employer_id)\
        .scalar() or 0.0
        
    recovery_rate = (total_paid / total_billed * 100) if total_billed > 0 else 100.0

    # TOP ACTES LES PLUS RENTABLES (Global)
    top_acts_query = db.query(
        models.Acte.libelle, 
        func.sum(models.Acte.montant).label('total_revenue')
    )\
    .join(models.Patient)\
    .filter(models.Patient.employer_id == employer_id)\
    .group_by(models.Acte.libelle)\
    .order_by(func.sum(models.Acte.montant).desc())\
    .limit(5)\
    .all()
    
    top_acts = [{"name": act.libelle, "value": act.total_revenue} for act in top_acts_query]

    # TOP ACTES (Fréquence)
    top_acts_freq_query = db.query(
        models.Acte.libelle, 
        func.count(models.Acte.id).label('count')
    )\
    .join(models.Patient)\
    .filter(models.Patient.employer_id == employer_id)\
    .group_by(models.Acte.libelle)\
    .order_by(func.count(models.Acte.id).desc())\
    .limit(5)\
    .all()

    top_acts_freq = [{"name": act.libelle, "value": act.count} for act in top_acts_freq_query]

    return {
        "revenue_this_month": revenue_this_month,
        "revenue_last_month": revenue_last_month,
        "monthly_revenue": monthly_revenue,
        "recovery_rate": round(recovery_rate, 2),
        "total_billed": total_billed,
        "total_paid": total_paid,
        "top_acts_revenue": top_acts,
        "top_acts_frequency": top_acts_freq
    }
