import logging
from typing import Dict, Any, Optional
from backend import schemas

logger = logging.getLogger(__name__)

class BilanOrthoEngine:
    """
    Moteur Déterministe pour le Bilan Orthodontique (Local First, Sans LLM).
    Fusionne les données céphalométriques (CephaloAnalysisResult) et cliniques (ClinicalData)
    pour générer une synthèse médicale d'une précision chirurgicale.
    """

    def generate_bilan(self, cephalo: schemas.CephaloAnalysisResult, clinique: schemas.ClinicalData) -> Dict[str, str]:
        resume_cephalo = self._generate_resume_cephalo(cephalo)
        resume_moulages = self._generate_resume_moulages(clinique)
        resume_diagnostic = self._generate_synthese_diagnostique(cephalo, clinique)
        plan_traitement = self._generate_plan_traitement(cephalo, clinique)

        return {
            "diagnostic_squelettique": resume_cephalo,
            "analyse_moulages": resume_moulages,
            "synthese_diagnostique": resume_diagnostic,
            "strategie_therapeutique": plan_traitement,
            "is_fallback": False # Déterministe natif
        }

    def _generate_resume_cephalo(self, cephalo: schemas.CephaloAnalysisResult) -> str:
        # Reprise du diagnostic squelettique et dentaire déterministe
        narrative = cephalo.ai_narrative or {}
        diag_sq = narrative.get("diagnostic_squelettique", "")
        diag_dent = narrative.get("analyse_dentaire", "")
        
        # S'il manque, on le reconstruit très succinctement
        if not diag_sq:
            ab = cephalo.metrics.analyse_osseuse.Decalage_A_B.valeur or 0
            if ab > 6: classe_sq = "Classe II"
            elif ab < 1: classe_sq = "Classe III"
            else: classe_sq = "Classe I"
            
            tweed = cephalo.metrics.analyse_osseuse.Angle_de_Tweed.valeur or 26
            if tweed > 30: div = "hyperdivergente"
            elif tweed < 22: div = "hypodivergente"
            else: div = "normodivergente"
            
            diag_sq = f"Base squelettique de {classe_sq} (A'B' = {ab} mm). Typologie faciale {div} (Tweed = {tweed}°)."

        if not diag_dent:
            impa = cephalo.metrics.analyse_dentaire.IMPA.valeur or 90
            diag_dent = f"Position incisive mandibulaire : IMPA = {impa}°."

        return f"{diag_sq} {diag_dent}".strip()

    def _generate_resume_moulages(self, clinique: schemas.ClinicalData) -> str:
        parts = []
        
        # 1. Rapports d'occlusion (Classes d'Angle)
        classes = []
        if clinique.classe_molaire_droite: classes.append(f"Molaire Droite: Cl {clinique.classe_molaire_droite}")
        if clinique.classe_molaire_gauche: classes.append(f"Molaire Gauche: Cl {clinique.classe_molaire_gauche}")
        if clinique.classe_canine_droite: classes.append(f"Canine Droite: Cl {clinique.classe_canine_droite}")
        if clinique.classe_canine_gauche: classes.append(f"Canine Gauche: Cl {clinique.classe_canine_gauche}")
        
        if classes:
            parts.append("Rapports d'Occlusion: " + " | ".join(classes) + ".")
            
            # Subdivision
            mg = clinique.classe_molaire_gauche
            md = clinique.classe_molaire_droite
            if mg and md and mg != md:
                parts.append("Asymétrie de classe molaire (Subdivision) détectée.")
        
        # 2. DDM Clinique
        if clinique.ddm_reelle is not None:
            val = clinique.ddm_reelle
            sev = "Légère"
            if val < -6: sev = "Sévère"
            elif val < -3: sev = "Modérée"
            elif val > 0: sev = "Excès d'espace (Diastèmes)"
            
            if val < 0:
                parts.append(f"Dysharmonie Dento-Maxillaire (DDM) Réelle: Encombrement {sev} ({val} mm).")
            else:
                parts.append(f"Dysharmonie Dento-Maxillaire (DDM) Réelle: {sev} (+{val} mm).")
                
        if not parts:
            return "Aucune donnée de moulages fournie."
            
        return " ".join(parts)

    def _generate_synthese_diagnostique(self, cephalo: schemas.CephaloAnalysisResult, clinique: schemas.ClinicalData) -> str:
        # Croisement intelligent Radio / Clinique
        ab = cephalo.metrics.analyse_osseuse.Decalage_A_B.valeur or 0
        ddm = clinique.ddm_reelle or 0
        impa = cephalo.metrics.analyse_dentaire.IMPA.valeur or 90
        
        synthese = []
        
        # Association Squelettique / Dentaire
        if ab > 6:
            synthese.append("La Classe II squelettique est le problème majeur.")
            if ddm < -4:
                synthese.append("Elle est aggravée par un encombrement dentaire limitant la compensation.")
            if impa > 95:
                synthese.append("Notez une forte proalvéolie mandibulaire (compensation physiologique à corriger prudemment).")
        elif ab < 1:
            synthese.append("Tendance Classe III squelettique.")
            if impa < 85:
                synthese.append("L'incisive inférieure est linguoversée (compensation).")
        else:
            synthese.append("Bases osseuses équilibrées (Classe I).")
            if ddm < -5:
                synthese.append("L'encombrement dentaire (DDM) constitue le défi thérapeutique principal.")
                
        return " ".join(synthese)

    def _generate_plan_traitement(self, cephalo: schemas.CephaloAnalysisResult, clinique: schemas.ClinicalData) -> str:
        """
        Arbre Décisionnel Expert (Elite v5.0).
        Intègre la denture, le stade CVM et la philosophie de traitement.
        """
        # Priorité à la saisie manuelle si elle est déjà substantielle
        if clinique.plan_traitement and len(clinique.plan_traitement) > 50:
            return clinique.plan_traitement
            
        cvm = clinique.cvm or "CS3"
        ab = cephalo.metrics.analyse_osseuse.Decalage_A_B.valeur or 4.0
        tweed = cephalo.metrics.analyse_osseuse.Angle_de_Tweed.valeur or 26
        ddm = clinique.ddm_reelle or 0
        denture = clinique.denture_type or "PERMANENTE"
        tech = clinique.preference_technique or "DAMON"
        
        is_interceptive = denture in ["TEMPORAIRE", "MIXTE"] or cvm in ["CS1", "CS2"]
        plan = []

        # --- 1. ORIENTATION STRATÉGIQUE ---
        plan.append(f"### 🎯 ORIENTATION : {'TRAITEMENT INTERCEPTIF' if is_interceptive else 'TRAITEMENT GLOBAL'}")
        
        if is_interceptive:
            plan.append(f"Patient en denture {denture.lower()}. Objectif : Correction squelettique et préparation d'arcade.")
        else:
            plan.append(f"Patient en denture permanente. Objectif : Alignement, nivellement et coordination occlusale.")

        # --- 2. PHASE SQUELETTIQUE (Orthopédie / Chirurgie) ---
        if ab > 7: # Classe II marquée
            if is_interceptive:
                plan.append("- **Orthopédie** : Correction fonctionnelle de la Classe II (Twin Block ou Activateur) pour stimuler la croissance mandibulaire.")
            else:
                plan.append("- **Orthodontie** : Camouflage par recul en masse (mini-vis) ou chirurgie orthognathique (BSSO) si le décalage est trop sévère.")
        elif ab < 1: # Classe III
            if cvm in ["CS1", "CS2"]:
                plan.append("- **Orthopédie** : Traction maxillaire précoce via Masque de Delaire et disjonction palatine.")
            else:
                plan.append("- **Compromis/Chirurgie** : Risque de compensation incisive. Chirurgie Le Fort I à envisager en fin de croissance.")

        # --- 3. GESTION DE L'ESPACE & TECHNIQUE ---
        if tech == "DAMON":
            plan.append(f"- **Mécanique Passive (Système Damon)** : Expansion physiologique privilégiée. Utilisation de forces légères pour limiter les extractions malgré une DDM de {ddm} mm.")
            if ddm < -7:
                plan.append("  *Note : Surveillance étroite de l'ancrage. Extractions à réévaluer après alignement.*")
        elif tech == "ALIGNEURS":
            plan.append("- **Système d'Aligneurs (Invisalign)** : Séquençage précis des mouvements. Prévoir stripping (IPR) pour résoudre l'encombrement.")
        else:
            plan.append("- **Multi-attaches Conventionnel** : Alignement standard avec contrôle strict de l'ancrage.")

        # --- 4. FEUILLE DE ROUTE CLINIQUE (Roadmap) ---
        plan.append("\n### 🛤️ ÉTAPES DU TRAITEMENT :")
        plan.append("1. **Phase d'Alignement** : Arcs de section ronde (Copper NiTi) pour la résolution de l'encombrement.")
        plan.append("2. **Phase de Nivellement** : Arcs rectangulaires pour le contrôle du torque et de l'inclinaison.")
        plan.append("3. **Phase de Coordination** : Élastiques inter-maxillaires pour caler l'occlusion (Classe I).")
        plan.append("4. **Finition & Contention** : Détails de l'esthétique du sourire et pose d'une contention fixe/amovible.")

        return "\n".join(plan)

bilan_ortho_engine = BilanOrthoEngine()
