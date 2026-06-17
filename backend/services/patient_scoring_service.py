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

    def _grade_from_score(self, final_score: int) -> str:
        if final_score >= 90:
            return "PLATINUM"
        if final_score >= 75:
            return "GOLD"
        if final_score >= 50:
            return "SILVER"
        return "BRONZE"

    def calculate_scores_bulk(self, db: Session, employer_id: int) -> dict:
        """
        Calcule les scores de TOUS les patients d'un cabinet en 3 requêtes agrégées
        (au lieu de 3 requêtes par patient). Évite le flood de N appels /score.
        Retourne {patient_id: {score, grade, details}}.
        """
        patient_ids = [
            pid for (pid,) in db.query(models.Patient.id)
            .filter(models.Patient.employer_id == employer_id).all()
        ]
        if not patient_ids:
            return {}

        # 1. RDV agrégés par patient + statut
        appt_rows = (
            db.query(models.Appointment.patient_id, models.Appointment.status, func.count().label("c"))
            .filter(models.Appointment.patient_id.in_(patient_ids))
            .group_by(models.Appointment.patient_id, models.Appointment.status)
            .all()
        )
        honores: dict = {}
        annules: dict = {}
        for pid, status, c in appt_rows:
            name = status.name if hasattr(status, "name") else str(status)
            if name == "TERMINE":
                honores[pid] = honores.get(pid, 0) + c
            elif name == "ANNULE":
                annules[pid] = annules.get(pid, 0) + c

        # 2. Total facturé / encaissé par patient
        acte_rows = (
            db.query(models.Acte.patient_id, func.coalesce(func.sum(models.Acte.montant), 0))
            .filter(models.Acte.patient_id.in_(patient_ids))
            .group_by(models.Acte.patient_id).all()
        )
        factures = {pid: float(total or 0) for pid, total in acte_rows}
        pay_rows = (
            db.query(models.Payment.patient_id, func.coalesce(func.sum(models.Payment.amount), 0))
            .filter(models.Payment.patient_id.in_(patient_ids))
            .group_by(models.Payment.patient_id).all()
        )
        encaisses = {pid: float(total or 0) for pid, total in pay_rows}

        result = {}
        for pid in patient_ids:
            h = honores.get(pid, 0)
            a = annules.get(pid, 0)
            appt_score = max(0.0, min(100.0, 100.0 + 5 * h - 10 * a))

            total_facture = factures.get(pid, 0.0)
            total_encaisse = encaisses.get(pid, 0.0)
            solv_score = 100.0
            if total_facture > 0:
                solv_score = max(0.0, min(100.0, (total_encaisse / total_facture) * 100))

            final_score = math.floor((appt_score * 0.6) + (solv_score * 0.4))
            result[pid] = {
                "score": final_score,
                "grade": self._grade_from_score(final_score),
                "details": {
                    "assiduite_score": math.floor(appt_score),
                    "solvabilite_score": math.floor(solv_score),
                    "rdv_honores": h,
                    "rdv_annules": a,
                    "total_facture": total_facture,
                    "total_encaisse": total_encaisse,
                },
            }
        return result


patient_scoring_service = PatientScoringService()
