import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from backend import models
from backend.services.ghost_memory_service import ghost_memory

logger = logging.getLogger(__name__)


class CMOAgentService:
    """
    Synthèse clinique déterministe et non prescriptive.

    Le service peut signaler des éléments textuels présents dans les comptes rendus,
    mais ne doit jamais transformer ces signaux en diagnostic, pronostic ou décision
    thérapeutique autonome. Toute décision reste sous validation du praticien.
    """

    _SIGNAL_DEFINITIONS = (
        ("carie", ("carie",), "Mention textuelle compatible avec une lésion carieuse."),
        (
            "infection",
            ("lésion", "kyste", "infection"),
            "Mention textuelle compatible avec un foyer lésionnel ou infectieux.",
        ),
        (
            "parodontal",
            ("parodont",),
            "Mention textuelle compatible avec un élément parodontal.",
        ),
        (
            "dent_incluse",
            ("sagesse", "incluse"),
            "Mention textuelle compatible avec une dent incluse ou une dent de sagesse.",
        ),
    )

    def generate_global_synthesis(
        self,
        db: Session,
        patient_id: int,
        employer_id: int = 1,
    ) -> Dict[str, Any]:
        """Génère une synthèse de signaux avec frontière clinique fail-safe."""
        pano = (
            db.query(models.PanoramicAnalysis)
            .filter(models.PanoramicAnalysis.patient_id == patient_id)
            .order_by(models.PanoramicAnalysis.created_at.desc())
            .first()
        )
        cephalo = (
            db.query(models.CephaloAnalysis)
            .filter(models.CephaloAnalysis.patient_id == patient_id)
            .order_by(models.CephaloAnalysis.created_at.desc())
            .first()
        )

        if not pano and not cephalo:
            return self._empty_fallback()

        evidence: List[Dict[str, Any]] = []
        signal_labels: List[str] = []

        if pano and pano.report_narrative:
            pano_text = pano.report_narrative.lower()
            for signal, keywords, description in self._SIGNAL_DEFINITIONS:
                matched = [keyword for keyword in keywords if keyword in pano_text]
                if not matched:
                    continue
                signal_labels.append(signal)
                evidence.append(
                    {
                        "source": "panoramic_report_narrative",
                        "signal": signal,
                        "matched_terms": matched,
                        "description": description,
                    }
                )

        synthese_parts = ["Dossier clinique fusionné."]
        if pano:
            if evidence:
                synthese_parts.append(
                    "La panoramique contient des signaux textuels à confronter à l'examen clinique."
                )
            else:
                synthese_parts.append(
                    "La panoramique est disponible sans signal textuel ciblé par cette synthèse."
                )
        else:
            synthese_parts.append("Aucune donnée panoramique récente.")

        if cephalo:
            synthese_parts.append("L'analyse céphalométrique est disponible au dossier.")
        else:
            synthese_parts.append("Aucune donnée céphalométrique récente.")

        if evidence:
            soins_prealables = "\n".join(
                f"- Signal à vérifier : {item['description']}" for item in evidence
            )
        else:
            soins_prealables = (
                "Aucun signal textuel ciblé identifié automatiquement. "
                "Cela n'exclut aucune pathologie ni aucun besoin de soin."
            )

        plan_orthodontique = (
            "Aucune décision de début, report ou choix thérapeutique n'est produite automatiquement. "
            "Le praticien doit valider les données d'imagerie, l'examen clinique et le diagnostic "
            "avant toute décision orthodontique."
        )
        uncertainty = (
            "Les signaux proviennent d'une détection lexicale dans un compte rendu et ne démontrent "
            "ni diagnostic, ni sévérité, ni indication thérapeutique."
            if pano and pano.report_narrative
            else "Données insuffisantes pour interpréter automatiquement la situation clinique."
        )

        result = {
            "synthese_clinique": " ".join(synthese_parts),
            "soins_prealables": soins_prealables,
            "plan_orthodontique": plan_orthodontique,
            "pronostic": "Non déterminé automatiquement",
            "is_fallback": False,
            "signals": signal_labels,
            "evidence": evidence,
            "uncertainty": uncertainty,
            "practitioner_validation_required": True,
            "decision_status": "NON_PRESCRIPTIVE",
        }

        context_str = (
            result["synthese_clinique"]
            + "\n"
            + result["soins_prealables"]
            + "\n"
            + result["uncertainty"]
        )
        if evidence:
            content = (
                "Signal CMO : éléments textuels d'imagerie à vérifier par le praticien ; "
                "aucune décision thérapeutique automatisée."
            )
        else:
            content = (
                "Synthèse CMO : données d'imagerie disponibles ; "
                "aucune décision thérapeutique automatisée."
            )

        ghost_memory.add_memory(
            db=db,
            patient_id=patient_id,
            employer_id=employer_id,
            insight_type="CMO_SIGNAL",
            content=content,
            context_data=context_str,
        )

        return result

    def _empty_fallback(self) -> Dict[str, Any]:
        return {
            "synthese_clinique": (
                "Dossier incomplet. Une synthèse automatique fiable n'est pas possible "
                "sans imagerie disponible."
            ),
            "soins_prealables": "Non évaluables automatiquement.",
            "plan_orthodontique": (
                "Aucune décision thérapeutique automatique. Validation praticien requise."
            ),
            "pronostic": "Non déterminé automatiquement",
            "is_fallback": True,
            "signals": [],
            "evidence": [],
            "uncertainty": "Données insuffisantes pour une synthèse clinique automatisée.",
            "practitioner_validation_required": True,
            "decision_status": "NON_PRESCRIPTIVE",
        }


cmo_agent = CMOAgentService()
