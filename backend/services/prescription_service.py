from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import case, desc, func
from sqlalchemy.orm import Session

from backend import models
from backend.services.prescription_context_guard import build_prescription_context, non_evaluable_plan, calculate_age
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

    @staticmethod
    def _normalize_preference_act_code(act_code: str) -> str:
        normalized = " ".join((act_code or "").strip().upper().split())
        if not normalized:
            raise ValueError("Code acte vide")
        return normalized

    def learn_habit(self, db: Session, doctor_id: int, act_code: str, drugs: List[Dict[str, Any]]):
        """Persist a doctor prescription preference and never mask DB failures."""
        normalized_act_code = self._normalize_preference_act_code(act_code)
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
            existing = db.query(models.DoctorPrescriptionPreference).filter(
                models.DoctorPrescriptionPreference.doctor_id == doctor_id,
                models.DoctorPrescriptionPreference.act_code == normalized_act_code,
            ).first()

            if existing:
                existing.drugs_json = cleaned_drugs
            else:
                db.add(
                    models.DoctorPrescriptionPreference(
                        doctor_id=doctor_id,
                        act_code=normalized_act_code,
                        drugs_json=cleaned_drugs,
                    )
                )
            db.commit()
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
        """Persist medication usage and never mask database failures."""
        normalized_name = med_name.strip().upper()
        try:
            existing = db.query(models.DoctorMedicationHabit).filter(
                models.DoctorMedicationHabit.doctor_id == doctor_id,
                models.DoctorMedicationHabit.medication_name == normalized_name,
                models.DoctorMedicationHabit.dosage == dosage,
                models.DoctorMedicationHabit.posologie == posologie,
            ).first()

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

            global_med = db.query(models.Medication).filter(
                models.Medication.nom == normalized_name
            ).first()
            if global_med:
                global_med.usage_count += 1

            db.commit()
        except Exception:
            db.rollback()
            raise

    def get_personalized_suggestions(self, db: Session, doctor_id: int, query: str = "") -> Dict[str, List[str]]:
        """Return doctor-scoped suggestions from the local database only."""
        normalized_query = (query or "").strip().upper()
        if normalized_query:
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
            medications = [row[0] for row in med_habits]

            if len(medications) < 10:
                global_meds = (
                    db.query(models.Medication.nom)
                    .filter(
                        models.Medication.nom.ilike(f"%{normalized_query}%"),
                        ~models.Medication.nom.in_(medications),
                    )
                    .order_by(
                        case(
                            (models.Medication.nom.ilike(f"{normalized_query}%"), 0),
                            else_=1,
                        ),
                        models.Medication.usage_count.desc(),
                    )
                    .limit(10 - len(medications))
                    .all()
                )
                medications.extend(row[0] for row in global_meds)

            return {"medications": medications, "dosages": [], "posologies": []}

        recent_rows = (
            db.query(
                models.DoctorMedicationHabit.medication_name,
                func.max(models.DoctorMedicationHabit.last_used).label("last_used"),
            )
            .filter(models.DoctorMedicationHabit.doctor_id == doctor_id)
            .group_by(models.DoctorMedicationHabit.medication_name)
            .order_by(desc("last_used"), models.DoctorMedicationHabit.medication_name.asc())
            .limit(5)
            .all()
        )
        frequent_rows = (
            db.query(
                models.DoctorMedicationHabit.medication_name,
                func.sum(models.DoctorMedicationHabit.usage_count).label("total"),
            )
            .filter(models.DoctorMedicationHabit.doctor_id == doctor_id)
            .group_by(models.DoctorMedicationHabit.medication_name)
            .order_by(desc("total"), models.DoctorMedicationHabit.medication_name.asc())
            .limit(5)
            .all()
        )

        recent = [row[0] for row in recent_rows]
        frequent = [row[0] for row in frequent_rows]
        merged = list(dict.fromkeys([*recent, *frequent]))[:8]
        return {
            "medications": merged,
            "dosages": [],
            "posologies": [],
            "recent_medications": recent,
            "frequent_medications": frequent,
        }

    def get_doctor_presets(self, db: Session, doctor_id: int) -> List[Dict[str, Any]]:
        """Return doctor-scoped persisted presets in a stable order."""
        presets = db.query(models.DoctorPrescriptionPreference).filter(
            models.DoctorPrescriptionPreference.doctor_id == doctor_id
        ).order_by(
            models.DoctorPrescriptionPreference.updated_at.desc(),
            models.DoctorPrescriptionPreference.id.desc(),
        ).limit(10).all()

        return [
            {
                "id": preset.id,
                "act_context": preset.act_code,
                "drugs": preset.drugs_json,
            }
            for preset in presets
        ]

    def delete_doctor_preset(self, db: Session, doctor_id: int, act_code: str) -> bool:
        """Delete the exact doctor preference row used by save/load."""
        normalized_act_code = self._normalize_preference_act_code(act_code)
        try:
            deleted = db.query(models.DoctorPrescriptionPreference).filter(
                models.DoctorPrescriptionPreference.doctor_id == doctor_id,
                models.DoctorPrescriptionPreference.act_code == normalized_act_code,
            ).delete(synchronize_session=False)
            if not deleted:
                db.rollback()
                raise HTTPException(status_code=404, detail="Preset introuvable")
            db.commit()
            return True
        except HTTPException:
            raise
        except Exception:
            db.rollback()
            raise

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


prescription_service = PrescriptionService()
