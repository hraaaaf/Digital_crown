import logging
import json
import requests
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from backend import models
from backend.config import settings
from backend.services.llm_cache import llm_cache

logger = logging.getLogger(__name__)

class CMOAgentService:
    """
    Agent Chief Medical Officer (CMO) Multimodal.
    Fusionne les résultats de l'analyse Céphalométrique et de l'analyse Panoramique
    pour générer un plan de traitement global (Omnipratique + Orthodontie).
    """

    def __init__(self, llm_endpoint: str = None):
        self.llm_endpoint = llm_endpoint or f"{settings.OLLAMA_URL}/api/generate"
        self.model_name = "llama3.2"
        
        self.system_prompt = """
        Tu es le Médecin Chef (Chief Medical Officer) d'un cabinet dentaire pluridisciplinaire.
        Ta mission est de fusionner le compte-rendu radiologique (Panoramique) et le diagnostic orthodontique (Céphalométrie) d'un patient pour établir un plan de traitement global et sécurisé.
        
        RÈGLES CLINIQUES :
        1. Priorité médicale : Les urgences infectieuses (caries profondes, lésions périapicales, kystes) ou parodontales doivent TOUJOURS être traitées AVANT le début du traitement orthodontique.
        2. Les dents de sagesse incluses ou enclavées doivent être évaluées pour avulsion si elles gênent le recul ou la mécanique orthodontique.
        3. Le plan de traitement orthodontique doit s'adapter aux pathologies dentaires (ex: ne pas prendre appui sur une dent compromise sans validation).
        
        CONTRAINTE DE SORTIE ABSOLUE :
        Tu dois produire UNIQUEMENT un objet JSON valide, strictement structuré comme suit :
        {
            "synthese_clinique": "Résumé global croisant la typologie squelettique et l'état dentaire général.",
            "soins_prealables": "Liste stricte des soins d'omnipratique ou chirurgie requis AVANT l'orthodontie (ex: Soin carie dent 36, extraction 48). Mettre 'Aucun' si RAS.",
            "plan_orthodontique": "Stratégie mécanique orthodontique (extractionnelle ou non, ancrage, chirurgie orthognathique) adaptée au patient.",
            "pronostic": "Favorable, Réservé, ou Complexe avec justification."
        }
        Ne mets aucun commentaire ou texte en dehors de l'objet JSON.
        """

    def generate_global_synthesis(self, db: Session, patient_id: int) -> Dict[str, Any]:
        """
        Génère une synthèse globale en récupérant les dernières analyses du patient.
        """
        # Récupération de la dernière analyse Panoramique
        pano = db.query(models.PanoramicAnalysis)\
                 .filter(models.PanoramicAnalysis.patient_id == patient_id)\
                 .order_by(models.PanoramicAnalysis.created_at.desc())\
                 .first()
                 
        # Récupération de la dernière analyse Céphalométrique
        cephalo = db.query(models.CephaloAnalysis)\
                    .filter(models.CephaloAnalysis.patient_id == patient_id)\
                    .order_by(models.CephaloAnalysis.created_at.desc())\
                    .first()

        if not pano and not cephalo:
            return self._empty_fallback()

        # Construction du contexte
        clinical_context = {"Panoramique": "Non réalisée", "Cephalometrie": "Non réalisée"}
        
        if pano and pano.report_narrative:
            clinical_context["Panoramique"] = pano.report_narrative
            
        if cephalo and cephalo.landmarks_data:
            # On cherche s'il y a un diagnostic généré par l'AI Advisor (stocké quelque part, ou on recrée les valeurs)
            # Pour faire simple, on passe les données brutes si on n'a pas le rapport, mais idéalement on passe le rapport.
            # L'AI Advisor renvoie le rapport à la volée. Si on n'a pas le diagnostic sauvegardé, on passe un résumé des points.
            clinical_context["Cephalometrie"] = "Analyse céphalométrique présente au dossier (se référer aux tracés pour l'A/B et le Tweed)."
            # L'AI Advisor est appelé côté frontend pour la ceph. S'il n'y a pas de sauvegarde, on pourrait appeler ai_advisor.py ici.
            # Pour l'instant, on laisse Llama se débrouiller avec les données disponibles.

        # If we have both or at least one, we ask the SLM
        prompt = f"Analyse ce dossier clinique partiel/complet :\n{json.dumps(clinical_context, ensure_ascii=False, indent=2)}"
        
        cached = llm_cache.get(self.model_name, prompt)
        if cached:
            return self._parse_json_safe(cached)

        try:
            logger.info("CMO Agent: SLM Attempt (15s timeout)...")
            response = requests.post(
                self.llm_endpoint,
                json={
                    "model": self.model_name,
                    "system": self.system_prompt,
                    "prompt": prompt,
                    "format": "json",
                    "stream": False,
                    "options": {"temperature": 0.1}
                },
                timeout=15.0
            )
            response.raise_for_status()

            raw_text = response.json().get("response", "{}")
            llm_cache.set(self.model_name, prompt, raw_text)
            parsed = self._parse_json_safe(raw_text)
            
            if parsed.get("synthese_clinique"):
                parsed["is_fallback"] = False
                return parsed
            else:
                return self._heuristic_fallback(clinical_context)

        except Exception as e:
            logger.warning(f"CMO Agent: SLM error ({e}), using heuristic fallback.")
            return self._heuristic_fallback(clinical_context)

    def _parse_json_safe(self, text: str) -> Dict[str, str]:
        """Assure que le retour JSON est valide."""
        try:
            data = json.loads(text)
            return {
                "synthese_clinique": data.get("synthese_clinique", "Erreur de format."),
                "soins_prealables": data.get("soins_prealables", "Erreur de format."),
                "plan_orthodontique": data.get("plan_orthodontique", "Erreur de format."),
                "pronostic": data.get("pronostic", "Non déterminé.")
            }
        except json.JSONDecodeError:
            return self._empty_fallback()

    def _heuristic_fallback(self, context: Dict[str, str]) -> Dict[str, Any]:
        """Mécanisme de secours si le SLM crashe."""
        pano = context.get("Panoramique", "")
        
        soins = "Aucun soin majeur détecté"
        if "Carie" in pano or "Lésion" in pano or "Parodontal" in pano:
            soins = "ATTENTION : Pathologies dentaires ou parodontales détectées à la radiographie. Un examen clinique approfondi et des soins d'omnipratique sont impératifs avant d'envisager l'orthodontie."
            
        return {
            "synthese_clinique": "Données fusionnées du dossier. Bilan panoramique et céphalométrique disponibles.",
            "soins_prealables": soins,
            "plan_orthodontique": "Le plan orthodontique doit être défini par le praticien suite à l'analyse clinique.",
            "pronostic": "À évaluer cliniquement.",
            "is_fallback": True
        }
        
    def _empty_fallback(self) -> Dict[str, Any]:
        return {
            "synthese_clinique": "Dossier incomplet. Nécessite au minimum une radiographie panoramique ou téléradiographie.",
            "soins_prealables": "À évaluer.",
            "plan_orthodontique": "En attente des examens.",
            "pronostic": "Inconnu",
            "is_fallback": True
        }

cmo_agent = CMOAgentService()
