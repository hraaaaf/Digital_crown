from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend import models
from backend.services.prescription_context_guard import build_prescription_context, non_evaluable_plan, calculate_age
from backend.services.prescription_service_legacy import PrescriptionService as LegacyPrescriptionService


class PrescriptionService(LegacyPrescriptionService):
    """Legacy-compatible service with an explicit missing-data gate."""

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


prescription_service = PrescriptionService()
