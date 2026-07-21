import logging
from typing import Dict, Any, Optional
from backend import schemas
from backend.schemas.cephalo_normative import NormativeContext, Sex
from backend.services.cephalo_normative_service import evaluate_measurement, NormativeEvaluationStatus

logger = logging.getLogger(__name__)

# ANB skeletal-class label -> bare letter, matching the same convention used
# in cephalo_engine.py (CEPHALOMETRY-NORMATIVE-BACKEND-WIRING-STEINER-4A).
# Only these exact, already-migrated ClassificationRule label strings are
# recognized — an unrecognized future label must never silently drive
# treatment-strategy text.
_ANB_LABEL_TO_SKELETAL_CLASS = {"Classe I": "I", "Classe II": "II", "Classe III": "III"}

# Registry classification labels -> this file's own feminine-agreement bare
# words ("Typologie faciale {div}" — div agrees with "typologie", unlike
# cephalo_engine.py's masculine "Angle de Tweed: {div}") (CEPHALOMETRY-
# NORMATIVE-BACKEND-WIRING-TWEED-IMPA-FRANCFORT-4C).
_TWEED_LABEL_TO_DIV_FEMININE = {
    "Hyperdivergent": "hyperdivergente",
    "Hypodivergent": "hypodivergente",
    "Normodivergent": "normodivergente",
}

# Patient.sexe is stored as "M"/"F" — anything else maps to None, never
# guessed (CEPHALOMETRY-NORMATIVE-CONTEXT-PLUMBING-4A2).
_SEX_CODE_TO_ENUM = {"M": Sex.MALE, "F": Sex.FEMALE}


def _map_sex(sex_code: Optional[str]) -> Optional[Sex]:
    if sex_code is None:
        return None
    return _SEX_CODE_TO_ENUM.get(sex_code)


def _authoritative_label(
    measurement_id: str,
    value: Optional[float],
    age: Optional[int] = None,
    sex: Optional[str] = None,
) -> Optional[str]:
    """Returns a classification label only if the normative service
    considers it authoritative — None otherwise (no silent fallback to
    local legacy constants). Duplicated from cephalo_engine.py's identical
    helper rather than cross-imported, to keep the two engine modules
    independent as they already are. population_id stays None: no
    population-profile concept exists anywhere in Digital Crown today
    (documented limitation, not an omission).
    """
    if value is None:
        return None
    result = evaluate_measurement(
        measurement_id, value, "v1",
        NormativeContext(age=age, sex=_map_sex(sex), population_id=None),
    )
    if result.status == NormativeEvaluationStatus.VALIDATED_PROFILE_MATCH and result.classification:
        return result.classification
    return None


class BilanOrthoEngine:
    """
    Moteur Déterministe pour le Bilan Orthodontique (Local First, Sans LLM).
    Fusionne les données céphalométriques (CephaloAnalysisResult) et cliniques (ClinicalData)
    pour générer une synthèse médicale d'une précision chirurgicale.
    """

    def generate_bilan(
        self,
        cephalo: schemas.CephaloAnalysisResult,
        clinique: schemas.ClinicalData,
        age: Optional[int] = None,
        sex: Optional[str] = None,
    ) -> Dict[str, str]:
        resume_cephalo = self._generate_resume_cephalo(cephalo, age, sex)
        resume_moulages = self._generate_resume_moulages(clinique)
        resume_diagnostic = self._generate_synthese_diagnostique(cephalo, clinique, age, sex)
        plan_traitement = self._generate_plan_traitement(cephalo, clinique)

        return {
            "diagnostic_squelettique": resume_cephalo,
            "analyse_moulages": resume_moulages,
            "synthese_diagnostique": resume_diagnostic,
            "strategie_therapeutique": plan_traitement,
            "is_fallback": False # Déterministe natif
        }

    def _generate_resume_cephalo(self, cephalo: schemas.CephaloAnalysisResult, age: Optional[int] = None, sex: Optional[str] = None) -> str:
        narrative = cephalo.ai_narrative or {}
        diag_sq = narrative.get("diagnostic_squelettique", "")
        diag_dent = narrative.get("analyse_dentaire", "")

        if not diag_sq or len(diag_sq) < 20:
            anb = cephalo.metrics.analyse_osseuse.ANB.valeur
            tweed = cephalo.metrics.analyse_osseuse.Angle_de_Tweed.valeur
            parts = []
            # ANB no longer classifies locally (CEPHALOMETRY-NORMATIVE-BACKEND-WIRING-
            # STEINER-4A) — only an authoritative service classification may name a
            # skeletal class; the registry has no VALIDATED_FOR_PROFILE Steiner profile
            # today, so this stays a neutral, value-only note.
            anb_label = _authoritative_label("ANB", anb, age, sex)
            if anb_label is not None:
                parts.append(f"Base squelettique de {anb_label}.")
            elif anb is not None:
                parts.append(f"ANB = {anb}° (référence normative non validée).")
            # Tweed no longer classifies locally (CEPHALOMETRY-NORMATIVE-BACKEND-
            # WIRING-TWEED-IMPA-FRANCFORT-4C) \u2014 same non-authoritative pattern as ANB above.
            tweed_label = _authoritative_label("Angle_de_Tweed", tweed, age, sex)
            div = _TWEED_LABEL_TO_DIV_FEMININE.get(tweed_label) if tweed_label else None
            if tweed_label is not None:
                parts.append(f"Typologie faciale {div} (Tweed = {tweed}\u00b0).")
            elif tweed is not None:
                parts.append(f"Tweed = {tweed}\u00b0 (r\u00e9f\u00e9rence normative non valid\u00e9e).")
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

    def _generate_synthese_diagnostique(self, cephalo: schemas.CephaloAnalysisResult, clinique: schemas.ClinicalData, age: Optional[int] = None, sex: Optional[str] = None) -> str:
        anb = cephalo.metrics.analyse_osseuse.ANB.valeur
        ddm = clinique.ddm_reelle
        impa = cephalo.metrics.analyse_dentaire.IMPA.valeur
        synthese = []
        # ANB no longer classifies locally (CEPHALOMETRY-NORMATIVE-BACKEND-WIRING-
        # STEINER-4A) \u2014 this method's whole job is naming *the* sagittal problem, and
        # with no authoritative classification there is no class-specific sentence to
        # attach a note to, so it is omitted entirely rather than replaced (confirmed
        # design choice). Raw ANB stays visible via diagnostic_squelettique instead.
        anb_label = _authoritative_label("ANB", anb, age, sex)
        skeletal_class = _ANB_LABEL_TO_SKELETAL_CLASS.get(anb_label) if anb_label else None
        # IMPA no longer classifies locally (same 4C mission as Tweed above) \u2014
        # only fires when the service names it authoritatively.
        impa_label = _authoritative_label("IMPA", impa, age, sex)
        if skeletal_class == "II":
            synthese.append("La Classe II squelettique est le probl\u00e8me sagittal majeur.")
            if ddm is not None and ddm < -4:
                synthese.append("Elle est aggrav\u00e9e par un encombrement dentaire limitant les compensations.")
            if impa_label == "Proalveolie mandibulaire":
                synthese.append("Notez une forte proalv\u00e9olie mandibulaire (compensation physiologique \u00e0 g\u00e9rer).")
        elif skeletal_class == "III":
            synthese.append("Probl\u00e9matique de Classe III squelettique identifi\u00e9e.")
            if impa_label == "Retroalveolie mandibulaire":
                synthese.append("L'incisive inf\u00e9rieure est linguovers\u00e9e en tentative de compensation naturelle.")
        elif skeletal_class == "I":
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
