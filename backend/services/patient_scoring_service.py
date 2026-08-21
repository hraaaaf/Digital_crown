from sqlalchemy.orm import Session
from sqlalchemy import func
from backend import models


class PatientScoringService:
    """Expose des repères patient factuels sans produire de note comportementale."""

    @staticmethod
    def _details(
        *,
        rdv_honores: int,
        rdv_annules: int,
        total_facture: float,
        total_encaisse: float,
        has_billing_data: bool,
    ) -> dict:
        remaining_due = (
            round(max(total_facture - total_encaisse, 0.0), 2)
            if has_billing_data
            else None
        )
        return {
            # Anciens champs conservés explicitement nuls pour compatibilité de contrat :
            # ils ne doivent plus être interprétés comme des scores.
            "assiduite_score": None,
            "solvabilite_score": None,
            "rdv_honores": int(rdv_honores),
            "rdv_annules": int(rdv_annules),
            "rdv_total_observe": int(rdv_honores + rdv_annules),
            "total_facture": round(float(total_facture), 2),
            "total_encaisse": round(float(total_encaisse), 2),
            "remaining_due": remaining_due,
            "has_billing_data": bool(has_billing_data),
        }

    def calculate_score(self, db: Session, patient_id: int) -> dict:
        """Retourne les faits historiques ; aucun score/grade automatique n'est calculé."""
        appointments = db.query(models.Appointment).filter(
            models.Appointment.patient_id == patient_id
        ).all()
        rdv_honores = sum(
            1 for appt in appointments if appt.status == models.AppointmentStatus.TERMINE
        )
        rdv_annules = sum(
            1 for appt in appointments if appt.status == models.AppointmentStatus.ANNULE
        )

        actes = db.query(models.Acte).filter(models.Acte.patient_id == patient_id).all()
        payments = db.query(models.Payment).filter(models.Payment.patient_id == patient_id).all()
        total_facture = sum(float(acte.montant or 0.0) for acte in actes)
        total_encaisse = sum(float(payment.amount or 0.0) for payment in payments)
        has_billing_data = len(actes) > 0

        return {
            "score": None,
            "grade": None,
            "details": self._details(
                rdv_honores=rdv_honores,
                rdv_annules=rdv_annules,
                total_facture=total_facture,
                total_encaisse=total_encaisse,
                has_billing_data=has_billing_data,
            ),
        }

    def calculate_scores_bulk(self, db: Session, employer_id: int) -> dict:
        """Agrège les mêmes faits en batch, sans N appels ni notation automatique."""
        patient_ids = [
            pid
            for (pid,) in db.query(models.Patient.id)
            .filter(models.Patient.employer_id == employer_id)
            .all()
        ]
        if not patient_ids:
            return {}

        appt_rows = (
            db.query(
                models.Appointment.patient_id,
                models.Appointment.status,
                func.count().label("c"),
            )
            .filter(models.Appointment.patient_id.in_(patient_ids))
            .group_by(models.Appointment.patient_id, models.Appointment.status)
            .all()
        )
        honores: dict[int, int] = {}
        annules: dict[int, int] = {}
        for pid, status, count in appt_rows:
            name = status.name if hasattr(status, "name") else str(status)
            if name == "TERMINE":
                honores[pid] = honores.get(pid, 0) + int(count)
            elif name == "ANNULE":
                annules[pid] = annules.get(pid, 0) + int(count)

        acte_rows = (
            db.query(
                models.Acte.patient_id,
                func.count(models.Acte.id),
                func.coalesce(func.sum(models.Acte.montant), 0),
            )
            .filter(models.Acte.patient_id.in_(patient_ids))
            .group_by(models.Acte.patient_id)
            .all()
        )
        billing = {
            pid: {"count": int(count), "total": float(total or 0.0)}
            for pid, count, total in acte_rows
        }
        pay_rows = (
            db.query(
                models.Payment.patient_id,
                func.coalesce(func.sum(models.Payment.amount), 0),
            )
            .filter(models.Payment.patient_id.in_(patient_ids))
            .group_by(models.Payment.patient_id)
            .all()
        )
        encaisses = {pid: float(total or 0.0) for pid, total in pay_rows}

        result: dict[int, dict] = {}
        for pid in patient_ids:
            billing_row = billing.get(pid, {"count": 0, "total": 0.0})
            result[pid] = {
                "score": None,
                "grade": None,
                "details": self._details(
                    rdv_honores=honores.get(pid, 0),
                    rdv_annules=annules.get(pid, 0),
                    total_facture=billing_row["total"],
                    total_encaisse=encaisses.get(pid, 0.0),
                    has_billing_data=billing_row["count"] > 0,
                ),
            }
        return result


patient_scoring_service = PatientScoringService()
