import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# --- Lexique des états dentaires (saisie manuelle du praticien) ---
ANOMALY_LABELS = {
    # Conservatrice
    'carie_email': "Carie de l'émail",
    'carie_dentinaire': "Carie dentinaire",
    'carie_profonde': "Carie profonde (atteinte pulpaire)",
    'reprise_carie': "Reprise de carie sous obturation",
    'obturation_comp': "Obturation (composite/amalgame)",
    'obturation_debord': "Obturation débordante",
    # Endodontie
    'lesion_periapicale': "Lésion périapicale (kyste/granulome)",
    'elargissement_desmo': "Élargissement desmodontal",
    'tr_adequat': "Traitement canalaire adéquat",
    'tr_incomplet': "Traitement canalaire incomplet",
    'depassement_pate': "Dépassement de pâte canalaire",
    'instrument_fracture': "Instrument fracturé intra-canalaire",
    'perforation': "Perforation (faux-canal)",
    # Parodontie
    'alveolyse_h': "Alvéolyse horizontale localisée",
    'alveolyse_v': "Alvéolyse verticale (défaut angulaire)",
    'furcation': "Atteinte de la furcation",
    'tartre': "Tartre sous-gingival",
    # Chirurgie
    'dent_absente': "Dent absente",
    'agenesie': "Agénésie dentaire",
    'surnumeraire': "Dent surnuméraire",
    'incluse': "Dent incluse",
    'enclavee': "Dent enclavée",
    'reste_radiculaire': "Reste radiculaire",
    'resorption': "Résorption radiculaire",
    # Prothèse
    'couronne': "Couronne prothétique",
    'bridge': "Bridge prothétique",
    'implant': "Implant dentaire",
    'appareil': "Appareil / prothèse amovible",
    'peri_implantite': "Péri-implantite",
    'infiltration_prothese': "Infiltration sous prothèse",
    # ATM / Sinus
    'opacite_sinus': "Opacité sinusienne",
    'racine_sinus': "Racine au contact du sinus",
    'condyle_asymetrie': "Asymétrie condylienne",
    'arthrose_atm': "Arthrose de l'ATM",
    'calcification': "Calcification (carotide/sialolithe)",
}

# --- Constats généraux (mouth-wide, pas rattachés à une dent) ---
GLOBAL_FINDING_LABELS = {
    'alveolyse_gen_legere': "Alvéolyse horizontale généralisée légère (parodontite débutante)",
    'alveolyse_gen_moderee': "Alvéolyse horizontale généralisée modérée",
    'alveolyse_gen_severe': "Alvéolyse généralisée sévère (parodontite avancée)",
    'parodontite_gen': "Aspect de maladie parodontale généralisée",
    'denture_mixte': "Denture mixte (phase de remplacement dentaire)",
    'edentement_total_max': "Édentement total maxillaire",
    'edentement_total_mand': "Édentement total mandibulaire",
}

# --- Suggestions CCAM (conduite à tenir, déterministe) ---
CCAM_SUGGESTIONS = {
    'carie_email': "HBMD038 — Restauration 1 face",
    'carie_dentinaire': "HBMD042 — Restauration 2 faces",
    'carie_profonde': "HBMD044 / HBFD033 — Restauration profonde ou traitement endodontique",
    'reprise_carie': "HBMD042 — Dépose et restauration",
    'lesion_periapicale': "HBFD033 / HBGD035 — Retraitement canalaire ou résection apicale",
    'tr_incomplet': "HBFD033 — Retraitement endodontique",
    'incluse': "HBGD036 — Avulsion de dent incluse",
    'reste_radiculaire': "HBGD031 — Avulsion de racine résiduelle",
    'tartre': "HBJD001 — Détartrage complet",
    'furcation': "Bilan parodontal — assainissement",
    'dent_absente': "Réhabilitation prothétique (implant / bridge / amovible)",
}

# Ordre d'affichage clinique des constats (du plus urgent au plus bénin)
URGENT_KEYS = {'carie_profonde', 'lesion_periapicale', 'perforation', 'peri_implantite', 'reste_radiculaire'}


