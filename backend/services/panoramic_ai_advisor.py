import logging
from backend.services.panoramic_expert_engine import panoramic_expert_engine

logger = logging.getLogger(__name__)

class PanoramicAIAdvisor:
    """
    Service d'Intelligence Clinique pour Radiographies Panoramiques.
    Phase 4 : Analyse experte 100% Déterministe (Arbre Décisionnel).
    Conformément aux exigences Ghost Elite : AUCUN LLM n'est utilisé.
    """
    
    def __init__(self):
        self.engine_name = "Digital Crown Expert System (Zero-LLM)"

    async def generate_report(self, vision_data: dict = None, detections: list = None) -> dict:
        """
        Génère un rapport clinique complet.
        Utilise exclusivement l'arbre décisionnel local pour garantir 100% 
        de reproductibilité, confidentialité, et rapidité, sans hallucination.
        """
        if detections is None and vision_data:
            detections = vision_data.get("detections", [])
        
        try:
            # Appel exclusif à l'arbre décisionnel (panoramic_expert_engine.py)
            expert_report = panoramic_expert_engine.generate_report(detections)
            
            # Post-processing : Ajout du Disclaimer
            disclaimer = "\n\n---\n*⚠️ **Disclaimer Médical** : Ce rapport est généré par un système expert déterministe à titre d'aide au diagnostic. Il ne remplace en aucun cas l'examen clinique et la validation finale par un praticien diplômé (expertise clinique finale).*"
            
            final_narrative = expert_report.get("narrative", "") + disclaimer
            
            return {
                "narrative_report": final_narrative,
                "engine": self.engine_name,
                "grounding_status": "EXPERT_TREE_ACTIVE",
                "severity": expert_report.get("severity", "LOW")
            }
            
        except Exception as e:
            logger.error(f"Erreur du Système Expert : {e}")
            return {
                "narrative_report": "Erreur lors de l'exécution de l'arbre décisionnel. Veuillez vérifier les logs.",
                "engine": self.engine_name,
                "grounding_status": "FAILED"
            }

panoramic_ai_advisor = PanoramicAIAdvisor()
