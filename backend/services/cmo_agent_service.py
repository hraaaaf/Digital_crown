import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from backend import models
from backend.services.ghost_memory_service import ghost_memory

logger = logging.getLogger(__name__)

class CMOAgentService:
    """
    Agent Chief Medical Officer (Ghost Brain V2 - NLG).
    Fusionne instantanément (<10ms) la radio panoramique et la céphalométrie
    pour générer un plan de traitement global (Omnipratique + Orthodontie).
    Mémorise ses déductions dans GhostMemoryLog.
    """

    def generate_global_synthesis(self, db: Session, patient_id: int, employer_id: int = 1) -> Dict[str, Any]:
        """
        Génère une synthèse globale en croisant les données, sans LLM.
        """
        pano = db.query(models.PanoramicAnalysis)\
                 .filter(models.PanoramicAnalysis.patient_id == patient_id)\
                 .order_by(models.PanoramicAnalysis.created_at.desc())\
                 .first()
                 
        cephalo = db.query(models.CephaloAnalysis)\
                    .filter(models.CephaloAnalysis.patient_id == patient_id)\
                    .order_by(models.CephaloAnalysis.created_at.desc())\
                    .first()

        if not pano and not cephalo:
            return self._empty_fallback()

        # Construction du contexte pour la synthèse
        synthese_parts = ["Dossier clinique fusionné."]
        soins_parts = []
        ortho_parts = []
        pronostic = "Favorable"
        
        has_caries = False
        has_infections = False
        
        if pano and pano.report_narrative:
            pano_text = pano.report_narrative.lower()
            if "carie" in pano_text:
                has_caries = True
                soins_parts.append("- Traitement conservateur des lésions carieuses.")
            if "lésion" in pano_text or "kyste" in pano_text or "parodont" in pano_text or "infection" in pano_text:
                has_infections = True
                soins_parts.append("- Assainissement parodontal et endodontique impératif.")
                pronostic = "Réservé"
            if "sagesse" in pano_text or "incluse" in pano_text:
                soins_parts.append("- Évaluation pour avulsion des dents de sagesse incluses.")
                
            synthese_parts.append("L'analyse panoramique révèle des éléments nécessitant une attention omnipratique.")
        else:
            synthese_parts.append("Aucune donnée panoramique récente.")
            
        if cephalo:
            synthese_parts.append("L'analyse céphalométrique est disponible au dossier.")
            if has_caries or has_infections:
                ortho_parts.append("⚠️ ATTENTION : La mécanique orthodontique doit être reportée après assainissement total.")
            else:
                ortho_parts.append("Feu vert pour le début du traitement orthodontique.")
                
            ortho_parts.append("Le plan orthodontique exact doit s'appuyer sur le diagnostic céphalométrique de l'AI Advisor.")
        else:
            synthese_parts.append("Aucune donnée céphalométrique.")
            ortho_parts.append("Analyse céphalométrique requise pour établir le plan de traitement.")

        if not soins_parts:
            soins_parts.append("Aucun soin préalable identifié à l'imagerie. Validation clinique requise.")
            
        result = {
            "synthese_clinique": " ".join(synthese_parts),
            "soins_prealables": "\n".join(soins_parts),
            "plan_orthodontique": "\n".join(ortho_parts),
            "pronostic": pronostic,
            "is_fallback": False
        }
        
        # --- Mémoire (Ghost Brain V2) ---
        # On sauvegarde cet insight pour que le bot s'en souvienne
        context_str = result["synthese_clinique"] + result["soins_prealables"]
        insight_type = "URGENCE" if has_infections else ("PHARMACOLOGIE" if has_caries else "ORTHO")
        content = "Recommandation CMO : " + ("Soins requis avant orthodontie." if has_infections or has_caries else "Prêt pour orthodontie.")
        
        ghost_memory.add_memory(
            db=db,
            patient_id=patient_id,
            employer_id=employer_id,  # Idéalement injecté via auth
            insight_type=insight_type,
            content=content,
            context_data=context_str
        )
        
        return result

    def _empty_fallback(self) -> Dict[str, Any]:
        return {
            "synthese_clinique": "Dossier incomplet. Nécessite au minimum une radiographie panoramique ou téléradiographie.",
            "soins_prealables": "À évaluer.",
            "plan_orthodontique": "En attente des examens.",
            "pronostic": "Inconnu",
            "is_fallback": True
        }

cmo_agent = CMOAgentService()
