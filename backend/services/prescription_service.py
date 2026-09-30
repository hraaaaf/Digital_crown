from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import desc, func
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

        result = super().resolve_smart_prescription(db, patient_id, acts, doctor_id)
        result["patient_context"] = context.as_dict()
        result["evaluation"] = context.evaluation_dict()
        return result

    def check_safety(self, db: Session, patient_id: int, drug_names: List[str]) -> List[Dict[str, Any]]:
        """Expose legacy safety warnings minus known non-evaluable false signals."""
        warnings = super().check_safety(db, patient_id, drug_names)
        filtered: List[Dict[str, Any]] = []
        for warning in warnings:
            if str(warning.get("antecedent", "")).strip().lower() == "allergie":
                continue
            if warning.get("drug") == "omission-prophylaxie":
                continue
            if warning.get("drug") == "antibiotique-injustifie":
                continue
            filtered.append(warning)
        return filtered

    @staticmethod
    def _normalize_preference_act_code(act_code: str) -> str:
        normalized = " ".join((act_code or "").strip().upper().split())
        if not normalized:
            raise ValueError("Code acte vide")
        return normalized

    def learn_habit(
        self,
        db: Session,
        doctor_id: int,
        act_code: str,
        drugs: List[Dict[str, Any]],
        *,
        label: Optional[str] = None,
        preference_type: str = "PROTOCOL",
        indication: Optional[str] = None,
        is_favorite: Optional[bool] = None,
    ):
        """Persist a reusable prescription object while preserving legacy callers."""
        normalized_act_code = self._normalize_preference_act_code(act_code)
        normalized_type = str(preference_type or "PROTOCOL").strip().upper()
        if normalized_type not in {"PROTOCOL", "SAVED_PRESCRIPTION"}:
            raise ValueError("Type de préférence ordonnance invalide")
        cleaned_drugs = [
            {
                "name": d.get("name", d.get("nom", "")),
                "dosage": d.get("dosage", ""),
                "forme": d.get("forme", ""),
                "posologie": d.get("posologie", ""),
                "type": d.get("type", "MEDICAMENT"),
                "quantite": d.get("quantite"),
                "non_substituable": bool(d.get("non_substituable", False)),
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
                existing.preference_type = normalized_type
                existing.label = (label or act_code).strip()[:100] or None
                existing.indication = (indication or "").strip() or None
                if is_favorite is not None:
                    existing.is_favorite = bool(is_favorite)
            else:
                db.add(
                    models.DoctorPrescriptionPreference(
                        doctor_id=doctor_id,
                        act_code=normalized_act_code,
                        label=(label or act_code).strip()[:100] or None,
                        preference_type=normalized_type,
                        indication=(indication or "").strip() or None,
                        is_favorite=bool(is_favorite) if is_favorite is not None else False,
                        drugs_json=cleaned_drugs,
                    )
                )
            db.commit()
        except Exception:
            db.rollback()
            raise

    def get_personalized_suggestions(self, db: Session, doctor_id: int, query: str = "") -> Dict[str, List[str]]:
        """Keep query search behavior and expose doctor-scoped quick picks when q is empty."""
        normalized_query = (query or "").strip()
        if normalized_query:
            return super().get_personalized_suggestions(db, doctor_id, normalized_query)

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
        """Return doctor-scoped reusable prescription objects with Neo metadata."""
        presets = db.query(models.DoctorPrescriptionPreference).filter(
            models.DoctorPrescriptionPreference.doctor_id == doctor_id
        ).order_by(
            models.DoctorPrescriptionPreference.is_favorite.desc(),
            models.DoctorPrescriptionPreference.last_used.desc().nullslast(),
            models.DoctorPrescriptionPreference.updated_at.desc(),
            models.DoctorPrescriptionPreference.id.desc(),
        ).limit(50).all()

        return [
            {
                "id": preset.id,
                "act_context": preset.act_code,
                "label": (preset.label or preset.act_code.strip().lower().capitalize()),
                "kind": preset.preference_type or "PROTOCOL",
                "drugs": preset.drugs_json,
                "indication": preset.indication,
                "is_favorite": bool(preset.is_favorite),
                "usage_count": int(preset.usage_count or 0),
                "last_used": preset.last_used.isoformat() if preset.last_used else None,
            }
            for preset in presets
        ]

    def record_reusable_use(self, db: Session, doctor_id: int, preset_id: int) -> bool:
        preset = db.query(models.DoctorPrescriptionPreference).filter(
            models.DoctorPrescriptionPreference.id == preset_id,
            models.DoctorPrescriptionPreference.doctor_id == doctor_id,
        ).first()
        if preset is None:
            raise HTTPException(status_code=404, detail="Élément réutilisable introuvable")
        preset.usage_count = int(preset.usage_count or 0) + 1
        preset.last_used = datetime.utcnow()
        db.commit()
        return True

    def set_reusable_favorite(self, db: Session, doctor_id: int, preset_id: int, value: bool) -> bool:
        preset = db.query(models.DoctorPrescriptionPreference).filter(
            models.DoctorPrescriptionPreference.id == preset_id,
            models.DoctorPrescriptionPreference.doctor_id == doctor_id,
        ).first()
        if preset is None:
            raise HTTPException(status_code=404, detail="Élément réutilisable introuvable")
        preset.is_favorite = bool(value)
        db.commit()
        return True

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
