import logging
from typing import Dict, Optional

from backend import schemas

logger = logging.getLogger(__name__)


class AIAdvisor:
    """Legacy compatibility adapter for cephalometric narrative consumers.

    The former implementation mixed measurements, diagnostic interpretation and
    autonomous treatment strategy. During Scientific Core rebuild this adapter
    intentionally fails closed: it may expose documented raw measurements, but
    it never selects treatment, appliance, mechanics, imaging or surgery.
    """

    def __init__(self):
        self.model_name = "scientific-core-fail-closed"

    def generate_diagnostic(
        self,
        result: schemas.CephaloAnalysisResult,
        use_slm: bool = False,
        age: Optional[int] = None,
        sex: Optional[str] = None,
    ) -> Dict[str, str]:
        del use_slm, age, sex
        return self._generate_nlg_report(result.metrics, result.analysis_metadata.cohort)

    def _generate_nlg_report(
        self,
        metrics: schemas.AnalysisMetrics,
        cohort: str,
        age: Optional[int] = None,
        sex: Optional[str] = None,
    ) -> Dict[str, str]:
        del age, sex

        osseuse = metrics.analyse_osseuse
        dentaire = metrics.analyse_dentaire

        raw = []
        for label, measurement in (
            ("ANB", osseuse.ANB),
            ("Tweed", osseuse.Angle_de_Tweed),
            ("IMPA", dentaire.IMPA),
            ("I/Francfort", dentaire.I_Francfort),
            ("Surplomb", dentaire.Surplomb),
            ("Recouvrement", dentaire.Recouvrement),
        ):
            value = getattr(measurement, "valeur", None)
            if value is not None:
                raw.append(f"{label} = {value}")

        observations = "; ".join(raw) if raw else "Aucune mesure céphalométrique exploitable documentée."
        diagnostic = (
            f"Cohorte documentée : {cohort}. Mesures brutes : {observations}. "
            "Aucune interprétation diagnostique autonome n'est produite par ce module legacy."
        )
        treatment = (
            "Aucune stratégie thérapeutique n'est générée automatiquement. "
            "La décision relève du praticien après validation clinique, radiographique "
            "et normative applicable."
        )

        return {
            "diagnostic_squelettique": diagnostic,
            "analyse_dentaire": observations,
            "strategie_therapeutique": treatment,
            "is_fallback": False,
        }


ai_advisor = AIAdvisor()
