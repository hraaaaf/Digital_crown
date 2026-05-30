import logging
from typing import Dict, Optional, Any
from backend import schemas
from backend.config import settings

logger = logging.getLogger(__name__)

class ClinicalNorms:
    CHILD = {
        "ab_mean": 4.2, "ab_dev": 3.2,
        "a_mean": 2.8, "a_dev": 3.3,
        "b_mean": -1.5, "b_dev": 4.5,
        "severe_cl2": 7.4, "severe_cl3": -6.0,
        "tweed_default": 26,
        "impa_default": 90,
        "if_default": 107
    }
    ADULT = {
        "ab_mean": 2.3, "ab_dev": 3.1,
        "a_mean": 2.3, "a_dev": 3.0,
        "b_mean": 0.0, "b_dev": 4.9,
        "severe_cl2": 8.0, "severe_cl3": -4.9,
        "tweed_default": 26,
        "impa_default": 90,
        "if_default": 107
    }

    @classmethod
    def get(cls, is_child: bool) -> Dict[str, float]:
        return cls.CHILD if is_child else cls.ADULT

class AIAdvisor:
    """
    Clinical Intelligence Service (Ghost Brain V2 - NLG Déterministe).
    Remplace le LLM local (Ollama) par un moteur de règles expert (NLG) 
    qui génère un texte médical fluide, précis et instantané (<10ms).
    """

    def __init__(self):
        # Configuration purement symbolique pour compatibilité avec l'existant
        self.model_name = "ghost-brain-nlg"

    def generate_diagnostic(self, result: schemas.CephaloAnalysisResult, use_slm: bool = False) -> Dict[str, str]:
        """
        Génère un diagnostic expert instantané. Le paramètre use_slm est ignoré.
        """
        metrics = result.metrics
        age = result.analysis_metadata.cohort # "Enfant (9 ans)" or "Adulte"
        
        logger.info("Ghost Brain V2: Génération déterministe (NLG) de l'analyse céphalométrique")
        return self._generate_nlg_report(metrics, age)

    def _generate_nlg_report(self, metrics: schemas.AnalysisMetrics, cohort: str) -> Dict[str, str]:
        """
        Deterministic expert rule engine (NLG).
        Génère un rapport clinique complet basé sur les standards COM.
        """
        osseuse = metrics.analyse_osseuse
        dentaire = metrics.analyse_dentaire
        is_child = "Enfant" in cohort
        
        # --- NORMES ---
        norms = ClinicalNorms.get(is_child)
        NORM_AB_MEAN = norms["ab_mean"]
        NORM_AB_DEV = norms["ab_dev"]
        NORM_A_MEAN = norms["a_mean"]
        NORM_A_DEV = norms["a_dev"]
        NORM_B_MEAN = norms["b_mean"]
        NORM_B_DEV = norms["b_dev"]
        
        ab_data = osseuse.Decalage_A_B
        tweed_data = osseuse.Angle_de_Tweed
        sit_a_data = osseuse.Situation_A
        sit_b_data = osseuse.Situation_B
        
        ab_status = ab_data.status
        ab_value = ab_data.valeur if ab_data.valeur is not None else NORM_AB_MEAN
        tweed_status = tweed_data.status
        tweed_value = tweed_data.valeur if tweed_data.valeur is not None else norms["tweed_default"]
        sit_a_value = sit_a_data.valeur if sit_a_data.valeur is not None else NORM_A_MEAN
        sit_b_value = sit_b_data.valeur if sit_b_data.valeur is not None else NORM_B_MEAN
        
        # --- SYNTHESE SQUELETTIQUE ---
        diag_os_parts = ["L'analyse céphalométrique révèle"]
        
        if ab_status == "High":
            severe_cl2 = NORM_AB_MEAN + 2 * NORM_AB_DEV
            if ab_value and ab_value > severe_cl2:
                diag_os_parts.append(f"une structure de Classe II sévère (A-B = {ab_value} mm).")
            else:
                diag_os_parts.append(f"une structure de Classe II modérée (A-B = {ab_value} mm).")
        elif ab_status == "Low":
            severe_cl3 = NORM_AB_MEAN - 2 * NORM_AB_DEV
            if ab_value and ab_value < severe_cl3:
                diag_os_parts.append(f"une structure de Classe III sévère (A-B = {ab_value} mm).")
            else:
                diag_os_parts.append(f"une structure de Classe III modérée (A-B = {ab_value} mm).")
        else:
            diag_os_parts.append(f"une structure de Classe I normosquelettique (A-B = {ab_value} mm).")
            
        diag_os_parts.append("Ce décalage est principalement dû à")
        
        sit_a_seuil_sup = NORM_A_MEAN + NORM_A_DEV
        sit_a_seuil_inf = NORM_A_MEAN - NORM_A_DEV
        sit_b_seuil_sup = NORM_B_MEAN + NORM_B_DEV
        sit_b_seuil_inf = NORM_B_MEAN - NORM_B_DEV
        
        causes = []
        if sit_a_value > sit_a_seuil_sup: causes.append(f"un maxillaire prognathique (+{sit_a_value} mm)")
        elif sit_a_value < sit_a_seuil_inf: causes.append(f"un maxillaire rétrognathique ({sit_a_value} mm)")
        
        if sit_b_value > sit_b_seuil_sup: causes.append(f"une mandibule prognathique (+{sit_b_value} mm)")
        elif sit_b_value < sit_b_seuil_inf: causes.append(f"une mandibule rétrognathique ({sit_b_value} mm)")
        
        if causes:
            diag_os_parts.append(" et ".join(causes) + ".")
        else:
            diag_os_parts.append("des bases osseuses bien positionnées par rapport à la base du crâne.")
            
        diag_os_parts.append("Sur le plan vertical, on observe")
        if tweed_status == "High":
            diag_os_parts.append(f"une typologie hyperdivergente (Tweed = {tweed_value}°), caractérisant une face longue avec un risque d'ouverture de l'occlusion.")
        elif tweed_status == "Low":
            diag_os_parts.append(f"une typologie hypodivergente (Tweed = {tweed_value}°), caractérisant une face courte avec un risque de surplomb.")
        else:
            diag_os_parts.append(f"un équilibre normodivergent favorable (Tweed = {tweed_value}°).")
            
        diag_os = " ".join(diag_os_parts)
        
        # --- SYNTHESE DENTAIRE ---
        impa_data = dentaire.IMPA
        if_data = dentaire.I_Francfort
        surplomb_data = dentaire.Surplomb
        recouv_data = dentaire.Recouvrement
        
        impa_status = impa_data.status
        impa_value = impa_data.valeur if impa_data.valeur is not None else norms["impa_default"]
        if_status = if_data.status
        if_value = if_data.valeur if if_data.valeur is not None else norms["if_default"]
        
        diag_dent_parts = ["Au niveau dento-alvéolaire,"]
        
        if impa_status == "High":
            diag_dent_parts.append(f"l'incisive inférieure est vestibuloversée (IMPA = {impa_value}°).")
        elif impa_status == "Low":
            diag_dent_parts.append(f"l'incisive inférieure est linguoversée (IMPA = {impa_value}°).")
        else:
            diag_dent_parts.append(f"les incisives inférieures sont bien positionnées sur leur base (IMPA = {impa_value}°).")
            
        if if_status == "High":
            diag_dent_parts.append(f"On note également une proalvéolie maxillaire (I/F = {if_value}°).")
        elif if_status == "Low":
            diag_dent_parts.append(f"On note également une rétroalvéolie maxillaire (I/F = {if_value}°).")
            
        if impa_data.plage_compensation and impa_status == "Compensated":
            diag_dent_parts.append("Ces inclinaisons correspondent à une compensation dento-alvéolaire physiologique du décalage squelettique.")
            
        if surplomb_data.valeur and surplomb_data.valeur > 3:
            diag_dent_parts.append("Cliniquement, cela se traduit par un surplomb (overjet) augmenté.")
        if recouv_data.valeur and recouv_data.valeur > 3:
            diag_dent_parts.append("Il y a aussi une supraclusion incisive (deep bite).")
            
        diag_dent = " ".join(diag_dent_parts)
        
        # --- STRATEGIE ---
        strat_parts = []
        SEVERE_CL2_THRESHOLD = norms["severe_cl2"]
        SEVERE_CL3_THRESHOLD = norms["severe_cl3"]
        
        strat_parts.append("🎯 OBJECTIFS THÉRAPEUTIQUES :")
        if is_child:
            strat_parts.append("Patient en croissance : L'objectif prioritaire est la modification orthopédique.")
        else:
            strat_parts.append("Patient adulte : L'objectif est la compensation orthodontique ou la chirurgie.")
            
        if ab_status == "High":
            if is_child:
                strat_parts.append("- Correction de la Classe II par propulsion mandibulaire (élastiques, Herbst).")
            else:
                if ab_value and ab_value > SEVERE_CL2_THRESHOLD:
                    strat_parts.append("- Approche ortho-chirurgicale recommandée (avancée mandibulaire BSSO).")
                else:
                    strat_parts.append("- Compensation avec extractions (14/24 ou 15/25) et recul en masse.")
        elif ab_status == "Low":
            if is_child:
                strat_parts.append("- Masque facial de traction postéro-antérieure pour stimuler le maxillaire.")
            else:
                strat_parts.append("- Chirurgie d'avancée maxillaire (Lefort I) à envisager si la fonction est altérée.")
        
        if tweed_status == "High":
            strat_parts.append("- ⚠️ Contrôle vertical strict impératif (ancrage absolu, éviter les extractions maxillaires seules).")
        
        if impa_status == "High" and not is_child:
            strat_parts.append("- Rétroclinaison incisive mandibulaire nécessaire pour l'esthétique du profil.")
            
        strat_parts.append("\n🛠 MOYENS PROPOSÉS :")
        if is_child:
            strat_parts.append("Appareillage fonctionnel interceptif, suivi d'un traitement multi-attaches post-éruptif.")
        else:
            strat_parts.append("Multi-attaches auto-ligaturants. Mini-vis d'ancrage recommandées.")
            
        return {
            "diagnostic_squelettique": diag_os,
            "analyse_dentaire": diag_dent,
            "strategie_therapeutique": "\n".join(strat_parts),
            "is_fallback": False # GhostBrain NLG est la source officielle
        }

ai_advisor = AIAdvisor()