class PanoramicReportEngine:
    """
    Générateur de bilan panoramique 100 % déterministe (sans LLM).
    Le modèle IA ne fait que nommer les dents ; toute la sémiologie provient
    des annotations manuelles du praticien (par dent) et des constats généraux.
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

            # 1. Construction de la carte dent -> {id_anomalie} (manuel prioritaire)
            #    On conserve les ids bruts pour la sémantique, et un label lisible.
            teeth_ids: Dict[int, set] = {}      # fdi -> set(anomaly_id)
            for fdi_str, anomalies in manual_anomalies.items():
                fdi = int(fdi_str)
                teeth_ids.setdefault(fdi, set())
                for a in anomalies:
                    teeth_ids[fdi].add(a)

            # 2. Séparation des familles cliniques
            absent_teeth = sorted([f for f, ids in teeth_ids.items() if 'dent_absente' in ids or 'agenesie' in ids])

            # Regroupement id_anomalie -> [fdi] (hors dents absentes déjà traitées)
            anomaly_map: Dict[str, List[int]] = {}
            for fdi, ids in teeth_ids.items():
                for aid in ids:
                    if aid in ('dent_absente', 'agenesie'):
                        continue
                    anomaly_map.setdefault(aid, []).append(fdi)
            for aid in anomaly_map:
                anomaly_map[aid].sort()

            lines: List[str] = []

            # 3. SYNTHÈSE déterministe (en tête)
            synthesis = self._build_synthesis(anomaly_map, absent_teeth, global_findings)
            lines.append("### SYNTHÈSE CLINIQUE")
            # Puce (et non paragraphe brut) pour être capturé par le générateur PDF Élite.
            lines.append(f"- {synthesis}")
            lines.append("")

            # 4. TECHNIQUE
            lines.append("### TECHNIQUE")
            lines.append("- Examen réalisé sur appareil numérique, scannage unique à faible dose de rayonnement.")
            lines.append("")

            # 5. RÉSULTATS
            lines.append("### RÉSULTATS")
            denture = "mixte" if 'denture_mixte' in global_findings else "adulte"
            lines.append(f"- Dentition de type {denture}.")

            # Édentement / dents absentes
            if absent_teeth:
                lines.append(f"- {self._fmt_teeth_phrase(absent_teeth, 'Absence')} (édentement à réhabiliter).")

            # Constats par anomalie (ordre : urgent d'abord)
            ordered_aids = sorted(anomaly_map.keys(), key=lambda a: (a not in URGENT_KEYS, a))
            for aid in ordered_aids:
                fdis = anomaly_map[aid]
                lines.append("- " + self._phrase_for(aid, fdis))

            # Constats généraux (lyse généralisée, etc.)
            for gid in global_findings:
                if gid == 'denture_mixte':
                    continue  # déjà reflété dans le type de denture
                label = GLOBAL_FINDING_LABELS.get(gid, gid)
                lines.append(f"- {label}.")

            # 6. Phrases de normalité conditionnelles (sinus / os / ATM)
            self._append_normality(lines, anomaly_map, global_findings)

            # 7. CONDUITE À TENIR (CCAM déterministe)
            recos = self._build_recommendations(anomaly_map, absent_teeth)
            if recos:
                lines.append("")
                lines.append("### CONDUITE À TENIR")
                for r in recos:
                    lines.append(f"- {r}")

            return "\n".join(lines)

        except Exception as e:
            logger.error(f"Erreur Report Engine : {e}")
            return "## Erreur lors de la génération du rapport."

    # ----------------------------------------------------------------- helpers

    def _fmt_teeth_phrase(self, fdis: List[int], prefix: str) -> str:
        """'Absence de la dent 16' / 'Absence des dents 16, 26 et 36'."""
        if not fdis:
            return prefix
        if len(fdis) == 1:
            return f"{prefix} de la dent {fdis[0]}"
        body = ", ".join(str(f) for f in fdis[:-1])
        return f"{prefix} des dents {body} et {fdis[-1]}"

    def _teeth_list(self, fdis: List[int]) -> str:
        if len(fdis) == 1:
            return f"la dent {fdis[0]}"
        if len(fdis) == 2:
            return f"les dents {fdis[0]} et {fdis[1]}"
        return f"les dents {', '.join(str(f) for f in fdis[:-1])} et {fdis[-1]}"

    def _phrase_for(self, aid: str, fdis: List[int]) -> str:
        """Phrase clinique professionnelle pour une anomalie donnée."""
        t = self._teeth_list(fdis)
        templates = {
            'carie_email': f"Lésion carieuse débutante de l'émail sur {t}.",
            'carie_dentinaire': f"Lésion carieuse dentinaire sur {t}.",
            'carie_profonde': f"Carie profonde avec atteinte pulpaire probable sur {t}.",
            'reprise_carie': f"Reprise carieuse sous obturation sur {t}.",
            'obturation_comp': f"Obturation coronaire en place sur {t}.",
            'obturation_debord': f"Obturation débordante à reprendre sur {t}.",
            'lesion_periapicale': f"Image périapicale radio-claire (lésion/granulome) sur {t}.",
            'elargissement_desmo': f"Élargissement de l'espace desmodontal sur {t}.",
            'tr_adequat': f"Traitement endodontique d'aspect satisfaisant sur {t}.",
            'tr_incomplet': f"Traitement endodontique incomplet sur {t}.",
            'depassement_pate': f"Dépassement de pâte canalaire sur {t}.",
            'instrument_fracture': f"Instrument endodontique fracturé sur {t}.",
            'perforation': f"Image de perforation radiculaire (faux-canal) sur {t}.",
            'alveolyse_h': f"Alvéolyse horizontale localisée au niveau de {t}.",
            'alveolyse_v': f"Alvéolyse verticale (défaut angulaire) au niveau de {t}.",
            'furcation': f"Atteinte de la furcation sur {t}.",
            'tartre': f"Dépôts de tartre sous-gingival au niveau de {t}.",
            'surnumeraire': f"Dent surnuméraire au niveau de {t}.",
            'incluse': f"Dent incluse : {t}.",
            'enclavee': f"Dent enclavée : {t}.",
            'reste_radiculaire': f"Reste radiculaire à avulser : {t}.",
            'resorption': f"Résorption radiculaire sur {t}.",
            'couronne': f"Couronne prothétique en place sur {t}.",
            'bridge': f"Bridge prothétique sur {t}.",
            'implant': f"Implant dentaire en place sur {t}.",
            'appareil': f"Appareil / prothèse amovible au niveau de {t}.",
            'peri_implantite': f"Image de péri-implantite sur {t}.",
            'infiltration_prothese': f"Infiltration sous prothèse sur {t}.",
            'opacite_sinus': f"Opacité du sinus maxillaire en regard de {t}.",
            'racine_sinus': f"Racine au contact du plancher sinusien : {t}.",
            'condyle_asymetrie': f"Asymétrie condylienne objectivée.",
            'arthrose_atm': f"Remaniements arthrosiques de l'ATM.",
            'calcification': f"Calcification des parties molles en regard de {t}.",
        }
        return templates.get(aid, f"{ANOMALY_LABELS.get(aid, aid)} sur {t}.")

    def _append_normality(self, lines: List[str], anomaly_map: Dict[str, List[int]], global_findings: List[str]):
        aids = set(anomaly_map.keys())
        gids = set(global_findings)

        has_sinus = bool(aids & {'opacite_sinus', 'racine_sinus'})
        has_bone = bool(aids & {'alveolyse_h', 'alveolyse_v', 'lesion_periapicale', 'resorption', 'furcation'}) \
            or bool(gids & {'alveolyse_gen_legere', 'alveolyse_gen_moderee', 'alveolyse_gen_severe', 'parodontite_gen'})
        has_atm = bool(aids & {'condyle_asymetrie', 'arthrose_atm'})

        if not has_sinus:
            lines.append("- Transparence normale des cuvettes sinusiennes maxillaires.")
        lines.append("- Cloison nasale médiane.")

        if not has_bone and not has_atm:
            lines.append("- Absence de lésion osseuse d'allure suspecte ; articulations temporo-mandibulaires respectées.")
        elif not has_atm:
            lines.append("- Articulations temporo-mandibulaires respectées.")

    def _build_synthesis(self, anomaly_map, absent_teeth, global_findings) -> str:
        aids = anomaly_map
        sentences: List[str] = []

        carie_keys = [k for k in aids if k.startswith('carie') or k == 'reprise_carie']
        nb_caries = sum(len(aids[k]) for k in carie_keys)
        urgent = [k for k in aids if k in URGENT_KEYS]
        prostheses = [k for k in ('couronne', 'bridge', 'implant', 'appareil') if k in aids]
        endo = [k for k in ('tr_adequat', 'tr_incomplet') if k in aids]
        gen_lysis = [g for g in global_findings if g.startswith('alveolyse_gen') or g == 'parodontite_gen']

        if nb_caries:
            sentences.append(f"Bilan carieux : {nb_caries} site(s) carieux objectivé(s)")
        if urgent:
            labels = ", ".join(sorted({ANOMALY_LABELS.get(k, k) for k in urgent}))
            sentences.append(f"⚠️ Foyer(s) nécessitant une prise en charge prioritaire ({labels})")
        if absent_teeth:
            sentences.append(f"Édentement de {len(absent_teeth)} dent(s) à réhabiliter")
        if prostheses:
            labels = ", ".join(ANOMALY_LABELS.get(k, k).lower() for k in prostheses)
            sentences.append(f"Réhabilitations existantes : {labels}")
        if endo:
            sentences.append("Présence de traitements endodontiques (à recontrôler)")
        if gen_lysis:
            sentences.append("Contexte parodontal généralisé à surveiller")

        if not sentences:
            return ("Examen panoramique sans anomalie dentaire ou osseuse significative décelée. "
                    "Structures osseuses, sinusiennes et articulaires d'aspect normal.")

        return ". ".join(sentences) + "."

    def _build_recommendations(self, anomaly_map, absent_teeth) -> List[str]:
        recos: List[str] = []
        seen = set()
        # Recommandations par anomalie présente
        for aid in anomaly_map:
            if aid in CCAM_SUGGESTIONS and aid not in seen:
                recos.append(CCAM_SUGGESTIONS[aid])
                seen.add(aid)
        if absent_teeth and 'dent_absente' not in seen:
            recos.append(CCAM_SUGGESTIONS['dent_absente'])
        return recos


panoramic_report_engine = PanoramicReportEngine()
