from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Dict, Any

from backend import models, database
from backend.routers.auth import get_current_user

router = APIRouter(tags=["Statistiques"])

@router.get("/financial")
def get_financial_stats(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """
    Récupère le chiffre d'affaires du mois et la trésorerie latente (Latent Cash).
    """
    emp_id = current_user.get_employer_id()
    today = datetime.now()
    first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Revenus du mois (Actes)
    revenus_mois = db.query(func.sum(models.Acte.montant)).join(models.Patient).filter(
        models.Patient.employer_id == emp_id,
        models.Acte.date_debut >= first_day_of_month,
        models.Acte.statut_paiement.in_([models.PaiementStatut.PAYE, models.PaiementStatut.PARTIEL])
    ).scalar() or 0.0

    # Trésorerie Latente : Total des Devis PENDING (TreatmentPlanStep.status == PENDING)
    # Les TreatmentPlanStep n'ont pas de prix, mais si les actes ont DEVIS, on utilise ça ?
    # Le backend "intelligence" utilise Acte.statut_paiement == EN_ATTENTE
    latent_cash_query = db.query(func.sum(models.Acte.montant)).join(models.Patient).filter(
        models.Patient.employer_id == emp_id,
        models.Acte.statut_paiement == models.PaiementStatut.EN_ATTENTE,
        models.Acte.is_accounted == False
    )
    latent_cash = latent_cash_query.scalar() or 0.0

    # Liste des 5 devis en attente les plus élevés (pour le bouton "Qui relancer ?")
    top_latent = db.query(
        models.Patient.nom, 
        models.Patient.prenom, 
        models.Patient.telephone,
        models.Acte.montant, 
        models.Acte.libelle
    ).join(models.Patient).filter(
        models.Patient.employer_id == emp_id,
        models.Acte.statut_paiement == models.PaiementStatut.EN_ATTENTE,
        models.Acte.is_accounted == False
    ).order_by(models.Acte.montant.desc()).limit(5).all()

    top_latent_list = [{"nom": p.nom, "prenom": p.prenom, "telephone": p.telephone, "montant": p.montant, "soin": p.libelle} for p in top_latent]

    return {
        "revenu_mois": round(revenus_mois, 2),
        "latent_cash": round(latent_cash, 2),
        "top_relances": top_latent_list
    }

@router.get("/operational")
def get_operational_stats(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    """
    Récupère les statistiques opérationnelles : No-shows, occupation, temps d'attente (simulé ou via les tickets).
    """
    emp_id = current_user.get_employer_id()
    
    # Statistiques sur la semaine glissante
    week_ago = datetime.now() - timedelta(days=7)
    
    total_appts = db.query(models.Appointment).filter(
        models.Appointment.employer_id == emp_id,
        models.Appointment.datetime_start >= week_ago
    ).count()

    annules = db.query(models.Appointment).filter(
        models.Appointment.employer_id == emp_id,
        models.Appointment.datetime_start >= week_ago,
        models.Appointment.status == models.AppointmentStatus.ANNULE
    ).count()

    no_show_rate = round((annules / total_appts * 100) if total_appts > 0 else 0, 1)

    # Temps d'attente moyen (En attendant d'avoir des timestamps exacts, on simule une valeur basée sur le nombre de tickets ou de rdv EN_S_ATTENTE)
    en_salle = db.query(models.Appointment).filter(
        models.Appointment.employer_id == emp_id,
        models.Appointment.status == models.AppointmentStatus.EN_SALLE_ATTENTE
    ).count()

    # Si on a 2 patients en salle, le temps d'attente moyen estimé est de ~15min
    estimated_wait_time = max(5, en_salle * 10)

    # Flux du jour (Tickets & RDV)
    today_start = datetime.now().replace(hour=0, minute=0, second=0)
    today_appts = db.query(models.Appointment).filter(
        models.Appointment.employer_id == emp_id,
        models.Appointment.datetime_start >= today_start
    ).count()

    return {
        "no_show_rate": no_show_rate,
        "total_appts_week": total_appts,
        "estimated_wait_time_minutes": estimated_wait_time,
        "patients_en_salle": en_salle,
        "flux_today": today_appts
    }
