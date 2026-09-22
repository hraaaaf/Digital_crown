import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

from backend.services.panoramic_report_ontology import (
    PANORAMIC_DOMAIN_SECTION_TITLES,
    PANORAMIC_DOMAIN_TITLES,
    PANORAMIC_EXPLICIT_NORMAL_TEXT,
    PANORAMIC_REPORT_DOMAINS,
)

# Manual practitioner labels only. The report engine must not upgrade these
# observations into diagnoses, normality claims, treatment plans, or billing acts.
ANOMALY_LABELS = {
    # Conservatrice
    "carie_email": "Carie de l'émail",
    "carie_dentinaire": "Carie dentinaire",
    "carie_profonde": "Image carieuse profonde",
    "reprise_carie": "Reprise de carie sous obturation",
    "obturation_comp": "Obturation (composite/amalgame)",
    "obturation_debord": "Obturation débordante",
    # Endodontie
    "lesion_periapicale": "Image radioclaire périapicale",
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
    "peri_implantite": "Perte osseuse péri-implantaire",
    "infiltration_prothese": "Infiltration sous prothèse",
    # ATM / Sinus
    "opacite_sinus": "Opacité sinusienne",
    "racine_sinus": "Racine au contact du sinus",
    "condyle_asymetrie": "Asymétrie condylienne",
    "arthrose_atm": "Remaniements osseux condyliens",
    "calcification": "Calcification (carotide/sialolithe)",
}

GLOBAL_FINDING_LABELS = {
    "alveolyse_gen_legere": "Alvéolyse horizontale généralisée légère",
    "alveolyse_gen_moderee": "Alvéolyse horizontale généralisée modérée",
    "alveolyse_gen_severe": "Alvéolyse généralisée sévère",
    "parodontite_gen": "Perte osseuse parodontale généralisée",
    "denture_mixte": "Denture mixte (phase de remplacement dentaire)",
    "edentement_total_max": "Édentement total maxillaire",
    "edentement_total_mand": "Édentement total mandibulaire",
}

