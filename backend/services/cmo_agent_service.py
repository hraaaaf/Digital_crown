import logging
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from backend import models
from backend.services.ghost_memory_service import ghost_memory

logger = logging.getLogger(__name__)


class CMOAgentService:
    """
    Synthèse clinique déterministe de signaux issus de l'imagerie.

    Ce service est une aide à la revue du dossier. Il ne doit jamais transformer
    un signal textuel en diagnostic, pronostic, indication thérapeutique ou feu
    vert de traitement autonome.
    """

    def generate_global_synthesis(
        self,
        db: Session,
        patient_id: int,
        employer_id: int = 1,
    ) -> Dict[str, Any]:
        """Génère une synthèse non prescriptive, sans LLM."""
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

        synthese_parts: List[str] = ["Dossier clinique fusionné."]
        review_parts: List[str] = []
        ortho_parts: List[str] = []
        signals: List[Dict[str, str]] = []

        if pano and pano.report_narrative:
            pano_text = pano.report_narrative.lower()

            signal_rules = (
                (
                    "CARIES_TEXT_SIGNAL",
                    ("carie",),
                    "Mention textuelle compatible avec une lésion carieuse",
                ),
                (
                    "INFECTION_TEXT_SIGNAL",
                    ("lésion", "kyste", "parodont", "infection"),
                    "Mention textuelle compatible avec un processus lésionnel, parodontal ou infectieux",
                ),
                (
                    "WISDOM_TOOTH_TEXT_SIGNAL",
                    ("sagesse", "incluse"),
                    "Mention textuelle concernant une dent de sagesse ou une inclusion",
                ),
            )

            for code, keywords, label in signal_rules:
                matched = [keyword for keyword in keywords if keyword in pano_text]
                if not matched:
                    continue
                evidence = ", ".join(matched)
                signals.append(
                    {
                        "code": code,
                        "label": label,
                        "source": "panoramic_report_narrative",
                        "evidence": evidence,
                        "uncertainty": "Signal lexical uniquement ; contexte, négation et diagnostic clinique non établis.",
                    }
                )
                review_parts.append(
                    f"- Signal textuel à vérifier : {label.lower()} (terme(s) repéré(s) : {evidence})."
                )

            if signals:
                synthese_parts.append(
                    f"Le compte rendu panoramique contient {len(signals)} signal(aux) textuel(s) à vérifier cliniquement."
                )
            else:
                synthese_parts.append(
                    "Le compte rendu panoramique est disponible ; aucun des signaux lexicaux ciblés n'a été repéré."
                )
        else:
            synthese_parts.append("Aucune donnée panoramique récente.")

        if cephalo:
            synthese_parts.append("L'analyse céphalométrique est disponible au dossier.")
            if signals:
                ortho_parts.append(
                    "Des signaux panoramiques restent à vérifier avant toute décision orthodontique."
                )
            else:
                ortho_parts.append(
                    "Aucun signal lexical ciblé n'a été repéré sur le compte rendu panoramique ; cela ne constitue pas un feu vert thérapeutique."
                )
            ortho_parts.append(
                "La décision orthodontique doit être établie et validée par le praticien à partir de l'examen clinique et des données diagnostiques appropriées."
            )
        else:
            synthese_parts.append("Aucune donnée céphalométrique.")
            ortho_parts.append(
                "Décision orthodontique non établie automatiquement ; données diagnostiques et validation praticien requises."
            )

        if not review_parts:
            review_parts.append(
                "Aucun signal lexical ciblé identifié à l'imagerie ; cette absence ne permet pas de conclure à l'absence de pathologie."
            )

        result = {
            "synthese_clinique": " ".join(synthese_parts),
            "soins_prealables": "\n".join(review_parts),
            "plan_orthodontique": "\n".join(ortho_parts),
            "pronostic": "Non évalué automatiquement",
            "signals": signals,
            "uncertainty": (
                "Les signaux proviennent d'un repérage lexical du compte rendu et peuvent inclure faux positifs, "
                "négations ou contexte incomplet."
            ),
            "requires_practitioner_validation": True,
            "decision_status": "NON_EVALUE",
            "is_fallback": False,
        }

        context_str = result["synthese_clinique"] + " " + result["soins_prealables"]
        if signals:
            content = (
                f"Signal CMO non validé : {len(signals)} mention(s) textuelle(s) à vérifier. "
                "Validation praticien requise."
            )
        else:
            content = (
                "Synthèse CMO : aucun signal lexical ciblé détecté. "
                "Cette absence ne constitue pas une validation clinique."
            )

        ghost_memory.add_memory(
            db=db,
            patient_id=patient_id,
            employer_id=employer_id,
            insight_type="ORTHO",
            content=content,
            context_data=context_str,
        )

        return result

    def _empty_fallback(self) -> Dict[str, Any]:
        return {
            "synthese_clinique": (
                "Dossier incomplet. Nécessite au minimum une radiographie panoramique ou téléradiographie."
            ),
            "soins_prealables": "À évaluer par le praticien.",
            "plan_orthodontique": "Décision non établie ; en attente des examens et de la validation praticien.",
            "pronostic": "Non évalué automatiquement",
            "signals": [],
            "uncertainty": "Données d'imagerie insuffisantes pour une synthèse.",
            "requires_practitioner_validation": True,
            "decision_status": "NON_EVALUE",
            "is_fallback": True,
        }


cmo_agent = CMOAgentService()
