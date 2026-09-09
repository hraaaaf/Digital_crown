"""Fail-closed orthodontic summary adapter.

Only patient measurements and practitioner-entered observations are restated.
No normative classification, diagnostic synthesis, severity grading, appliance
choice, mechanics, imaging indication or treatment is inferred here.
"""

from typing import Dict, Optional

from backend import schemas


class BilanOrthoEngine:
    """Compatibility adapter that preserves observations without clinical inference."""

    def generate_bilan(
        self,
        cephalo: schemas.CephaloAnalysisResult,
        clinique: schemas.ClinicalData,
        age: Optional[int] = None,
        sex: Optional[str] = None,
    ) -> Dict[str, str]:
        del age, sex
        plan_traitement = (
            clinique.plan_traitement.strip()
            if clinique.plan_traitement and clinique.plan_traitement.strip()
            else (
                "Aucune stratégie thérapeutique n'est générée automatiquement. "
                "Le plan de traitement relève exclusivement de la décision du praticien."
            )
        )
        return {
            "diagnostic_squelettique": self._raw_cephalo_observations(cephalo),
            "analyse_moulages": self._raw_clinical_observations(clinique),
            "synthese_diagnostique": (
                "Aucune synthèse diagnostique autonome n'est générée. "
                "L'interprétation appartient au praticien."
            ),
            "strategie_therapeutique": plan_traitement,
            "is_fallback": False,
        }

    @staticmethod
    def _raw_cephalo_observations(cephalo: schemas.CephaloAnalysisResult) -> str:
        observations = []
        for label, measurement, unit in (
            ("SNA", cephalo.metrics.analyse_osseuse.SNA, "°"),
            ("SNB", cephalo.metrics.analyse_osseuse.SNB, "°"),
            ("ANB", cephalo.metrics.analyse_osseuse.ANB, "°"),
            ("Angle de Tweed", cephalo.metrics.analyse_osseuse.Angle_de_Tweed, "°"),
            ("Situation A", cephalo.metrics.analyse_osseuse.Situation_A, "mm"),
            ("Situation B", cephalo.metrics.analyse_osseuse.Situation_B, "mm"),
            ("Décalage A-B", cephalo.metrics.analyse_osseuse.Decalage_A_B, "mm"),
            ("IMPA", cephalo.metrics.analyse_dentaire.IMPA, "°"),
            ("I/Francfort", cephalo.metrics.analyse_dentaire.I_Francfort, "°"),
            ("Angle inter-incisif", cephalo.metrics.analyse_dentaire.Inter_Incisif, "°"),
            ("Surplomb", cephalo.metrics.analyse_dentaire.Surplomb, "mm"),
            ("Recouvrement", cephalo.metrics.analyse_dentaire.Recouvrement, "mm"),
        ):
            value = measurement.valeur
            if value is not None:
                observations.append(f"{label} = {value}{unit}")
        return (
            "Mesures céphalométriques brutes : " + "; ".join(observations) + "."
            if observations
            else "Aucune mesure céphalométrique exploitable documentée."
        )

    @staticmethod
    def _raw_clinical_observations(clinique: schemas.ClinicalData) -> str:
        observations = []
        for label, value in (
            ("Classe molaire droite", clinique.classe_molaire_droite),
            ("Classe molaire gauche", clinique.classe_molaire_gauche),
            ("Classe canine droite", clinique.classe_canine_droite),
            ("Classe canine gauche", clinique.classe_canine_gauche),
            ("Forme d'arcade", clinique.forme_arcade),
        ):
            if value:
                observations.append(f"{label} : {value}")
        if clinique.subdivision is not None:
            observations.append(f"Subdivision : {'oui' if clinique.subdivision else 'non'}")
        if clinique.ddm_reelle is not None:
            observations.append(f"DDM clinique documentée : {clinique.ddm_reelle} mm")
        return "; ".join(observations) + "." if observations else "Aucune donnée de moulages fournie."

    def _generate_plan_traitement(
        self,
        cephalo: schemas.CephaloAnalysisResult,
        clinique: schemas.ClinicalData,
    ) -> str:
        """Compatibility boundary: preserve practitioner plan only."""
        del cephalo
        if clinique.plan_traitement and clinique.plan_traitement.strip():
            return clinique.plan_traitement.strip()
        return (
            "Aucune stratégie thérapeutique n'est générée automatiquement. "
            "Le plan de traitement relève exclusivement de la décision du praticien."
        )


bilan_ortho_engine = BilanOrthoEngine()
