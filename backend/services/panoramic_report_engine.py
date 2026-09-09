import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

# Manual practitioner labels only. The report engine must not upgrade these
# observations into diagnoses, normality claims, treatment plans, or billing acts.
ANOMALY_LABELS = {
    # Conservatrice
    "carie_email": "Carie de l'émail",
    "carie_dentinaire": "Carie dentinaire",
    "carie_profonde": "Carie profonde (atteinte pulpaire)",
    "reprise_carie": "Reprise de carie sous obturation",
    "obturation_comp": "Obturation (composite/amalgame)",
    "obturation_debord": "Obturation débordante",
    # Endodontie
    "lesion_periapicale": "Lésion périapicale (kyste/granulome)",
    "elargissement_desmo": "Élargissement desmodontal",
    "tr_adequat": "Traitement canalaire adéquat",
    "tr_incomplet": "Traitement canalaire incomplet",
    "depassement_pate": "Dépassement de pâte canalaire",
    "instrument_fracture": "Instrument fracturé intra-canalaire",
    "perforation": "Perforation (faux-canal)",
    # Parodontie
    "alveolyse_h": "Alvéolyse horizontale localisée",
    "alveolyse_v": "Alvéolyse verticale (défaut angulaire)",
    "furcation": "Atteinte de la furcation",
    "tartre": "Tartre sous-gingival",
    # Chirurgie
    "dent_absente": "Dent absente",
    "agenesie": "Agénésie dentaire",
    "surnumeraire": "Dent surnuméraire",
    "incluse": "Dent incluse",
    "enclavee": "Dent enclavée",
    "reste_radiculaire": "Reste radiculaire",
    "resorption": "Résorption radiculaire",
    # Prothèse
    "couronne": "Couronne prothétique",
    "bridge": "Bridge prothétique",
    "implant": "Implant dentaire",
    "appareil": "Appareil / prothèse amovible",
    "peri_implantite": "Péri-implantite",
    "infiltration_prothese": "Infiltration sous prothèse",
    # ATM / Sinus
    "opacite_sinus": "Opacité sinusienne",
    "racine_sinus": "Racine au contact du sinus",
    "condyle_asymetrie": "Asymétrie condylienne",
    "arthrose_atm": "Arthrose de l'ATM",
    "calcification": "Calcification (carotide/sialolithe)",
}

GLOBAL_FINDING_LABELS = {
    "alveolyse_gen_legere": "Alvéolyse horizontale généralisée légère (parodontite débutante)",
    "alveolyse_gen_moderee": "Alvéolyse horizontale généralisée modérée",
    "alveolyse_gen_severe": "Alvéolyse généralisée sévère (parodontite avancée)",
    "parodontite_gen": "Aspect de maladie parodontale généralisée",
    "denture_mixte": "Denture mixte (phase de remplacement dentaire)",
    "edentement_total_max": "Édentement total maxillaire",
    "edentement_total_mand": "Édentement total mandibulaire",
}


