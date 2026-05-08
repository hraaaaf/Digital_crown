import logging
import json
import requests
from typing import Dict, Optional, Any
from backend import schemas

logger = logging.getLogger(__name__)

class AIAdvisor:
    """
    Clinical Intelligence Service (SLM).
    Interfaces the Geometric Engine with a local LLM (Llama-3/Mistral) for COM synthesis and Pharmacology.
    Produces strictly structured diagnostic reports (Structured JSON Output).
    """
    
    def __init__(self, llm_endpoint: str = "http://localhost:11434/api/generate"):
        self.llm_endpoint = llm_endpoint
        self.model_name = "llama3.2" 
        
        # Prompt Engineering - Role and Output Locking
        self.system_prompt = """
        Tu es un Expert Orthodontiste Senior au sein du Centre d'Orthodontie Moderne (COM).
        Ta mission est de rédiger une synthèse diagnostique basée sur les métriques céphalométriques fournies.
        
        RÈGLES CLINIQUES :
        1. Ton ton doit être purement médical, factuel, et synthétique (style compte-rendu radiologique).
        2. Analyse en priorité les valeurs ayant un Z-score > 1.5 (déviations sévères).
        3. Identifie et nomme explicitement les phénomènes marqués comme "Compensated" (Compensations dento-alvéolaires).
        4. Utilise un vocabulaire strict : prognathie, rétrognathie, biproalvéolie, hyperdivergent, hypodivergent, etc.
        
        CONTRAINTE DE SORTIE ABSOLUE :
        Tu ne dois produire AUCUN texte libre, AUCUN commentaire d'introduction ou de conclusion.
        Ta réponse doit être EXCLUSIVEMENT un objet JSON valide, strictement structuré selon ce schéma exact :
        {
            "diagnostic_squelettique": "Analyse de la position des bases osseuses (A/B) et du type de croissance (Tweed).",
            "analyse_dentaire": "Évaluation des inclinaisons incisives (IMPA, I/Francfort) et des phénomènes de compensation.",
            "strategie_therapeutique": "Recommandations globales basées sur les objectifs COM (ex: contrôle vertical, propulsion mandibulaire, levée de compensation)."
        }
        """

    def generate_diagnostic(self, result: schemas.CephaloAnalysisResult, use_slm: bool = False) -> Dict[str, str]:
        """
        Ingests typed analysis results and generates the diagnostic report.
        """
        metrics = result.metrics
        age = result.analysis_metadata.cohort # "Enfant (9 ans)" or "Adulte"
        
        # 1. Patient context preparation
        patient_context = f"Profil: {age}. "

        # 2. Smart filtering: Isolate relevant data (High Z-score or Compensations)
        clinical_data = {
            "Contexte": patient_context,
            "Deviations_Severes_Ou_Compensees": {}
        }
        
        osseuse = metrics.analyse_osseuse
        dentaire = metrics.analyse_dentaire
        
        for category, measures in [("Squelettique", osseuse), ("Dentaire", dentaire)]:
            # Dynamic extraction from Pydantic model
            for name, measure in measures:
                if not isinstance(measure, schemas.MeasureData):
                    continue
                if measure.z_score >= 1.0 or measure.status in ["High", "Low", "Compensated"]:
                    clinical_data["Deviations_Severes_Ou_Compensees"][name] = {
                        "Valeur": measure.valeur,
                        "Norme": f"[{measure.norm_min} - {measure.norm_max}]",
                        "Statut": measure.status,
                        "Interprétation_Moteur": measure.interpretation
                    }

        # Default mode: expert heuristic (fast, reliable, COM standards)
        if not use_slm:
            logger.info("AI Advisor: Heuristic mode active (COM standards)")
            return self._heuristic_fallback(osseuse, dentaire, age)
        
        # SLM Mode: attempt with extended timeout (5s), fallback on failure
        prompt = f"Analyse ces données cliniques et génère le JSON attendu :\n{json.dumps(clinical_data, ensure_ascii=False, indent=2)}"
        
        try:
            logger.info("AI Advisor: SLM Attempt (5s timeout)...")
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
                timeout=5.0  # Timeout adapted for Elite Edition
            )
            response.raise_for_status()
            
            raw_text = response.json().get("response", "{}")
            parsed = self._parse_json_safe(raw_text)
            
            # Minimal consistency check
            if parsed.get("diagnostic_squelettique") and len(parsed["diagnostic_squelettique"]) > 20:
                logger.info("AI Advisor: SLM responded correctly")
                return parsed
            else:
                logger.warning("AI Advisor: SLM invalid response, heuristic fallback (incomplete data analysis)")
                return self._heuristic_fallback(osseuse, dentaire, age)

        except requests.exceptions.Timeout:
            logger.warning("AI Advisor: SLM timeout (5s), heuristic fallback (expert mode active)")
            return self._heuristic_fallback(osseuse, dentaire, age)
        except requests.exceptions.ConnectionError:
            logger.warning("AI Advisor: SLM offline (Ollama unavailable), heuristic fallback (expert mode active)")
            return self._heuristic_fallback(osseuse, dentaire, age)
        except Exception as e:
            logger.warning(f"AI Advisor: SLM critical error ({e}), heuristic fallback (expert mode active)")
            return self._heuristic_fallback(osseuse, dentaire, age)

    def _parse_json_safe(self, text: str) -> Dict[str, str]:
        """Ensures output is always a valid JSON matching the schema."""
        try:
            data = json.loads(text)
            return {
                "diagnostic_squelettique": data.get("diagnostic_squelettique", "Analyse squelettique non générée."),
                "analyse_dentaire": data.get("analyse_dentaire", "Analyse dentaire non générée."),
                "strategie_therapeutique": data.get("strategie_therapeutique", "Stratégie non générée.")
            }
        except json.JSONDecodeError:
            logger.error("AI Advisor: LLM response JSON parsing failure.")
            return {
                "diagnostic_squelettique": "Erreur de formatage IA.",
                "analyse_dentaire": "Erreur de formatage IA.",
                "strategie_therapeutique": "Veuillez vérifier les tracés manuellement."
            }

    def _heuristic_fallback(self, osseuse: schemas.SkeletalAnalysis, dentaire: schemas.DentalAnalysis, cohort: str) -> Dict[str, str]:
        """
        Deterministic expert rule engine for SLM failure.
        Generates a complete report based on COM (Modern Orthodontics Center) standards.
        Uses age-specific norms (9 years old vs Adult) according to the COM sheet.
        """
        # --- COM NORMS BY COHORT ---
        is_child = "Enfant" in cohort
        
        # A'B' Norms (Maxillo-mandibular discrepancy)
        # 9yo: +4.2 ± 3.2 | Adult: +2.3 ± 3.1
        NORM_AB_MEAN = 4.2 if is_child else 2.3
        NORM_AB_DEV = 3.2 if is_child else 3.1
        NORM_AB_MAX = NORM_AB_MEAN + NORM_AB_DEV  # Class II Upper threshold
        NORM_AB_MIN = NORM_AB_MEAN - NORM_AB_DEV  # Class III Lower threshold
        
        # Position A Norms (Maxilla)
        # 9yo: +2.8 ± 3.3 | Adult: +2.3 ± 3.0
        NORM_A_MEAN = 2.8 if is_child else 2.3
        NORM_A_DEV = 3.3 if is_child else 3.0
        
        # Position B Norms (Mandible)
        # 9yo: -1.5 ± 4.5 | Adult: 0.0 ± 4.9
        NORM_B_MEAN = -1.5 if is_child else 0.0
        NORM_B_DEV = 4.5 if is_child else 4.9
        
        # --- SKELETAL ANALYSIS ---
        ab_data = osseuse.Decalage_A_B
        tweed_data = osseuse.Angle_de_Tweed
        sit_a_data = osseuse.Situation_A
        sit_b_data = osseuse.Situation_B
        
        ab_status = ab_data.status
        ab_value = ab_data.valeur if ab_data.valeur is not None else NORM_AB_MEAN
        tweed_status = tweed_data.status
        tweed_value = tweed_data.valeur if tweed_data.valeur is not None else 26
        sit_a_value = sit_a_data.valeur if sit_a_data.valeur is not None else NORM_A_MEAN
        sit_b_value = sit_b_data.valeur if sit_b_data.valeur is not None else NORM_B_MEAN
        
        # Detailed skeletal diagnostic
        diag_os_parts = []
        
        # Sagittal classification with age-specific thresholds
        # Class II: > norm + standard deviation | Class III: < norm - standard deviation
        if ab_status == "High":
            severe_cl2 = NORM_AB_MEAN + 2 * NORM_AB_DEV  # +2 SD
            if ab_value and ab_value > severe_cl2:
                diag_os_parts.append(f"Structure de Classe II sévère (A-B = {ab_value} mm, >{severe_cl2:.1f}).")
            else:
                diag_os_parts.append(f"Structure de Classe II modérée (A-B = {ab_value} mm, norme: {NORM_AB_MEAN}±{NORM_AB_DEV}).")
        elif ab_status == "Low":
            severe_cl3 = NORM_AB_MEAN - 2 * NORM_AB_DEV  # -2 SD
            if ab_value and ab_value < severe_cl3:
                diag_os_parts.append(f"Structure de Classe III sévère (A-B = {ab_value} mm, <{severe_cl3:.1f}).")
            else:
                diag_os_parts.append(f"Structure de Classe III modérée (A-B = {ab_value} mm, norme: {NORM_AB_MEAN}±{NORM_AB_DEV}).")
        else:
            diag_os_parts.append(f"Structure de Classe I normosquelettique (A-B = {ab_value} mm).")
        
        # Base positions with numerical values (age-specific norms)
        sit_a_seuil_sup = NORM_A_MEAN + NORM_A_DEV
        sit_a_seuil_inf = NORM_A_MEAN - NORM_A_DEV
        sit_b_seuil_sup = NORM_B_MEAN + NORM_B_DEV
        sit_b_seuil_inf = NORM_B_MEAN - NORM_B_DEV
        
        if sit_a_value > sit_a_seuil_sup:
            diag_os_parts.append(f"Maxillaire prognathique (A à {sit_a_value} mm > {sit_a_seuil_sup:.1f}).")
        elif sit_a_value < sit_a_seuil_inf:
            diag_os_parts.append(f"Maxillaire rétrognathique (A à {sit_a_value} mm < {sit_a_seuil_inf:.1f}).")
        
        if sit_b_value > sit_b_seuil_sup:
            diag_os_parts.append(f"Mandibule prognathique (B à {sit_b_value} mm > {sit_b_seuil_sup:.1f}).")
        elif sit_b_value < sit_b_seuil_inf:
            diag_os_parts.append(f"Mandibule rétrognathique (B à {sit_b_value} mm < {sit_b_seuil_inf:.1f}).")
        
        # Vertical type
        if tweed_status == "High":
            diag_os_parts.append(f"Typologie hyperdivergente (Tweed = {tweed_value}°) - face longue avec risque d'ouverture.")
        elif tweed_status == "Low":
            diag_os_parts.append(f"Typologie hypodivergente (Tweed = {tweed_value}°) - face courte avec risque de surplomb.")
        else:
            diag_os_parts.append(f"Équilibre vertical normodivergent (Tweed = {tweed_value}°).")
        
        diag_os = " ".join(diag_os_parts)
        
        # --- DENTAL ANALYSIS ---
        impa_data = dentaire.IMPA
        if_data = dentaire.I_Francfort
        inter_data = dentaire.Inter_Incisif
        surplomb_data = dentaire.Surplomb
        recouv_data = dentaire.Recouvrement
        
        impa_status = impa_data.status
        impa_value = impa_data.valeur if impa_data.valeur is not None else 90
        if_status = if_data.status
        if_value = if_data.valeur if if_data.valeur is not None else 107
        
        diag_dent_parts = []
        
        # Soft tissue Aesthetic analysis
        esthetique = getattr(metrics, "analyse_esthetique", None)
        if esthetique:
            e_ls = esthetique.Ligne_E_Ls
            e_li = esthetique.Ligne_E_Li
            if e_ls.status != "Normoposition":
                diag_dent_parts.append(f"Profil : {e_ls.interpretation} ({e_ls.valeur:.1f} mm vs -4mm).")
            if e_li.status != "Normoposition":
                diag_dent_parts.append(f"{e_li.interpretation} ({e_li.valeur:.1f} mm vs -2mm).")
        
        # IMPA Analysis
        if impa_status == "High":
            diag_dent_parts.append(f"Proalvéolie mandibulaire (IMPA = {impa_value}°) - incisive inférieure vestibuloversée.")
        elif impa_status == "Low":
            diag_dent_parts.append(f"Rétroalvéolie mandibulaire (IMPA = {impa_value}°) - incisive inférieure linguoversée.")
        else:
            diag_dent_parts.append(f"Normoalvéolie mandibulaire (IMPA = {impa_value}°).")
        
        # I/Francfort Analysis
        if if_status == "High":
            diag_dent_parts.append(f"Proalvéolie maxillaire (I/F = {if_value}°).")
        elif if_status == "Low":
            diag_dent_parts.append(f"Rétroalvéolie maxillaire (I/F = {if_value}°).")
        
        # Compensations
        if impa_data.plage_compensation and impa_status == "Compensated":
            diag_dent_parts.append("Compensation dento-alvéolaire physiologique détectée.")
        
        # Overjet/Overbite
        if surplomb_data.valeur and surplomb_data.valeur > 3:
            diag_dent_parts.append("Surplomb (overjet) augmenté.")
        if recouv_data.valeur and recouv_data.valeur > 3:
            diag_dent_parts.append("Supraclusion (deep bite).")
        
        diag_dent = " ".join(diag_dent_parts) if diag_dent_parts else "Dentition en normoalvéolie avec bon rapport incisif."
        
        # --- THERAPEUTIC STRATEGY (AGE-ADAPTED) ---
        strat_parts = []
        
        # Severity thresholds by age
        SEVERE_CL2_THRESHOLD = 7.4 if is_child else 8.0  # Adult > 8mm, Child > 7.4mm
        SEVERE_CL3_THRESHOLD = -6.0 if is_child else -4.9  # Child <-6mm, Adult <-4.9mm
        
        # Main goals
        strat_parts.append("OBJECTIFS COM :")
        
        # Age context for the plan
        if is_child:
            strat_parts.append(f"Patient pédiatrique ({age} ans) - Croissance modulable.")
        else:
            strat_parts.append("Patient adulte - Approche compensatoire ou chirurgicale.")
        
        # By Class
        if ab_status == "High":
            if is_child:
                strat_parts.append("1. Correction orthopédique de la Classe II par propulsion mandibulaire")
                strat_parts.append("   (Herbst, Forsus, élastiques Classe II ou appareil amovible)")
                if ab_value and ab_value > SEVERE_CL2_THRESHOLD:
                    strat_parts.append("2. Vigilance sur le décalage sévère - contôle fréquent")
                else:
                    strat_parts.append("2. Contrôle de la croissance verticale (ancrage mini-vis si hyperdivergent)")
            else:
                if ab_value and ab_value > SEVERE_CL2_THRESHOLD:
                    strat_parts.append("1. Approche combinée ortho-chirurgicale à discuter (BSSO avancement mandibulaire)")
                else:
                    strat_parts.append("1. Compensation orthodontique avec extractions 14/24 ou 15/25 si encombrement sévère")
                strat_parts.append("2. Levée des compensations dentaires (redressement incisif mandibulaire)")
        elif ab_status == "Low":
            if is_child:
                strat_parts.append("1. Maintien de la Classe III fonctionnelle avec suivi de croissance")
                if ab_value and ab_value < SEVERE_CL3_THRESHOLD:
                    strat_parts.append("2. Décalage sévère - masque facial ou chirurgie différée à l'adolescence")
            else:
                strat_parts.append("1. Maintien de la Classe III si fonctionnel acceptable")
                strat_parts.append("2. Ou chirurgie d'avancée maxillaire selon souhait esthétique")
        else:
            strat_parts.append("1. Conservation de la Classe I")
        
        # By vertical type
        if tweed_status == "High":
            strat_parts.append("3. Contrôle vertical strict (ancrage squelettique, pas d'extractions en maxillaire)")
        elif tweed_status == "Low":
            strat_parts.append("3. Extractions possibles pour favoriser l'ouverture")
        
        # By alveolie
        if impa_status == "High":
            strat_parts.append("4. Rétroclinaison incisive mandibulaire (à discuter selon profil)")
        elif impa_status == "Low":
            strat_parts.append("4. Proclinaison incisive mandibulaire pour gagner de l'espace")
        
        # Age-adapted means
        strat_parts.append("")
        strat_parts.append("MOYENS :")
        
        if is_child:
            strat_parts.append("- Appareillage amovible (Turbogrow, Thurow) ou fixe précoce selon coopération")
            strat_parts.append("- Traitement en 2 temps possible (fonctionnel puis fixe)")
            strat_parts.append("- Surveillance du pic de croissance pubertaire (CVM)")
        else:
            strat_parts.append("- Multibrackets auto-ligaturants ou conventionnels")
        
        if tweed_status == "High":
            if is_child:
                strat_parts.append("- Ancrage extra-dentaire (masque facial) ou mini-vis si coopération")
            else:
                strat_parts.append("- Mini-vis d'ancrage (2 à 4) pour contrôle vertical strict")
        
        # Aesthetic Objective
        if esthetique:
            if esthetique.Ligne_E_Ls.status != "Normoposition" or esthetique.Ligne_E_Li.status != "Normoposition":
                strat_parts.append("")
                strat_parts.append("OBJECTIF ESTHÉTIQUE :")
                if esthetique.Ligne_E_Ls.status == "High" or esthetique.Ligne_E_Li.status == "High":
                    strat_parts.append("- Recul labial par ingression et rétroclinaison incisive pour harmoniser le profil.")
                elif esthetique.Ligne_E_Ls.status == "Low":
                    strat_parts.append("- Soutien labial par version vestibulaire contrôlée.")

        strat = "\n".join(strat_parts)
        
        # Prepare elite diagnostic even in fallback mode
        return {
            "diagnostic_squelettique": diag_os,
            "analyse_dentaire": diag_dent,
            "strategie_therapeutique": strat,
            "is_fallback": True # UI marker
        }

    def generate_prescription(self, acte: str, age: int = 30) -> list:
        """Generates a medical protocol via local SLM."""
        prompt = f"""
        Tu es un chirurgien-dentiste. Génère une ordonnance standard pour l'acte suivant : "{acte}". Le patient a {age} ans.
        Règles :
        - Renvoie UNIQUEMENT un tableau JSON valide.
        - Format exigé : [{{"nom": "Médicament", "dosage": "Dose", "forme": "Comprimés/Sachets", "posologie": "Instructions"}}]
        - Ne mets AUCUN texte avant ou après le JSON.
        """
        try:
            response = requests.post(
                self.llm_endpoint,
                json={"model": self.model_name, "prompt": prompt, "format": "json", "stream": False, "options": {"temperature": 0.1}},
                timeout=5.0
            )
            response.raise_for_status()
            return json.loads(response.json().get("response", "[]"))
        except Exception as e:
            logger.error(f"AI Advisor Prescription Error: {e}")
            return [] # Empty fallback, doctor will fill manually

# Backend singleton instance
ai_advisor = AIAdvisor()