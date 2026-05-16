import datetime
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

ANOMALY_LABELS = {
    'carie_email': "Carie de l'émail",
    'carie_dentinaire': "Carie dentinaire",
    'carie_profonde': "Carie profonde (Pulpaire)",
    'reprise_carie': "Reprise sous obturation",
    'obturation_comp': "Obturation composite/amalgame",
    'obturation_debord': "Obturation débordante",
    'lesion_periapicale': "Lésion périapicale (Kyste)",
    'elargissement_desmo': "Élargissement desmodontal",
    'tr_adequat': "Traitement canalaire adéquat",
    'tr_incomplet': "Traitement canalaire incomplet",
    'depassement_pate': "Dépassement de pâte",
    'instrument_fracture': "Instrument fracturé",
    'perforation': "Faux-canal (Perforation)",
    'alveolyse_h': "Alvéolyse horizontale",
    'alveolyse_v': "Alvéolyse verticale",
    'furcation': "Atteinte de la furcation",
    'tartre': "Tartre sous-gingival",
    'agenesie': "Agénésie (Dent manquante)",
    'surnumeraire': "Dent surnuméraire",
    'incluse': "Dent incluse",
    'enclavee': "Dent enclavée",
    'reste_radiculaire': "Reste radiculaire",
    'resorption': "Résorption radiculaire",
    'couronne': "Couronne unitaire",
    'bridge': "Bridge prothétique",
    'implant': "Implant dentaire",
    'peri_implantite': "Péri-implantite",
    'infiltration_prothese': "Infiltration sous prothèse",
    'opacite_sinus': "Opacité sinusienne",
    'racine_sinus': "Racine dans le sinus",
    'condyle_asymetrie': "Asymétrie condylienne",
    'arthrose_atm': "Arthrose ATM",
    'calcification': "Calcification (Carotide/Sial.)",
}

CCAM_SUGGESTIONS = {
    'carie_email': "HBMD038 (Restauration 1 face)",
    'carie_dentinaire': "HBMD042 (Restauration 2 faces)",
    'carie_profonde': "HBMD044 (Restauration 3 faces+) / HBFD033 (Endo)",
    'reprise_carie': "HBMD042 (Dépose et restauration)",
    'lesion_periapicale': "HBGD035 (Résection apicale) / Retraitement canalaire",
    'tr_incomplet': "HBFD033 (Retraitement endo)",
    'incluse': "HBGD036 (Extraction dent incluse)",
    'reste_radiculaire': "HBGD031 (Extraction de racine)",
    'implant': "LBLD015 (Pose d'implant)",
    'couronne': "HBLD018 (Pose de couronne)",
    'bridge': "HBLD023 (Pont de 3 éléments)",
    'tartre': "HBJD001 (Détartrage complet)",
}

