import logging
import json
import requests
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

class AIAdvisor:
    """
    Service d'Intelligence Clinique (SLM).
    Interface le Moteur Géométrique avec un LLM local (Llama-3/Mistral) pour la synthèse COM et la Pharmacologie.
    Produit exclusivement des diagnostics structurés (Structured JSON Output).
    """
    
    def __init__(self, llm_endpoint: str = "http://localhost:11434/api/generate"):
        self.llm_endpoint = llm_endpoint
        self.model_name = "llama3.2" 
        
        # Ingénierie du Prompt - Verrouillage du Rôle et de la Sortie
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

    def generate_diagnostic(self, metrics: Dict, age: Optional[int] = None, cvm_stage: Optional[str] = None, use_slm: bool = False) -> Dict[str, str]:
        """
        Ingère le dictionnaire de métriques et génère le diagnostic.
        
        Mode par défaut (use_slm=False): utilise le moteur heuristique expert (rapide, déterministe, normes COM).
        Mode SLM (use_slm=True): tente d'appeler Ollama avec timeout court (3s), fallback heuristique si échec.
        
        RECOMMANDATION: Laisser use_slm=False pour la production. Le SLM (llama3.2) peut générer des erreurs cliniques.
        """
        # 1. Préparation du contexte patient
        patient_context = f"Âge: {age if age else 'Adulte'}. "
        if cvm_stage:
            patient_context += f"Stade de maturation osseuse (CVM): {cvm_stage}."

        # 2. Filtrage intelligent : Isolation des données pertinentes (Z-score élevé ou Compensations)
        clinical_data = {
            "Contexte": patient_context,
            "Deviations_Severes_Ou_Compensees": {}
        }
        
        osseuse = metrics.get("analyse_osseuse", {})
        dentaire = metrics.get("analyse_dentaire", {})
        
        for category, measures in [("Squelettique", osseuse), ("Dentaire", dentaire)]:
            for name, data in measures.items():
                if data.get("z_score", 0) >= 1.0 or data.get("status") in ["High", "Low", "Compensated"]:
                    clinical_data["Deviations_Severes_Ou_Compensees"][name] = {
                        "Valeur": data.get("value"),
                        "Norme": f"[{data.get('norm_min')} - {data.get('norm_max')}]",
                        "Statut": data.get("status"),
                        "Interprétation_Moteur": data.get("interpretation")
                    }

        # Mode par défaut: heuristique expert (rapide, fiable, normes COM)
        if not use_slm:
            logger.info("AI Advisor: Mode heuristique actif (normes COM âge-spécifiques)")
            return self._heuristic_fallback(osseuse, dentaire, age)
        
        # Mode SLM: tentative avec timeout court (3s), fallback si échec
        prompt = f"Analyse ces données cliniques et génère le JSON attendu :\n{json.dumps(clinical_data, ensure_ascii=False, indent=2)}"
        
        try:
            logger.info("AI Advisor: Tentative SLM (timeout 3s)...")
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
                timeout=3.0  # Timeout court pour ne pas bloquer l'UI
            )
            response.raise_for_status()
            
            raw_text = response.json().get("response", "{}")
            parsed = self._parse_json_safe(raw_text)
            
            # Vérification de cohérence minimale
            if parsed.get("diagnostic_squelettique") and len(parsed["diagnostic_squelettique"]) > 20:
                logger.info("AI Advisor: SLM a répondu correctement")
                return parsed
            else:
                logger.warning("AI Advisor: SLM réponse invalide, fallback heuristique")
                return self._heuristic_fallback(osseuse, dentaire, age)

        except requests.exceptions.Timeout:
            logger.warning("AI Advisor: SLM timeout (3s), fallback heuristique")
            return self._heuristic_fallback(osseuse, dentaire, age)
        except requests.exceptions.ConnectionError:
            logger.warning("AI Advisor: SLM non disponible (Ollama éteint?), fallback heuristique")
            return self._heuristic_fallback(osseuse, dentaire, age)
        except Exception as e:
            logger.warning(f"AI Advisor: Erreur SLM ({e}), fallback heuristique")
            return self._heuristic_fallback(osseuse, dentaire, age)

    def _parse_json_safe(self, text: str) -> Dict[str, str]:
        """Garantit que la sortie est toujours un JSON valide conforme au schéma."""
        try:
            data = json.loads(text)
            return {
                "diagnostic_squelettique": data.get("diagnostic_squelettique", "Analyse squelettique non générée."),
                "analyse_dentaire": data.get("analyse_dentaire", "Analyse dentaire non générée."),
                "strategie_therapeutique": data.get("strategie_therapeutique", "Stratégie non générée.")
            }
        except json.JSONDecodeError:
            logger.error("AI Advisor : Échec du parsing JSON de la réponse LLM.")
            return {
                "diagnostic_squelettique": "Erreur de formatage IA.",
                "analyse_dentaire": "Erreur de formatage IA.",
                "strategie_therapeutique": "Veuillez vérifier les tracés manuellement."
            }

    def _heuristic_fallback(self, osseuse: Dict, dentaire: Dict, age: Optional[int]) -> Dict[str, str]:
        """
        Moteur de règles déterministe expert en cas de panne du SLM.
        Génère un bilan complet basé sur les normes COM (Centre d'Orthodontie Moderne).
        Utilise les normes âge-spécifiques (9 ans vs Adulte) selon la fiche COM.
        """
        # --- NORMES COM SELON L'ÂGE (d'après la fiche COM) ---
        is_child = age is not None and age <= 12
        
        # Normes A'B' (Décalage maxillo-mandibulaire)
        # 9 ans: +4.2 ± 3.2 | Adulte: +2.3 ± 3.1
        NORM_AB_MEAN = 4.2 if is_child else 2.3
        NORM_AB_DEV = 3.2 if is_child else 3.1
        NORM_AB_MAX = NORM_AB_MEAN + NORM_AB_DEV  # Seuil supérieur Classe II
        NORM_AB_MIN = NORM_AB_MEAN - NORM_AB_DEV  # Seuil inférieur Classe III
        
        # Normes Situation A (Maxillaire)
        # 9 ans: +2.8 ± 3.3 | Adulte: +2.3 ± 3.0
        NORM_A_MEAN = 2.8 if is_child else 2.3
        NORM_A_DEV = 3.3 if is_child else 3.0
        
        # Normes Situation B (Mandibule)
        # 9 ans: -1.5 ± 4.5 | Adulte: 0.0 ± 4.9
        NORM_B_MEAN = -1.5 if is_child else 0.0
        NORM_B_DEV = 4.5 if is_child else 4.9
        
        # --- ANALYSE SQUELETTIQUE ---
        ab_data = osseuse.get("Decalage_A_B", {})
        tweed_data = osseuse.get("Angle_de_Tweed", {})
        sit_a_data = osseuse.get("Situation_A", {})
        sit_b_data = osseuse.get("Situation_B", {})
        
        ab_status = ab_data.get("status", "Normal")
        ab_value = ab_data.get("value", NORM_AB_MEAN)
        tweed_status = tweed_data.get("status", "Normal")
        tweed_value = tweed_data.get("value", 26)
        sit_a_value = sit_a_data.get("value", NORM_A_MEAN)
        sit_b_value = sit_b_data.get("value", NORM_B_MEAN)
        
        # Diagnostic squelettique détaillé
        diag_os_parts = []
        
        # Classification sagittale avec seuils âge-spécifiques
        # Classe II: > norme + écart-type | Classe III: < norme - écart-type
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
        
        # Position des bases avec valeurs numériques (normes âge-spécifiques)
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
        
        # Type vertical
        if tweed_status == "High":
            diag_os_parts.append(f"Typologie hyperdivergente (Tweed = {tweed_value}°) - face longue avec risque d'ouverture.")
        elif tweed_status == "Low":
            diag_os_parts.append(f"Typologie hypodivergente (Tweed = {tweed_value}°) - face courte avec risque de surplomb.")
        else:
            diag_os_parts.append(f"Équilibre vertical normodivergent (Tweed = {tweed_value}°).")
        
        diag_os = " ".join(diag_os_parts)
        
        # --- ANALYSE DENTAIRE ---
        impa_data = dentaire.get("IMPA", {})
        if_data = dentaire.get("I_Francfort", {})
        inter_data = dentaire.get("Inter_Incisif", {})
        surplomb_data = dentaire.get("Surplomb", {})
        recouv_data = dentaire.get("Recouvrement", {})
        
        impa_status = impa_data.get("status", "Normal")
        impa_value = impa_data.get("value", 90)
        if_status = if_data.get("status", "Normal")
        if_value = if_data.get("value", 107)
        
        diag_dent_parts = []
        
        # Analyse IMPA
        if impa_status == "High":
            diag_dent_parts.append(f"Proalvéolie mandibulaire (IMPA = {impa_value}°) - incisive inférieure vestibuloversée.")
        elif impa_status == "Low":
            diag_dent_parts.append(f"Rétroalvéolie mandibulaire (IMPA = {impa_value}°) - incisive inférieure linguoversée.")
        else:
            diag_dent_parts.append(f"Normoalvéolie mandibulaire (IMPA = {impa_value}°).")
        
        # Analyse I/Francfort
        if if_status == "High":
            diag_dent_parts.append(f"Proalvéolie maxillaire (I/F = {if_value}°).")
        elif if_status == "Low":
            diag_dent_parts.append(f"Rétroalvéolie maxillaire (I/F = {if_value}°).")
        
        # Compensations
        if impa_data.get("plage_compensation") and impa_status == "Compensated":
            diag_dent_parts.append("Compensation dento-alvéolaire physiologique détectée.")
        
        # Surplomb/Recouvrement
        if surplomb_data.get("value") and surplomb_data.get("value", 0) > 3:
            diag_dent_parts.append("Surplomb (overjet) augmenté.")
        if recouv_data.get("value") and recouv_data.get("value", 0) > 3:
            diag_dent_parts.append("Supraclusion (deep bite).")
        
        diag_dent = " ".join(diag_dent_parts) if diag_dent_parts else "Dentition en normoalvéolie avec bon rapport incisif."
        
        # --- STRATÉGIE THÉRAPEUTIQUE (ADAPTÉE À L'ÂGE) ---
        strat_parts = []
        
        # Seuils sévérité selon âge
        SEVERE_CL2_THRESHOLD = 7.4 if is_child else 8.0  # Adulte > 8mm, Enfant > 7.4mm
        SEVERE_CL3_THRESHOLD = -6.0 if is_child else -4.9  # Enfant <-6mm, Adulte <-4.9mm
        
        # Objectifs principaux
        strat_parts.append("OBJECTIFS COM :")
        
        # Contexte âge pour le plan
        if is_child:
            strat_parts.append(f"Patient pédiatrique ({age} ans) - Croissance modulable.")
        else:
            strat_parts.append("Patient adulte - Approche compensatoire ou chirurgicale.")
        
        # Selon la classe
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
        
        # Selon le type vertical
        if tweed_status == "High":
            strat_parts.append("3. Contrôle vertical strict (ancrage squelettique, pas d'extractions en maxillaire)")
        elif tweed_status == "Low":
            strat_parts.append("3. Extractions possibles pour favoriser l'ouverture")
        
        # Selon l'alvéolie
        if impa_status == "High":
            strat_parts.append("4. Rétroclinaison incisive mandibulaire (à discuter selon profil)")
        elif impa_status == "Low":
            strat_parts.append("4. Proclinaison incisive mandibulaire pour gagner de l'espace")
        
        # Moyens adaptés à l'âge
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
        
        # Durée adaptée à l'âge
        if is_child:
            strat_parts.append("- Durée estimée : 12-24 mois (selon phase de croissance)")
        else:
            strat_parts.append("- Durée estimée : 18-30 mois")
        
        strat = "\n".join(strat_parts)
        
        return {
            "diagnostic_squelettique": diag_os,
            "analyse_dentaire": diag_dent,
            "strategie_therapeutique": strat
        }

    def generate_prescription(self, acte: str, age: int = 30) -> list:
        """Génère un protocole médicamenteux via le SLM local."""
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
            logger.error(f"Erreur SLM Prescription: {e}")
            return [] # Fallback vide, le médecin remplira à la main

# Instance singleton pour le backend
ai_advisor = AIAdvisor()