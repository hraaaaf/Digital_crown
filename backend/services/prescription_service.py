from typing import Any, Dict, List, Optional

from sqlalchemy import case, desc, func
from sqlalchemy.orm import Session

from backend import models
from backend.services.prescription_context_guard import (
    build_prescription_context,
    calculate_age,
    non_evaluable_plan,
)
from backend.services.prescription_service_legacy import PrescriptionService as LegacyPrescriptionService


class PrescriptionService(LegacyPrescriptionService):
    """Legacy-compatible service with explicit safety and persistence gates."""

    def resolve_smart_prescription(
        self,
        db: Session,
        patient_id: int,
        acts: List[str],
        doctor_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
        if not patient:
            raise ValueError("Patient introuvable")

        context = build_prescription_context(patient)
        main_act = self._safe_act_context(acts)

        if not context.evaluable:
            return non_evaluable_plan(context, main_act)

        # The legacy child-specific path still owns an internal synthetic
        # default. Do not enter it until that implementation is replaced.
        if context.age is not None and context.age < 15:
            plan = non_evaluable_plan(context, main_act)
            plan["evaluation"] = {
                "status": "manual_review_required",
                "missing_fields": [],
            }
            return plan

        result = super().resolve_smart_prescription(db, patient_id, acts, doctor_id)
        result["patient_context"] = context.as_dict()
        result["evaluation"] = context.evaluation_dict()
        return result

    def _safe_act_context(self, acts: List[str]) -> str:
        if not acts:
            return "DEFAULT"
        try:
            from backend.services.clinical_rules_engine import clinical_rules

            return clinical_rules._normalize_act_name(acts[0])
        except Exception:
            return "DEFAULT"

    def _calculate_age(self, birth_date) -> Optional[int]:
        return calculate_age(birth_date)

    # ------------------------------------------------------------------
    # R2 — deterministic local-first prescription persistence
    # ------------------------------------------------------------------
    def learn_habit(
        self,
        db: Session,
        doctor_id: int,
        act_code: str,
        drugs: List[Dict[str, Any]],
    ) -> None:
        """Persist a personal prescription preset or fail visibly.

        The legacy implementation swallowed database failures, allowing the
        HTTP layer to report success after a rollback. R2 deliberately lets
        the original database exception propagate after rollback.
        """
        cleaned_drugs = [
            {
                "name": d.get("name", d.get("nom", "")),
                "dosage": d.get("dosage", ""),
                "forme": d.get("forme", ""),
                "posologie": d.get("posologie", ""),
            }
            for d in drugs
        ]

        try:
            existing = (
                db.query(models.DoctorPrescriptionPreference)
                .filter(
                    models.DoctorPrescriptionPreference.doctor_id == doctor_id,
                    models.DoctorPrescriptionPreference.act_code == act_code,
                )
                .first()
            )
            if existing:
                existing.drugs_json = cleaned_drugs
            else:
                db.add(
                    models.DoctorPrescriptionPreference(
                        doctor_id=doctor_id,
                        act_code=act_code,
                        drugs_json=cleaned_drugs,
                    )
                )
            db.commit()
        except Exception:
            db.rollback()
            raise

    def delete_doctor_preset(self, db: Session, doctor_id: int, act_code: str) -> int:
        """Delete the same model used by save/load and return affected rows."""
        try:
            deleted = (
                db.query(models.DoctorPrescriptionPreference)
                .filter(
                    models.DoctorPrescriptionPreference.doctor_id == doctor_id,
                    models.DoctorPrescriptionPreference.act_code == act_code,
                )
                .delete(synchronize_session=False)
            )
            db.commit()
            return int(deleted)
        except Exception:
            db.rollback()
            raise

    def record_medication_usage(
        self,
        db: Session,
        doctor_id: int,
        med_name: str,
        dosage: str = None,
        posologie: str = None,
    ) -> None:
        """Persist medication usage or fail visibly instead of false success."""
        normalized_name = med_name.strip().upper()
        try:
            existing = (
                db.query(models.DoctorMedicationHabit)
                .filter(
                    models.DoctorMedicationHabit.doctor_id == doctor_id,
                    models.DoctorMedicationHabit.medication_name == normalized_name,
                    models.DoctorMedicationHabit.dosage == dosage,
                    models.DoctorMedicationHabit.posologie == posologie,
                )
                .first()
            )
            if existing:
                existing.usage_count += 1
            else:
                db.add(
                    models.DoctorMedicationHabit(
                        doctor_id=doctor_id,
                        medication_name=normalized_name,
                        dosage=dosage,
                        posologie=posologie,
                    )
                )

            global_med = (
                db.query(models.Medication)
                .filter(models.Medication.nom == normalized_name)
                .first()
            )
            if global_med:
                global_med.usage_count += 1
            db.commit()
        except Exception:
            db.rollback()
            raise

    def get_personalized_suggestions(
        self,
        db: Session,
        doctor_id: int,
        query: str = "",
    ) -> Dict[str, List[str]]:
        """Return suggestions from the local database only.

        R2 removes the implicit medicament.ma network fallback from this core
        path. Offline use therefore has deterministic latency and behaviour.
        """
        normalized_query = query.strip().upper()
        if not normalized_query:
            return {"medications": [], "dosages": [], "posologies": []}

        med_habits = (
            db.query(
                models.DoctorMedicationHabit.medication_name,
                func.sum(models.DoctorMedicationHabit.usage_count).label("total"),
            )
            .filter(
                models.DoctorMedicationHabit.doctor_id == doctor_id,
                models.DoctorMedicationHabit.medication_name.ilike(f"%{normalized_query}%"),
            )
            .group_by(models.DoctorMedicationHabit.medication_name)
            .order_by(
                case(
                    (
                        models.DoctorMedicationHabit.medication_name.ilike(
                            f"{normalized_query}%"
                        ),
                        0,
                    ),
                    else_=1,
                ),
                desc("total"),
            )
            .limit(10)
            .all()
        )
        meds = [row[0] for row in med_habits]

        if len(meds) < 10:
            global_meds = (
                db.query(models.Medication.nom)
                .filter(
                    models.Medication.nom.ilike(f"%{normalized_query}%"),
                    ~models.Medication.nom.in_(meds),
                )
                .order_by(
                    case(
                        (models.Medication.nom.ilike(f"{normalized_query}%"), 0),
                        else_=1,
                    ),
                    models.Medication.usage_count.desc(),
                )
                .limit(10 - len(meds))
                .all()
            )
            meds.extend(row[0] for row in global_meds)

        return {"medications": meds, "dosages": [], "posologies": []}


prescription_service = PrescriptionService()
