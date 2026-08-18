import logging
from typing import Dict, Any, Optional
from backend import schemas
from backend.schemas.cephalo_normative import NormativeContext, Sex
from backend.services.cephalo_normative_service import evaluate_measurement, NormativeEvaluationStatus

logger = logging.getLogger(__name__)

_ANB_LABEL_TO_SKELETAL_CLASS = {"Classe I": "I", "Classe II": "II", "Classe III": "III"}
_TWEED_LABEL_TO_DIV_FEMININE = {
    "Hyperdivergent": "hyperdivergente",
    "Hypodivergent": "hypodivergente",
    "Normodivergent": "normodivergente",
}
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
    """Moteur déterministe de synthèse orthodontique, sans décision thérapeutique autonome."""

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
        if clinique.plan_traitement and clinique.plan_traitement.strip():
            plan_traitement = clinique.plan_traitement.strip()
        else:
            plan_traitement = (
                "Aucune stratégie thérapeutique n'est générée automatiquement. "
                "Le plan de traitement relève exclusivement de la décision du praticien "
                "après validation clinique et radiographique."
            )

        return {
            "diagnostic_squelettique": resume_cephalo,
            "analyse_moulages": resume_moulages,
            "synthese_diagnostique": resume_diagnostic,
            "strategie_therapeutique": plan_traitement,
            "is_fallback": False
        }

    def _generate_resume_cephalo(self, cephalo: schemas.CephaloAnalysisResult, age: Optional[int] = None, sex: Optional[str] = None) -> str:
        narrative = cephalo.ai_narrative or {}
        diag_sq = narrative.get("diagnostic_squelettique", "")
        diag_dent = narrative.get("analyse_dentaire", "")

        if not diag_sq or len(diag_sq) < 20:
            anb = cephalo.metrics.analyse_osseuse.ANB.valeur
            tweed = cephalo.metrics.analyse_osseuse.Angle_de_Tweed.valeur
            parts = []
            anb_label = _authoritative_label("ANB", anb, age, sex)
            if anb_label is not None:
                parts.append(f"Base squelettique de {anb_label}.")
            elif anb is not None:
                parts.append(f"ANB = {anb}° (référence normative non validée).")
            tweed_label = _authoritative_label("Angle_de_Tweed", tweed, age, sex)
            div = _TWEED_LABEL_TO_DIV_FEMININE.get(tweed_label) if tweed_label else None
            if tweed_label is not None:
                parts.append(f"Typologie faciale {div} (Tweed = {tweed}°).")
            elif tweed is not None:
                parts.append(f"Tweed = {tweed}° (référence normative non validée).")
            diag_sq = " ".join(parts)

        if not diag_dent:
            impa = cephalo.metrics.analyse_dentaire.IMPA.valeur
            if impa is not None:
                diag_dent = f"Position incisive mandibulaire : IMPA = {impa}°."

        return f"{diag_sq} {diag_dent}".strip()

    def _generate_resume_moulages(self, clinique: schemas.ClinicalData) -> str:
        parts = []
        classes = []
        if clinique.classe_molaire_droite: classes.append(f"Molaire Droite: Cl {clinique.classe_molaire_droite}")
        if clinique.classe_molaire_gauche: classes.append(f"Molaire Gauche: Cl {clinique.classe_molaire_gauche}")
        if clinique.classe_canine_droite: classes.append(f"Canine Droite: Cl {clinique.classe_canine_droite}")
        if clinique.classe_canine_gauche: classes.append(f"Canine Gauche: Cl {clinique.classe_canine_gauche}")

        if classes:
            parts.append("Rapports d'Occlusion: " + " | ".join(classes) + ".")
            mg = clinique.classe_molaire_gauche
            md = clinique.classe_molaire_droite
            if mg and md and mg != md:
                parts.append("Asymétrie de classe molaire (Subdivision) détectée.")

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
        anb_label = _authoritative_label("ANB", anb, age, sex)
        skeletal_class = _ANB_LABEL_TO_SKELETAL_CLASS.get(anb_label) if anb_label else None
        impa_label = _authoritative_label("IMPA", impa, age, sex)
        if skeletal_class == "II":
            synthese.append("La Classe II squelettique est le problème sagittal majeur.")
            if ddm is not None and ddm < -4:
                synthese.append("Elle est aggravée par un encombrement dentaire limitant les compensations.")
            if impa_label == "Proalveolie mandibulaire":
                synthese.append("Notez une forte proalvéolie mandibulaire (compensation physiologique à gérer).")
        elif skeletal_class == "III":
            synthese.append("Problématique de Classe III squelettique identifiée.")
            if impa_label == "Retroalveolie mandibulaire":
                synthese.append("L'incisive inférieure est linguoversée en tentative de compensation naturelle.")
        elif skeletal_class == "I":
            synthese.append("Bases osseuses équilibrées sagittalement (Classe I).")
            if ddm is not None and ddm < -5:
                synthese.append("L'encombrement dentaire (DDM) constitue le défi thérapeutique principal.")
        return " ".join(synthese)

    def _generate_plan_traitement(self, cephalo: schemas.CephaloAnalysisResult, clinique: schemas.ClinicalData) -> str:
        """Legacy non appelé : conservé temporairement pour compatibilité, sans usage dans generate_bilan."""
        if clinique.plan_traitement and len(clinique.plan_traitement) > 50:
            return clinique.plan_traitement

        cvm = clinique.cvm or "CS3"
        ddm = clinique.ddm_reelle
        denture = clinique.denture_type or "PERMANENTE"
        tech = clinique.preference_technique or "DAMON"
        is_interceptive = denture in ["TEMPORAIRE", "MIXTE"] or cvm in ["CS1", "CS2"]
        plan = []
        plan.append(f"### 🎯 ORIENTATION : {'TRAITEMENT INTERCEPTIF' if is_interceptive else 'TRAITEMENT GLOBAL'}")
        if is_interceptive:
            plan.append(f"Patient en denture {denture.lower()}. Objectif : Correction squelettique et préparation d'arcade.")
        else:
            plan.append("Patient en denture permanente. Objectif : Alignement, nivellement et coordination occlusale.")
        if tech == "DAMON":
            mechanical_text = "- **Mécanique Passive (Système Damon)** : Expansion physiologique privilégiée. Utilisation de forces légères pour limiter les extractions."
            if ddm is not None:
                mechanical_text = f"- **Mécanique Passive (Système Damon)** : Expansion physiologique privilégiée. Utilisation de forces légères pour limiter les extractions malgré une DDM de {ddm} mm."
            plan.append(mechanical_text)
        elif tech == "ALIGNEURS":
            plan.append("- **Système d'Aligneurs (Invisalign)** : Séquençage précis des mouvements. Prévoir stripping (IPR) pour résoudre l'encombrement.")
        else:
            plan.append("- **Multi-attaches Conventionnel** : Alignement standard avec contrôle strict de l'ancrage.")
        return "\n".join(plan)

bilan_ortho_engine = BilanOrthoEngine()
