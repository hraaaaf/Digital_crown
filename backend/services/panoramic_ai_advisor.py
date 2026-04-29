import logging
from backend.services.panoramic_expert_engine import panoramic_expert_engine

logger = logging.getLogger(__name__)

class PanoramicAIAdvisor:
    """
    Clinical Intelligence Service for Panoramic X-Rays.
    Uses a deterministic Expert System (Local & Fast) instead of a heavy LLM.
    """
    
    def generate_clinical_report(self, vision_data: dict, patient_age: int = 25) -> dict:
        """
        Generates a structured clinical report using the Panoramic Expert Engine.
        """
        detections = vision_data.get("detections", [])
        
        # Délégation de l'intelligence métier au moteur expert déterministe
        expert_report = panoramic_expert_engine.generate_report(detections)
        
        return {
            "summary": expert_report["summary"],
            "narrative_report": expert_report["narrative"],
            "findings_count": expert_report["findings_count"],
            "severity": expert_report["severity"],
            "is_local_expert": True,
            "engine": "DENTEX_HEURISTIC_V1"
        }

panoramic_ai_advisor = PanoramicAIAdvisor()
