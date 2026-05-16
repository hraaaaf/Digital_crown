from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend import models
from typing import Dict, Any

class StateExtractor:
    """
    Service surgical d'extraction de données pour le payload mobile.
    Focalisé sur l'essentiel : Agenda, KPIs Financiers et Alertes.
    """
    
    def get_full_snapshot(self, db: Session, employer_id: int) -> Dict[str, Any]:
        """Génère le snapshot complet pour un cabinet donné."""
        today = date.today()
        
        # 1. Agenda du jour
        appointments = db.query(models.Appointment).filter(
            models.Appointment.employer_id == employer_id,
            func.date(models.Appointment.datetime_start) == today
        ).order_by(models.Appointment.datetime_start).all()
        
        # 2. KPIs Financiers (CA du mois en cours)
        current_month = today.month
        current_year = today.year
        
        # Recettes mensuelles réelles (paiements encaissés)
        month_revenue = db.query(func.sum(models.Payment.amount)).join(models.Patient).filter(
            models.Patient.employer_id == employer_id,
            models.Payment.payment_date >= datetime(current_year, current_month, 1)
        ).scalar() or 0.0

        # 3. Construction du Payload
        return {
            "metadata": {
                "sync_at": datetime.now().isoformat(),
                "clinic_id": employer_id,
                "version": "1.5-zka"
            },
            "agenda": [
                {
                    "id": apt.id,
                    "time": apt.datetime_start.strftime("%H:%M"),
                    "patient": f"{apt.patient.nom} {apt.patient.prenom}" if apt.patient else apt.patient_name,
                    "patient_id": apt.patient_id,
                    "motif": apt.motif,
                    "status": apt.status.value,
                    "grade": apt.patient.manual_grade if apt.patient else None
                } for apt in appointments
            ],
            "finance": {
                "month_revenue": float(month_revenue),
                "currency": "MAD"
            },
            "stats": {
                "today_count": len(appointments),
                "remaining_count": len([a for a in appointments if a.status.value == "PRÉVU"])
            }
        }

state_extractor = StateExtractor()
