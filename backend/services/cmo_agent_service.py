import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from backend import models
from backend.services.ghost_memory_service import ghost_memory

logger = logging.getLogger(__name__)


class CMOAgentService:
    """
    Synthèse documentaire clinique déterministe et non prescriptive.

    Le service peut signaler des mentions présentes dans les comptes rendus,
    mais ne doit ni diagnostiquer, ni établir un pronostic, ni autoriser,
    reporter ou prescrire un traitement de manière autonome.
    """

    @staticmethod
    def _matched_terms(text: str, terms: List[str]) -> List[str]:
        return [term for term in terms if term in text]

    def _build_non_prescriptive_synthesis(
        self,
        pano_text: Optional[str],
        cephalo_available: bool,
    ) -> Dict[str, Any]:
        """Transforme des données documentaires en signaux à valider par le praticien."""
        normalized = (pano_text or "").lower()
        evidence: List[Dict[str, Any]] = []
        signal_parts: List[str] = []

        signal_groups = (
            (
                "mention_carie",
                ["carie"],
                "Mention textuelle liée à une carie dans le compte rendu panoramique.",
            ),
            (
                "mention_infection_ou_lesion",
                ["lésion", "kyste", "parodont", "infection"],
                "Mention textuelle liée à une lésion, une infection ou au parodonte dans le compte rendu panoramique.",
            ),
            (
                "mention_dent_sagesse_incluse",
                ["sagesse", "incluse"],
                "Mention textuelle liée à une dent de sagesse ou à une inclusion dans le compte rendu panoramique.",
            ),
        )

        if pano_text:
            for signal_id, terms, description in signal_groups:
                matches = self._matched_terms(normalized, terms)
                if not matches:
                    continue
                evidence.append(
                    {
                        "source": "panoramic_report_narrative",
                        "signal": signal_id,
                        "matched_terms": matches,
                    }
                )
                signal_parts.append(
                    f"- {description} Signal documentaire uniquement : à confronter à l'examen clinique."
                )
        else:
            signal_parts.append("- Aucune donnée panoramique récente disponible.")

        if pano_text and not evidence:
            signal_parts.append(
                "- Aucun des signaux textuels ciblés n'a été détecté automatiquement. "
                "Cela n'exclut aucune pathologie."
            )

        if cephalo_available:
            ortho_text = (
                "Analyse céphalométrique disponible au dossier. Aucune décision d'initier, "
                "de reporter ou de modifier un traitement orthodontique n'est produite "
                "automatiquement ; décision réservée au praticien après confrontation clinique."
            )
        else:
            ortho_text = (
                "Aucune donnée céphalométrique disponible. Aucune décision orthodontique "
                "automatique ne peut être produite."
            )

        synthesis_parts = ["Synthèse de signaux documentaires."]
        synthesis_parts.append(
            "Compte rendu panoramique disponible." if pano_text else "Aucune donnée panoramique récente."
        )
        synthesis_parts.append(
            "Analyse céphalométrique disponible." if cephalo_available else "Aucune donnée céphalométrique."
        )

        return {
            "synthese_clinique": " ".join(synthesis_parts),
            "soins_prealables": "\n".join(signal_parts),
            "plan_orthodontique": ortho_text,
            "pronostic": "Non déterminé automatiquement",
            "is_fallback": False,
            "evidence": evidence,
            "uncertainty": (
                "La détection repose sur des mentions textuelles et ne tient pas lieu de diagnostic. "
                "Le contexte, les négations et la concordance radio-clinique doivent être vérifiés."
            ),
            "practitioner_validation_required": True,
            "automation_scope": "signal_only",
        }

    def generate_global_synthesis(
        self,
        db: Session,
        patient_id: int,
        employer_id: int = 1,
    ) -> Dict[str, Any]:
        """Génère une synthèse non prescriptive en croisant les données disponibles, sans LLM."""
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

        pano_text = pano.report_narrative if pano and pano.report_narrative else None
        result = self._build_non_prescriptive_synthesis(
            pano_text=pano_text,
            cephalo_available=bool(cephalo),
        )

        context_str = result["synthese_clinique"] + "\n" + result["soins_prealables"]
        signals = [item["signal"] for item in result["evidence"]]
        content = (
            "Signal CMO à vérifier par le praticien : " + ", ".join(signals)
            if signals
            else "Signal CMO : aucune conclusion thérapeutique automatique ; validation praticien requise."
        )

        ghost_memory.add_memory(
            db=db,
            patient_id=patient_id,
            employer_id=employer_id,
            insight_type="SIGNAL_CLINIQUE",
            content=content,
            context_data=context_str,
        )

        return result

    def _empty_fallback(self) -> Dict[str, Any]:
        return {
            "synthese_clinique": "Dossier d'imagerie insuffisant pour produire des signaux documentaires.",
            "soins_prealables": "Aucune conclusion thérapeutique automatique.",
            "plan_orthodontique": "Aucune décision orthodontique automatique.",
            "pronostic": "Non déterminé automatiquement",
            "is_fallback": True,
            "evidence": [],
            "uncertainty": "Données insuffisantes.",
            "practitioner_validation_required": True,
            "automation_scope": "signal_only",
        }


cmo_agent = CMOAgentService()