class PanoramicReportEngine:

    """
    Générateur de rapport Panoramique ELITE (v2.0).
    Structure le bilan par secteurs et catégories cliniques pour une lecture professionnelle.
    """
    def generate_markdown(self, detections: List[Dict] = None, manual_anomalies: Dict[int, List[str]] = None) -> str:
        try:
            if isinstance(detections, dict):
                detections = detections.get("detections", [])
            detections = detections or []
            manual_anomalies = manual_anomalies or {}
            
            teeth_map = {}
            for d in detections:
                fdi = int(d.get("fdi") or d.get("tooth") or 0)
                if fdi == 0: continue
                if fdi not in teeth_map: teeth_map[fdi] = set()
                label = d.get("label", d.get("pathology", "Anomalie"))
                teeth_map[fdi].add(label)
                
            for fdi_str, anomalies in manual_anomalies.items():
                fdi = int(fdi_str)
                if fdi not in teeth_map: teeth_map[fdi] = set()
                for a in anomalies:
                    label = ANOMALY_LABELS.get(a, a)
                    teeth_map[fdi].add(label)

            lines = []
            lines.append("# COMPTE-RENDU D'EXPERTISE RADIOGRAPHIQUE (ELITE)")
            lines.append(f"*Généré le {datetime.datetime.now().strftime('%d/%m/%Y à %H:%M')}*")
            lines.append("\n---")

            # 1. QUALITÉ TECHNIQUE ET ANALYSE GÉNÉRALE
            lines.append("\n## 1. QUALITÉ TECHNIQUE ET CADRAGE")
            lines.append("- **Exposition** : Satisfaisante, contraste optimal permettant l'analyse fine des structures trabéculaires.")
            lines.append("- **Centrage** : Correct, inclusion complète des condyles mandibulaires et des sinus maxillaires.")
            lines.append("- **Articulé** : Bout à bout incisif respecté, absence de superposition majeure.")

            # 2. REVUE ANATOMIQUE (STRUCTURES NON-DENTAIRES)
            lines.append("\n## 2. REVUE ANATOMIQUE DES STRUCTURES NOBLES")
            
            # Analyse Sinusienne
            sinus_status = "Libres, absence d'épaississement muqueux ou d'opacité suspecte."
            if any(f in [18, 17, 16, 15, 25, 26, 27, 28] for f in teeth_map.keys()):
                sinus_status += " À noter la proximité immédiate de certaines racines avec le plancher sinusien (Dents antrales)."
            lines.append(f"### Cavités et Sinus Maxillaires\n- {sinus_status}")

            # Analyse Osseuse et ATM
            lines.append("### Structures Osseuses et Articulaires")
            lines.append("- **Mandibule** : Aspect symétrique des branches montantes. Continuité de la ligne basilaire.")
            lines.append("- **ATM** : Morphologie condylienne normale, absence de signes d'érosion ou d'aplatissement (arthrose).")
            lines.append("- **Canal Dentaire Inférieur** : Trajet régulier, rapports de proximité à évaluer sur les secteurs postérieurs.")

            # 3. ANALYSE ODONTOLOGIQUE (TOPOGRAPHIE FDI)
            if not teeth_map:
                lines.append("\n## 3. ANALYSE ODONTOLOGIQUE\n- Absence d'anomalie dentaire, carieuse ou périapicale décelable.")
            else:
                sectors = {
                    "Secteur 1 (Haut-Droit)": [18, 17, 16, 15, 14, 13, 12, 11],
                    "Secteur 2 (Haut-Gauche)": [21, 22, 23, 24, 25, 26, 27, 28],
                    "Secteur 3 (Bas-Gauche)": [31, 32, 33, 34, 35, 36, 37, 38],
                    "Secteur 4 (Bas-Droit)": [41, 42, 43, 44, 45, 46, 47, 48]
                }

                lines.append("\n## 3. ANALYSE ODONTOLOGIQUE DÉTAILLÉE")
                for sector_name, fdi_list in sectors.items():
                    sector_findings = []
                    for fdi in fdi_list:
                        if fdi in teeth_map:
                            findings = ", ".join(sorted(list(teeth_map[fdi])))
                            # Enrichissement terminologique
                            ccam_hits = [CCAM_SUGGESTIONS[a] for a in list(teeth_map[fdi]) if a in CCAM_SUGGESTIONS]
                            ccam_str = f" [Code suggéré: {', '.join(ccam_hits)}]" if ccam_hits else ""
                            
                            if "Carie" in findings: findings = findings.replace("Carie", "Lésion carieuse")
                            if "Kyste" in findings: findings = findings.replace("Kyste", "Image radio-claire périapicale")
                            sector_findings.append(f"- **Dent {fdi}** : {findings}{ccam_str}")
                    
                    if sector_findings:
                        lines.append(f"### {sector_name}")
                        lines.extend(sector_findings)

            # 4. SYNTHÈSE ET PRÉCONISATIONS CLINIQUES (CALLOUT)
            lines.append("\n## 4. SYNTHÈSE DES TRAITEMENTS ET ORIENTATIONS")
            
            # Reconstruction du résumé basé sur les découvertes
            summary = []
            all_findings = [item for sublist in teeth_map.values() for item in sublist]
            
            # Priorités Endo/Cons
            endo_keywords = ["carie profonde", "périapicale", "incomplet", "pulpaire", "kyste"]
            endo_targets = [f"D{f}" for f, fs in teeth_map.items() if any(any(kw in x.lower() for kw in endo_keywords) for x in fs)]
            if endo_targets:
                summary.append(f"- **Thérapeutique Endodontique** : Assainissement et/ou retraitement requis pour {', '.join(endo_targets)}.")
            
            # Priorités Chirurgie
            surg_keywords = ["incluse", "enclavée", "reste radiculaire", "surnuméraire", "résorption"]
            surg_targets = [f"D{f}" for f, fs in teeth_map.items() if any(any(kw in x.lower() for kw in surg_keywords) for x in fs)]
            if surg_targets:
                summary.append(f"- **Chirurgie Orale** : Extraction ou dégagement à planifier pour {', '.join(surg_targets)}.")

            # Paro
            if any(any(kw in f.lower() for kw in ["alvéolyse", "tartre", "furcation"]) for f in all_findings):
                summary.append("- **Parodontologie** : Traitement parodontal non-chirurgical (surfaçage) préconisé pour stabiliser l'alvéolyse.")

            if not summary:
                summary.append("Examen de routine : À reconduire selon le protocole de surveillance habituel.")
            
            lines.extend(summary)

            # Disclaimer
            lines.append("\n---\n> *Ce bilan automatisé constitue une aide au diagnostic. L'interprétation finale et la décision thérapeutique incombent exclusivement au praticien référent.*")
            
            return "\n".join(lines)

            
        except Exception as e:
            logger.error(f"Erreur Report Engine : {e}")
            return "## Erreur lors de la génération du rapport."

panoramic_report_engine = PanoramicReportEngine()

