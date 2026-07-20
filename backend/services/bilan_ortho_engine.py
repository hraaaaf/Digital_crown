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
        narrative = cephalo.ai_narrative or {}
        diag_sq = narrative.get("diagnostic_squelettique", "")
        diag_dent = narrative.get("analyse_dentaire", "")

        if not diag_sq or len(diag_sq) < 20:
            ab = cephalo.metrics.analyse_osseuse.Decalage_A_B.valeur
            anb = cephalo.metrics.analyse_osseuse.ANB.valeur
            tweed = cephalo.metrics.analyse_osseuse.Angle_de_Tweed.valeur
            parts = []
            cl = None
            if (anb is not None and anb > 4.5) or (ab is not None and ab > 5.4):
                cl = "II"
            elif (anb is not None and anb < 0) or (ab is not None and ab < -0.8):
                cl = "III"
            elif anb is not None or ab is not None:
                cl = "I"
            if cl is not None:
                parts.append(f"Base squelettique de Classe {cl}.")
            if tweed is not None:
                div = "normodivergente"
                if tweed > 30:
                    div = "hyperdivergente"
                elif tweed < 22:
                    div = "hypodivergente"
                parts.append(f"Typologie faciale {div} (Tweed = {tweed}\u00b0).")
            diag_sq = " ".join(parts)

        if not diag_dent:
            impa = cephalo.metrics.analyse_dentaire.IMPA.valeur
            if impa is not None:
                diag_dent = f"Position incisive mandibulaire : IMPA = {impa}\u00b0."

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
        ab = cephalo.metrics.analyse_osseuse.Decalage_A_B.valeur
        anb = cephalo.metrics.analyse_osseuse.ANB.valeur
        ddm = clinique.ddm_reelle
        impa = cephalo.metrics.analyse_dentaire.IMPA.valeur
        synthese = []
        is_cl2 = (anb is not None and anb > 4.5) or (ab is not None and ab > 5.4)
        is_cl3 = (anb is not None and anb < 0) or (ab is not None and ab < -0.8)
        if is_cl2:
            synthese.append("La Classe II squelettique est le probl\u00e8me sagittal majeur.")
            if ddm is not None and ddm < -4:
                synthese.append("Elle est aggrav\u00e9e par un encombrement dentaire limitant les compensations.")
            if impa is not None and impa > 95:
                synthese.append("Notez une forte proalv\u00e9olie mandibulaire (compensation physiologique \u00e0 g\u00e9rer).")
        elif is_cl3:
            synthese.append("Probl\u00e9matique de Classe III squelettique identifi\u00e9e.")
            if impa is not None and impa < 85:
                synthese.append("L'incisive inf\u00e9rieure est linguovers\u00e9e en tentative de compensation naturelle.")
        elif anb is not None or ab is not None:
            synthese.append("Bases osseuses \u00e9quilibr\u00e9es sagittalement (Classe I).")
            if ddm is not None and ddm < -5:
                synthese.append("L'encombrement dentaire (DDM) constitue le d\u00e9fi th\u00e9rapeutique principal.")
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
        ab = cephalo.metrics.analyse_osseuse.Decalage_A_B.valeur
        tweed = cephalo.metrics.analyse_osseuse.Angle_de_Tweed.valeur
        ddm = clinique.ddm_reelle
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
        if ab is not None and ab > 7: # Classe II marquée
            if is_interceptive:
                plan.append("- **Orthopédie** : Correction fonctionnelle de la Classe II (Twin Block ou Activateur) pour stimuler la croissance mandibulaire.")
            else:
                plan.append("- **Orthodontie** : Camouflage par recul en masse (mini-vis) ou chirurgie orthognathique (BSSO) si le décalage est trop sévère.")
        elif ab is not None and ab < 1: # Classe III
            if cvm in ["CS1", "CS2"]:
                plan.append("- **Orthopédie** : Traction maxillaire précoce via Masque de Delaire et disjonction palatine.")
            else:
                plan.append("- **Compromis/Chirurgie** : Risque de compensation incisive. Chirurgie Le Fort I à envisager en fin de croissance.")

        # --- 3. GESTION DE L'ESPACE & TECHNIQUE ---
        if tech == "DAMON":
            mechanical_text = "- **M\u00e9canique Passive (Syst\u00e8me Damon)** : Expansion physiologique privil\u00e9gi\u00e9e. Utilisation de forces l\u00e9g\u00e8res pour limiter les extractions."
            if ddm is not None:
                mechanical_text = f"- **M\u00e9canique Passive (Syst\u00e8me Damon)** : Expansion physiologique privil\u00e9gi\u00e9e. Utilisation de forces l\u00e9g\u00e8res pour limiter les extractions malgr\u00e9 une DDM de {ddm} mm."
            plan.append(mechanical_text)
            if ddm is not None and ddm < -7:
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