ANOMALY_SECTIONS = {
    # Caries
    "carie_email": "LÉSIONS CARIEUSES",
    "carie_dentinaire": "LÉSIONS CARIEUSES",
    "carie_profonde": "LÉSIONS CARIEUSES",
    "reprise_carie": "LÉSIONS CARIEUSES",
    # Restaurations / prothèses / implants
    "obturation_comp": "RESTAURATIONS / PROTHÈSES / IMPLANTS",
    "obturation_debord": "RESTAURATIONS / PROTHÈSES / IMPLANTS",
    "couronne": "RESTAURATIONS / PROTHÈSES / IMPLANTS",
    "bridge": "RESTAURATIONS / PROTHÈSES / IMPLANTS",
    "implant": "RESTAURATIONS / PROTHÈSES / IMPLANTS",
    "appareil": "RESTAURATIONS / PROTHÈSES / IMPLANTS",
    "infiltration_prothese": "RESTAURATIONS / PROTHÈSES / IMPLANTS",
    # Périapical / endodontie
    "lesion_periapicale": "RÉGIONS PÉRIAPICALES / ENDODONTIE",
    "elargissement_desmo": "RÉGIONS PÉRIAPICALES / ENDODONTIE",
    "tr_adequat": "RÉGIONS PÉRIAPICALES / ENDODONTIE",
    "tr_incomplet": "RÉGIONS PÉRIAPICALES / ENDODONTIE",
    "depassement_pate": "RÉGIONS PÉRIAPICALES / ENDODONTIE",
    "instrument_fracture": "RÉGIONS PÉRIAPICALES / ENDODONTIE",
    "perforation": "RÉGIONS PÉRIAPICALES / ENDODONTIE",
    "resorption": "RÉGIONS PÉRIAPICALES / ENDODONTIE",
    # Parodonte
    "alveolyse_h": "PARODONTE ET SUPPORT OSSEUX",
    "alveolyse_v": "PARODONTE ET SUPPORT OSSEUX",
    "furcation": "PARODONTE ET SUPPORT OSSEUX",
    "tartre": "PARODONTE ET SUPPORT OSSEUX",
    "peri_implantite": "PARODONTE ET SUPPORT OSSEUX",
    # Dentition / anomalies dentaires
    "dent_absente": "DENTITION ET ANOMALIES DENTAIRES",
    "agenesie": "DENTITION ET ANOMALIES DENTAIRES",
    "surnumeraire": "DENTITION ET ANOMALIES DENTAIRES",
    "incluse": "DENTITION ET ANOMALIES DENTAIRES",
    "enclavee": "DENTITION ET ANOMALIES DENTAIRES",
    "reste_radiculaire": "DENTITION ET ANOMALIES DENTAIRES",
    # ATM
    "condyle_asymetrie": "ARTICULATIONS TEMPORO-MANDIBULAIRES",
    "arthrose_atm": "ARTICULATIONS TEMPORO-MANDIBULAIRES",
    # Sinus
    "opacite_sinus": "SINUS MAXILLAIRES",
    "racine_sinus": "SINUS MAXILLAIRES",
    # Non classé dans les domaines clés du template source
    "calcification": "AUTRES OBSERVATIONS DOCUMENTÉES",
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
        report_context: Optional[Dict] = None,
    ) -> str:
        try:
            if isinstance(detections, dict):
                detections = detections.get("detections", [])
            detections = detections or []
            manual_anomalies = manual_anomalies or {}
            global_findings = global_findings or []
            report_context = report_context or {}

            teeth_ids: Dict[int, set] = {}
            for fdi_str, anomalies in manual_anomalies.items():
                fdi = int(fdi_str)
                teeth_ids.setdefault(fdi, set())
                for anomaly_id in anomalies:
                    teeth_ids[fdi].add(anomaly_id)

            section_items: Dict[str, Dict[str, List[int]]] = {}
            for fdi, ids in teeth_ids.items():
                for anomaly_id in ids:
                    section = ANOMALY_SECTIONS.get(anomaly_id, "AUTRES OBSERVATIONS DOCUMENTÉES")
                    section_items.setdefault(section, {}).setdefault(anomaly_id, []).append(fdi)

            for anomalies in section_items.values():
                for anomaly_id in anomalies:
                    anomalies[anomaly_id].sort()

            lines: List[str] = []

            clinical_question = (report_context.get("clinical_question") or "").strip()
            if clinical_question:
                lines.extend([
                    "### QUESTION CLINIQUE",
                    f"- {clinical_question}",
                    "",
                ])

            lines.extend([
                "### TECHNIQUE",
                "- Radiographie panoramique numérique.",
            ])
            quality = report_context.get("image_quality", "not_assessed")
            quality_note = (report_context.get("image_quality_note") or "").strip()
            if quality == "diagnostic":
                lines.append("- Qualité jugée suffisante par le praticien pour la lecture panoramique.")
            elif quality == "limited":
                text = "- Qualité limitée pour la lecture panoramique."
                if quality_note:
                    text += f" {quality_note}"
                lines.append(text)
            elif quality == "non_diagnostic":
                text = "- Examen jugé non interprétable dans son ensemble par le praticien."
                if quality_note:
                    text += f" {quality_note}"
                lines.append(text)
            else:
                lines.append("- Qualité / interprétabilité : non évaluée dans les données structurées.")
            lines.extend([
                "- Le compte rendu reprend uniquement les constatations explicitement documentées par le praticien.",
                "",
            ])

            if "denture_mixte" in global_findings:
                lines.extend([
                    "### CONTEXTE DENTAIRE DOCUMENTÉ",
                    "- Denture mixte documentée par le praticien.",
                    "",
                ])

            context_lines_by_section: Dict[str, List[str]] = {}
            context_synthesis: List[str] = []
            unassessed_domains: List[str] = []
            for domain in PANORAMIC_REPORT_DOMAINS:
                raw = report_context.get(domain) or {}
                status = raw.get("status", "not_assessed")
                note = (raw.get("note") or "").strip()
                section = PANORAMIC_DOMAIN_SECTION_TITLES[domain]
                if status == "normal":
                    context_lines_by_section.setdefault(section, []).append(
                        PANORAMIC_EXPLICIT_NORMAL_TEXT[domain]
                    )
                elif status == "abnormal":
                    title = PANORAMIC_DOMAIN_TITLES[domain]
                    statement = (
                        note
                        if note
                        else f"{title} : anomalie signalée par le praticien, détail non renseigné."
                    )
                    context_lines_by_section.setdefault(section, []).append(statement)
                    context_synthesis.append(statement)
                else:
                    unassessed_domains.append(PANORAMIC_DOMAIN_TITLES[domain])

            ordered_sections = (
                "DENTITION ET ANOMALIES DENTAIRES",
                "RESTAURATIONS / PROTHÈSES / IMPLANTS",
                "LÉSIONS CARIEUSES",
                "RÉGIONS PÉRIAPICALES / ENDODONTIE",
                "PARODONTE ET SUPPORT OSSEUX",
                "MAXILLAIRE ET MANDIBULE",
                "ARTICULATIONS TEMPORO-MANDIBULAIRES",
                "SINUS MAXILLAIRES",
                "AUTRES OBSERVATIONS DOCUMENTÉES",
            )
            for section in ordered_sections:
                anomalies = section_items.get(section) or {}
                context_lines = context_lines_by_section.get(section) or []
                if not anomalies and not context_lines:
                    continue
                lines.append(f"### {section}")
                for anomaly_id in sorted(anomalies):
                    lines.append(f"- {self._observation_phrase(anomaly_id, anomalies[anomaly_id])}")
                lines.extend(f"- {statement}" for statement in context_lines)
                lines.append("")

            general_findings = [
                GLOBAL_FINDING_LABELS.get(finding_id, finding_id)
                for finding_id in global_findings
                if finding_id != "denture_mixte"
            ]
            if general_findings:
                lines.append("### CONSTATATIONS GÉNÉRALES")
                lines.extend(f"- {finding}." for finding in general_findings)
                lines.append("")

            clinical_answer = (report_context.get("clinical_answer") or "").strip()
            if clinical_answer:
                lines.extend([
                    "### RÉPONSE À LA QUESTION CLINIQUE",
                    f"- {clinical_answer}",
                    "",
                ])

            lines.append("### SYNTHÈSE")
            synthesis = self._build_synthesis(section_items, general_findings)
            synthesis.extend(context_synthesis)
            if synthesis:
                lines.extend(f"- {item}" for item in synthesis)
            else:
                lines.append(
                    "- Aucune constatation n'a été documentée dans les annotations fournies ; "
                    "cela ne constitue pas une conclusion de normalité radiographique."
                )
            if report_context:
                if unassessed_domains:
                    lines.append("- Domaines non évalués explicitement : " + ", ".join(unassessed_domains) + ".")
            else:
                lines.append(
                    "- Les territoires sans annotation explicite restent non documentés et ne sont pas déclarés normaux par ce compte rendu."
                )
            lines.append(
                "- Toute interprétation diagnostique ou décision thérapeutique relève du praticien après corrélation avec l'examen clinique."
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
        return f"{label} — {self._teeth_list(fdis)}."

    def _build_synthesis(self, section_items, general_findings: List[str]) -> List[str]:
        items: List[str] = []
        for section in (
            "DENTITION ET ANOMALIES DENTAIRES",
            "RESTAURATIONS / PROTHÈSES / IMPLANTS",
            "LÉSIONS CARIEUSES",
            "RÉGIONS PÉRIAPICALES / ENDODONTIE",
            "PARODONTE ET SUPPORT OSSEUX",
            "MAXILLAIRE ET MANDIBULE",
            "ARTICULATIONS TEMPORO-MANDIBULAIRES",
            "SINUS MAXILLAIRES",
            "AUTRES OBSERVATIONS DOCUMENTÉES",
        ):
            anomalies = section_items.get(section) or {}
            for anomaly_id in sorted(anomalies):
                items.append(self._observation_phrase(anomaly_id, anomalies[anomaly_id]))
        items.extend(f"{finding}." for finding in general_findings)
        return items


panoramic_report_engine = PanoramicReportEngine()
