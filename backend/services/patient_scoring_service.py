from sqlalchemy.orm import Session
from sqlalchemy import func
from backend import models
import math

class PatientScoringService:
    
    def calculate_score(self, db: Session, patient_id: int) -> dict:
        """
        Calcule le score dynamique d'un patient basé sur :
        1. L'assiduité aux rendez-vous (60%)
        2. La régularité des paiements (40%)
        """
        # --- 1. INDICE D'ASSIDUITÉ (60%) ---
        appointments = db.query(models.Appointment).filter(models.Appointment.patient_id == patient_id).all()
        
        appt_score = 100.0
        honores = 0
        no_shows = 0
        annules = 0
        
        for appt in appointments:
            if appt.status == models.AppointmentStatus.TERMINE:
                honores += 1
                appt_score += 5  # Bonus fidélité
            elif appt.status == models.AppointmentStatus.ANNULE:
                annules += 1
                appt_score -= 10 # Malus annulation
            # Si on avait un statut NO_SHOW, on appliquerait -30. On suppose ANNULE regroupe pour l'instant.
        
        # Clamp entre 0 et 100
        appt_score = max(0.0, min(100.0, appt_score))
        
        # --- 2. INDICE DE SOLVABILITÉ (40%) ---
        # Total facturé
        actes = db.query(models.Acte).filter(models.Acte.patient_id == patient_id).all()
        total_facture = sum(acte.montant for acte in actes)
        
        # Total encaissé
        payments = db.query(models.Payment).filter(models.Payment.patient_id == patient_id).all()
        total_encaisse = sum(payment.amount for payment in payments)
        
        solv_score = 100.0
        if total_facture > 0:
            ratio = (total_encaisse / total_facture) * 100
            solv_score = max(0.0, min(100.0, ratio))
            
        # --- 3. CALCUL FINAL ET GRADE ---
        final_score = math.floor((appt_score * 0.6) + (solv_score * 0.4))
        
        if final_score >= 90:
            grade = "PLATINUM"
        elif final_score >= 75:
            grade = "GOLD"
        elif final_score >= 50:
            grade = "SILVER"
        else:
            grade = "BRONZE"
            
        return {
            "score": final_score,
            "grade": grade,
            "details": {
                "assiduite_score": math.floor(appt_score),
                "solvabilite_score": math.floor(solv_score),
                "rdv_honores": honores,
                "rdv_annules": annules,
                "total_facture": total_facture,
                "total_encaisse": total_encaisse
            }
        }

patient_scoring_service = PatientScoringService()
