import logging
import os
import json
import requests
from backend.services.panoramic_expert_engine import panoramic_expert_engine

logger = logging.getLogger(__name__)

class PanoramicAIAdvisor:
    """
    Service d'Intelligence Clinique pour Radiographies Panoramiques (OralGPT).
    Phase 4 : Analyse experte, ancrage (grounding) et rapport pédagogique.
    """
    
    def __init__(self, llm_endpoint: str = "http://localhost:11434/api/generate"):
        self.llm_endpoint = llm_endpoint
        self.model_name = "llama3.2"
        
        # Tâche 4.1 : Ingénierie du System Prompt (Le Persona Restrictif)
        self.SYSTEM_PROMPT = """
        Tu es OralGPT, un expert en radiologie dentaire et chirurgie buccale de classe mondiale.
        Ta mission est d'analyser les résultats de détection fournis en JSON pour cette radio panoramique.
        
        CONSIGNES DE RÉDACTION :
        1. Rédige un compte-rendu en Français, concis et structuré.
        2. Divise l'analyse par quadrants (Standard FDI : Quadrants 1, 2, 3, 4).
        3. Ne commente QUE les données présentes dans le JSON de détection (Grounding strict).
        4. Si une dent n'est pas mentionnée, considère-la comme saine ou absente, mais ne spécule jamais sur des pathologies non détectées.
        5. Utilise la numérotation FDI (ex: 11, 26, 38, 46). N'utilise JAMAIS la numérotation américaine (1-32).
        
        STRUCTURE ATTENDUE (MARKDOWN) :
        ### 📊 Synthèse Globale
        (Résumé de l'état bucco-dentaire en 2 phrases max)
        
        ### 🦷 Analyse par Quadrants
        - **Quadrant 1 (Haut Droit)** : [Détails ou "RAS"]
        - **Quadrant 2 (Haut Gauche)** : [Détails ou "RAS"]
        - **Quadrant 3 (Bas Gauche)** : [Détails ou "RAS"]
        - **Quadrant 4 (Bas Droit)** : [Détails ou "RAS"]
        
        ### 💡 Recommandations Cliniques
        (Actions à entreprendre : soins, tests, imagerie complémentaire)
        """

    def _ground_detections(self, detections: list) -> str:
        """
        Tâche 4.2 : Mécanisme d'Ancrage (Grounding) avec Traduction.
        Convertit les labels YOLO (EN) en termes cliniques (FR) pour l'IA.
        """
        label_translation = {
            "Caries": "Carie",
            "Deep Caries": "Carie profonde",
            "Impacted": "Dent incluse",
            "Periapical Lesion": "Lésion périapicale",
            "Implant": "Implant",
            "Crown": "Couronne prothétique",
            "Endodontic": "Traitement endodontique (canalaire)",
            "Restoration": "Restauration / Obturation",
            "Filling": "Obturation"
        }

        if not detections:
            return "Scanner IA : Aucune anomalie détectée sur l'ensemble de la denture."
        
        lines = ["CONTEXTE CLINIQUE ISSU DU SCANNER (GROUNDING) :"]
        for det in detections:
            raw_pathology = det.get("pathology", "Inconnue")
            pathology = label_translation.get(raw_pathology, raw_pathology)
            tooth = det.get("tooth", "N/A")
            conf = int(det.get("confidence", 0) * 100)
            lines.append(f"- Dent {tooth} : {pathology} détectée avec un indice de confiance de {conf}%.")
        
        return "\n".join(lines)

    async def generate_report(self, vision_data: dict = None, detections: list = None) -> dict:
        """
        Génère un rapport clinique complet.
        Utilise OralGPT LOCAL (Ollama) avec Grounding pour éviter les hallucinations.
        """
        if detections is None and vision_data:
            detections = vision_data.get("detections", [])
        
        # 1. Mécanisme d'Ancrage (Grounding)
        grounded_context = self._ground_detections(detections)
        
        # 2. Construction du Prompt Final
        prompt = f"{self.SYSTEM_PROMPT}\n\n{grounded_context}\n\nOralGPT, rédige maintenant ton analyse :"
        
        try:
            # 3. Appel Ollama (Llama 3.2)
            # Utilisation de stream=False pour récupérer le bloc complet
            response = requests.post(
                self.llm_endpoint,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Rigueur clinique
                        "num_predict": 1000
                    }
                },
                timeout=8.0 # Timeout SaaS-Ready
            )
            response.raise_for_status()
            ai_text = response.json().get("response", "Erreur lors de la génération du texte.")
            
            # Post-processing : Ajout du Disclaimer si manquant
            disclaimer = "\n\n---\n*⚠️ **Disclaimer Médical** : Ce rapport est généré par une intelligence artificielle (OralGPT) à titre d'aide au diagnostic. Il ne remplace en aucun cas l'examen clinique et la validation finale par un praticien diplômé (expertise clinique finale).*"
            if "expertise clinique finale" not in ai_text.lower():
                ai_text += disclaimer
                
            return {
                "narrative_report": ai_text,
                "engine": f"OralGPT ({self.model_name})",
                "grounding_status": "OK"
            }
            
        except Exception as e:
            logger.error(f"OralGPT Error : {e}")
            # Fallback sur le moteur expert heuristique si OralGPT est indisponible
            expert_report = panoramic_expert_engine.generate_report(detections)
            disclaimer = "\n\n---\n*⚠️ **Disclaimer Médical** : Ce rapport est généré par un moteur expert à titre d'aide au diagnostic. Il ne remplace en aucun cas l'examen clinique et la validation finale par un praticien diplômé (expertise clinique finale).*"
            return {
                "narrative_report": expert_report.get("narrative", "") + disclaimer + "\n\n*(Note: Rapport généré par le moteur expert suite à une indisponibilité d'OralGPT)*",
                "engine": "Expert Engine (Fallback)",
                "grounding_status": "FAILED"
            }

panoramic_ai_advisor = PanoramicAIAdvisor()
