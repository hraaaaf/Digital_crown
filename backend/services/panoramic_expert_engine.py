import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class PanoramicExpertEngine:
    """
    Système Expert Déterministe pour Bilan Panoramique (Zero-LLM).
    Remplace l'Intelligence Artificielle générative par un arbre décisionnel clinique strict.
    Garantit 100% de reproductibilité, 0 hallucination, et une exécution locale instantanée.
    """
    
    def __init__(self):
        # Arbre de nomenclature clinique (Modèle 31 classes)
        self.categories = {
            # A. Pathologies Dentaires et Parodontales
            "Caries": {"fr": "Atteinte carieuse", "group": "Pathologies Dentaires"},
            "Deep Caries": {"fr": "Carie profonde avec risque de proximité pulpaire", "group": "Pathologies Dentaires"},
            "Periapical lesion": {"fr": "Image radioclaire périapicale (suspicion de kyste/granulome)", "group": "Pathologies Dentaires"},
            "impacted tooth": {"fr": "Dent incluse/enclavée", "group": "Positionnement"},
            "Impacted": {"fr": "Dent incluse/enclavée", "group": "Positionnement"},
            "Missing teeth": {"fr": "Agénésie ou dent manquante", "group": "Positionnement"},
            "Malaligned": {"fr": "Malposition dentaire / Version", "group": "Positionnement"},
            "Supra Eruption": {"fr": "Égression / Sur-éruption", "group": "Positionnement"},
            "Bone Loss": {"fr": "Perte osseuse parodontale (Alvéolyse)", "group": "Parodonte"},
            "bone defect": {"fr": "Défaut osseux angulaire", "group": "Parodonte"},
            "attrition": {"fr": "Usure dentaire / Attrition", "group": "Pathologies Dentaires"},
            "Fracture teeth": {"fr": "Fracture coronaire ou radiculaire", "group": "Pathologies Dentaires"},
            "Root resorption": {"fr": "Résorption radiculaire", "group": "Pathologies Dentaires"},
            "Retained root": {"fr": "Reste radiculaire", "group": "Pathologies Dentaires"},
            "Root Piece": {"fr": "Fragment apical ou radiculaire", "group": "Pathologies Dentaires"},
            "Cyst": {"fr": "Lésion kystique maxillo-mandibulaire", "group": "Pathologies Dentaires"},

            # B. Actes Iatrogènes et Restaurations Existantes
            "Filling": {"fr": "Restauration coronaire (Composite/Amalgame)", "group": "Restaurations"},
            "Root Canal Treatment": {"fr": "Traitement endodontique", "group": "Endodontie"},
            "post - core": {"fr": "Inlay-core ou tenon radiculaire", "group": "Endodontie"},
            "Crown": {"fr": "Restauration prothétique périphérique (Couronne/Bridge)", "group": "Prothèses"},
            "Implant": {"fr": "Implant dentaire", "group": "Implantologie"},
            "abutment": {"fr": "Pilier implantaire", "group": "Implantologie"},
            "gingival former": {"fr": "Vis de cicatrisation", "group": "Implantologie"},
            
            # Orthodontie et Chirurgie
            "TAD": {"fr": "Mini-vis d'ancrage orthodontique (TAD)", "group": "Orthodontie"},
            "orthodontic brackets": {"fr": "Attaches orthodontiques (Brackets)", "group": "Orthodontie"},
            "metal band": {"fr": "Bague orthodontique", "group": "Orthodontie"},
            "permanent retainer": {"fr": "Fil de contention", "group": "Orthodontie"},
            "wire": {"fr": "Arc orthodontique", "group": "Orthodontie"},
            "plating": {"fr": "Matériel d'ostéosynthèse (Plaque/Vis)", "group": "Chirurgie"},

            # C. Structures Osseuses et Articulaires
            "Mandibular Canal": {"fr": "Proximité avec le canal alvéolaire inférieur", "group": "Nerf"},
            "maxillary sinus": {"fr": "Visualisation du plancher sinusal", "group": "Sinus"},
            
            # Classes génériques / Anatomiques
            "Permanent Teeth": {"fr": "Dentition permanente", "group": "Autre"},
            "Primary teeth": {"fr": "Dentition lactéale", "group": "Autre"}
        }

    def _build_clinical_phrase(self, detection: Dict) -> str:
        """Génère la phrase clinique pour une détection donnée."""
        path_key = detection.get("pathology", "")
        tooth = detection.get("tooth")
        confidence = detection.get("confidence", 0) * 100
        
        info = self.categories.get(path_key, {"fr": path_key, "group": "Autre"})
        phrase = info["fr"]
        
        # Injection du numéro de dent si applicable
        if tooth and tooth > 0:
            return f"**Au niveau de la dent {tooth}** : {phrase}."
        else:
            return f"**Observation générale** : {phrase}."

    def generate_report(self, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Construit un rapport médical structuré via l'arbre décisionnel.
        """
        if not detections:
            return {
                "summary": "Examen radiologique dans les limites de la normale.",
                "narrative": "L'analyse algorithmique n'a détecté aucune anomalie radiologique ou pathologie évidente sur les structures dentaires, parodontales, osseuses et articulaires.",
                "findings_count": 0,
                "severity": "LOW"
            }

        # 1. Tri par groupes cliniques
        grouped_findings = {
            "Pathologies Dentaires & Positionnement": [],
            "État Parodontal": [],
            "Iatrogénie & Restaurations": [],
            "Structures Osseuses, Sinus & ATM": []
        }

        for det in detections:
            path = det.get("pathology", "")
            cat_info = self.categories.get(path)
            if not cat_info: continue
            
            group = cat_info["group"]
            phrase = self._build_clinical_phrase(det)
            
            if group in ["Pathologies Dentaires", "Positionnement", "Endodontie"]:
                grouped_findings["Pathologies Dentaires & Positionnement"].append(phrase)
            elif group in ["Parodonte"]:
                grouped_findings["État Parodontal"].append(phrase)
            elif group in ["Restaurations", "Prothèses", "Implantologie"]:
                grouped_findings["Iatrogénie & Restaurations"].append(phrase)
            elif group in ["Osseux", "Sinus", "ATM", "Nerf"]:
                grouped_findings["Structures Osseuses, Sinus & ATM"].append(phrase)

        # 2. Rédaction du rapport formel (Zéro-LLM)
        narrative_lines = ["## Compte-rendu Radiologique Panoramique\n"]
        
        for section_title, findings in grouped_findings.items():
            if findings:
                narrative_lines.append(f"### {section_title}")
                for finding in findings:
                    narrative_lines.append(f"- {finding}")
                narrative_lines.append("")

        findings_count = len(detections)
        summary = f"Analyse terminée : {findings_count} éléments cliniques mis en évidence."
        
        # Arbre de décision pour la conclusion et la sévérité
        severity = "LOW"
        conclusions = []
        
        if len(grouped_findings["Pathologies Dentaires & Positionnement"]) > 0:
            severity = "MEDIUM"
            conclusions.append("Des lésions ou atypies dentaires nécessitent un examen clinique intra-oral et d'éventuels clichés rétro-alvéolaires.")
            
        if any(d.get("pathology") in ["Carie Profonde", "Lésion Périapicale", "Proximité Nerf", "Lésion Osseuse"] for d in detections):
            severity = "HIGH"
            conclusions.append("⚠️ **Attention requise** : Présence d'atteintes sévères (risque pulpaire, infectieux, ou anatomique). Prise en charge prioritaire recommandée.")

        if not conclusions:
            conclusions.append("Bilan de routine. Corrélation clinique recommandée.")

        narrative_lines.append("### Conclusion & Stratégie")
        for conc in conclusions:
            narrative_lines.append(f"- {conc}")

        return {
            "summary": summary,
            "narrative": "\n".join(narrative_lines),
            "findings_count": findings_count,
            "severity": severity
        }

# Singleton
panoramic_expert_engine = PanoramicExpertEngine()
