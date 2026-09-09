# -*- coding: utf-8 -*-
import logging
from typing import List, Dict, Any

from sqlalchemy.orm import Session

from backend.models import Patient

logger = logging.getLogger(__name__)


class ClinicalCoherenceService:
    """Moteur de vigilance documentaire/clinique transitoire."""

    async def analyze_coherence(
        self,
        patient_id: int,
        doc_type: str,
        doc_data: Dict[str, Any],
        db: Session,
        doctor_id: int = None,
    ) -> List[Dict[str, Any]]:
        warnings: List[Dict[str, Any]] = []

        if doc_type == "ordonnance":
            warnings.extend(self._check_ordonnance_coherence(patient_id, doc_data, db))
        elif doc_type in ["devis", "note"]:
            warnings.extend(self._check_accounting_coherence(patient_id, doc_data, db))

        if warnings:
            logger.info(
                "Clinical Coherence: %s alertes totales pour Patient %s",
                len(warnings),
                patient_id,
            )

        return warnings

    def _check_ordonnance_coherence(
        self,
        patient_id: int,
        doc_data: Dict[str, Any],
        db: Session,
    ) -> List[Dict[str, Any]]:
        """Conserve seulement les contrôles encore justifiables avant rebuild.

        La règle historique « antibiotique sans acte invasif récent » a été retirée :
        l'indication d'une antibiothérapie dépend du diagnostic et du contexte
        clinique, pas de la simple présence d'un acte chirurgical/endodontique.
        """
        warnings: List[Dict[str, Any]] = []
        medications = doc_data.get("medications", [])

        # Validation documentaire transitoire. À déplacer vers le validateur
        # d'ordonnance canonique lors de la consolidation.
        for med in medications:
            if not med.get("dosage") or med.get("dosage").strip() == "":
                warnings.append(
                    {
                        "level": "info",
                        "message": (
                            f"Le dosage pour '{med.get('nom')}' est vide. "
                            "Vérifiez la précision de l'ordonnance."
                        ),
                    }
                )

        # Contrôle clinique transitoire. La détection par mots-clés reste à
        # remplacer par un futur moteur pharmacologique structuré et sourcé.
        has_nsaid = any(self._is_nsaid(m.get("nom", "")) for m in medications)
        if has_nsaid:
            patient = db.query(Patient).filter(Patient.id == patient_id).first()
            if patient and self._is_stomach_risk(patient.antecedents_medicaux):
                warnings.append(
                    {
                        "level": "critical",
                        "message": (
                            "🚨 Alerte Gastrique : Prescription d'anti-inflammatoire "
                            "(AINS) détectée chez un patient avec antécédents "
                            "gastro-intestinaux à vérifier."
                        ),
                    }
                )

        return warnings

    def _check_accounting_coherence(
        self,
        patient_id: int,
        doc_data: Dict[str, Any],
        db: Session,
    ) -> List[Dict[str, Any]]:
        """Compatibilité legacy ; à déplacer hors du moteur clinique."""
        warnings: List[Dict[str, Any]] = []
        items = doc_data.get("items", []) or doc_data.get("payments", [])
        for item in items:
            prix = item.get("prix_unitaire", 0) or item.get("montant", 0)
            if float(prix) == 0:
                warnings.append(
                    {
                        "level": "info",
                        "message": (
                            f"Acte '{item.get('description', item.get('libelle', 'Inconnu'))}' "
                            "avec montant à 0 MAD. Est-ce un acte gracieux ?"
                        ),
                    }
                )
        return warnings

    @staticmethod
    def _is_nsaid(name: str) -> bool:
        keywords = [
            "ibuprofene",
            "advil",
            "nurofen",
            "acigam",
            "brufen",
            "nurodol",
            "agifene",
            "algantil",
            "analgyl",
            "antarene",
            "diclofenac",
            "voltarene",
            "diclo pharma",
            "naproxene",
            "apranax",
            "naprosyne",
            "ketoprofene",
            "profenid",
            "bi-profenid",
            "flexen",
            "ketoflex",
            "ketum",
            "nifluril",
            "niflumique",
            "surgam",
            "tiaprofénique",
        ]
        return any(k in name.lower() for k in keywords)

    @staticmethod
    def _is_stomach_risk(antecedents: str) -> bool:
        if not antecedents:
            return False
        keywords = ["ulcère", "ulcere", "gastrite", "estomac", "reflux", "gerd", "rgo"]
        return any(k in antecedents.lower() for k in keywords)


coherence_service = ClinicalCoherenceService()
