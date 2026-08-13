from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend import models
from backend.services.prescription_service import prescription_service
from backend.services.prescription_context_guard import calculate_age


class PrescriptionAgenticService:
    def generate_clinical_assessment(
        self,
        db: Session,
        patient_id: int,
        act_names: List[str],
        doctor_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        plan = prescription_service.resolve_smart_prescription(db, patient_id, act_names, doctor_id)
        patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
        plan["age"] = calculate_age(patient.date_naissance) if patient else None
        plan["weight"] = plan.get("patient_context", {}).get("weight")
        evaluation = plan.get("evaluation", {"status": "non_evaluable"})
        plan["bilan_markdown"] = (
            "### Données incomplètes\nAucune automatisation disponible."
            if evaluation.get("status") != "evaluable"
            else "### Évaluation déterministe\nContexte disponible."
        )
        return plan

    def design_treatment_plan(self, assessment: Dict[str, Any], patient_context: Dict[str, Any]) -> Dict[str, Any]:
        evaluation = assessment.get("evaluation", {})
        if evaluation.get("status") != "evaluable":
            return {
                "plan_nom": "Non évaluable",
                "prescriptions": [],
                "conseils_patient": [],
                "is_deterministic": True,
                "evaluation": evaluation or {"status": "non_evaluable"},
            }
        rows = [
            {
                "medicament": item.get("name", "").upper(),
                "dosage": item.get("dosage", ""),
                "forme": item.get("forme", "Comprimés"),
                "posologie": item.get("posologie", ""),
                "conseil": "",
            }
            for item in assessment.get("drugs", [])
        ]
        return {
            "plan_nom": f"Protocole {assessment.get('act_context', 'Standard')}",
            "prescriptions": rows,
            "conseils_patient": [],
            "is_deterministic": True,
            "evaluation": evaluation,
        }

    def _calculate_age(self, birth_date):
        return calculate_age(birth_date)


prescription_agentic = PrescriptionAgenticService()