class PanoramicReportEngine:
    """Deterministic formatter for practitioner-entered panoramic observations.

    Scientific boundary:
    - tooth detection is not a diagnosis;
    - absence of an annotation is not evidence of normality;
    - a practitioner annotation is rendered as an observation, not upgraded;
    - this engine emits no treatment or CCAM recommendation.
    """

    def generate_markdown(
        self,
        detections: List[Dict] = None,
        manual_anomalies: Dict[int, List[str]] = None,
        global_findings: List[str] = None,
    ) -> str:
        try:
            if isinstance(detections, dict):
                detections = detections.get("detections", [])
            detections = detections or []
            manual_anomalies = manual_anomalies or {}
            global_findings = global_findings or []

            teeth_ids: Dict[int, set] = {}
            for fdi_str, anomalies in manual_anomalies.items():
                fdi = int(fdi_str)
                teeth_ids.setdefault(fdi, set())
                for anomaly_id in anomalies:
                    teeth_ids[fdi].add(anomaly_id)

            absent_teeth = sorted(
                fdi
                for fdi, ids in teeth_ids.items()
                if "dent_absente" in ids or "agenesie" in ids
            )

            anomaly_map: Dict[str, List[int]] = {}
            for fdi, ids in teeth_ids.items():
                for anomaly_id in ids:
                    if anomaly_id in ("dent_absente", "agenesie"):
                        continue
                    anomaly_map.setdefault(anomaly_id, []).append(fdi)
            for anomaly_id in anomaly_map:
                anomaly_map[anomaly_id].sort()

            lines: List[str] = [
                "### SYNTHÈSE RADIOGRAPHIQUE",
                f"- {self._build_synthesis(anomaly_map, absent_teeth, global_findings)}",
                "",
                "### TECHNIQUE",
                "- Examen panoramique numérique.",
                "",
                "### RÉSULTATS",
            ]

            if "denture_mixte" in global_findings:
                lines.append("- Observation praticien : denture mixte.")
            else:
                lines.append("- Type de dentition : non documenté par les annotations fournies.")

            if absent_teeth:
                lines.append(
                    f"- Observation praticien : {self._fmt_teeth_phrase(absent_teeth, 'Absence')}."
                )

            for anomaly_id in sorted(anomaly_map):
                lines.append(
                    "- Observation praticien : "
                    + self._observation_phrase(anomaly_id, anomaly_map[anomaly_id])
                )

            for finding_id in global_findings:
                if finding_id == "denture_mixte":
                    continue
                label = GLOBAL_FINDING_LABELS.get(finding_id, finding_id)
                lines.append(f"- Observation praticien : {label}.")

            lines.append(
                "- Structures ou territoires sans annotation explicite : non documentés / non évalués par ce rapport automatique."
            )
            lines.append(
                "- Interprétation diagnostique et conduite thérapeutique : décision du praticien à partir de l'image et du contexte clinique."
            )

            return "\n".join(lines)

        except Exception as exc:
            logger.error("Erreur Report Engine : %s", exc)
            return "## Erreur lors de la génération du rapport."

    def _fmt_teeth_phrase(self, fdis: List[int], prefix: str) -> str:
        if not fdis:
            return prefix
        if len(fdis) == 1:
            return f"{prefix} de la dent {fdis[0]}"
        body = ", ".join(str(fdi) for fdi in fdis[:-1])
        return f"{prefix} des dents {body} et {fdis[-1]}"

    def _teeth_list(self, fdis: List[int]) -> str:
        if len(fdis) == 1:
            return f"la dent {fdis[0]}"
        if len(fdis) == 2:
            return f"les dents {fdis[0]} et {fdis[1]}"
        return f"les dents {', '.join(str(fdi) for fdi in fdis[:-1])} et {fdis[-1]}"

    def _observation_phrase(self, anomaly_id: str, fdis: List[int]) -> str:
        label = ANOMALY_LABELS.get(anomaly_id, anomaly_id)
        if anomaly_id in {"condyle_asymetrie", "arthrose_atm"}:
            return f"{label}."
        return f"{label} sur {self._teeth_list(fdis)}."

    def _build_synthesis(self, anomaly_map, absent_teeth, global_findings) -> str:
        observation_count = sum(len(fdis) for fdis in anomaly_map.values()) + len(absent_teeth)
        general_count = len([finding for finding in global_findings if finding != "denture_mixte"])

        if observation_count == 0 and general_count == 0:
            return (
                "Aucune anomalie n'a été documentée dans les annotations fournies. "
                "Cela ne constitue pas une conclusion de normalité radiographique."
            )

        parts = []
        if observation_count:
            parts.append(f"{observation_count} observation(s) dentaire(s) documentée(s) par le praticien")
        if general_count:
            parts.append(f"{general_count} constat(s) général(aux) documenté(s) par le praticien")
        return "; ".join(parts) + "."


panoramic_report_engine = PanoramicReportEngine()
