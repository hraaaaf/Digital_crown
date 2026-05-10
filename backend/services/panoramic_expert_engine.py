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
        # Arbre de nomenclature clinique (20+ catégories)
        self.categories = {
            # A. Pathologies Dentaires et Parodontales
            "Carie": {"fr": "Atteinte carieuse", "group": "Pathologies Dentaires"},
            "Carie Profonde": {"fr": "Carie profonde avec risque de proximité pulpaire", "group": "Pathologies Dentaires"},
            "Lésion Périapicale": {"fr": "Image radioclaire périapicale (suspicion de kyste/granulome)", "group": "Pathologies Dentaires"},
            "Dent Incluse": {"fr": "Dent incluse/enclavée", "group": "Positionnement"},
            "Agénésie": {"fr": "Agénésie dentaire", "group": "Positionnement"},
            "Alvéolyse": {"fr": "Perte osseuse parodontale (Alvéolyse)", "group": "Parodonte"},
            "Tartre": {"fr": "Spicules de tartre sous-gingival", "group": "Parodonte"},
            "Élargissement Desmodontal": {"fr": "Élargissement de l'espace desmodontal", "group": "Parodonte"},

            # B. Actes Iatrogènes et Restaurations Existantes
            "Soin Conservateur": {"fr": "Restauration coronaire (Composite/Amalgame)", "group": "Restaurations"},
            "Obturation Endodontique": {"fr": "Traitement endodontique", "group": "Endodontie"},
            "Sous-obturation": {"fr": "Sous-obturation canalaire", "group": "Endodontie"},
            "Couronne": {"fr": "Restauration prothétique périphérique (Couronne/Bridge)", "group": "Prothèses"},
            "Implant": {"fr": "Implant dentaire", "group": "Implantologie"},
            "Péri-implantite": {"fr": "Cratérisation osseuse péri-implantaire", "group": "Implantologie"},

            # C. Structures Osseuses et Articulaires
            "Lésion Osseuse": {"fr": "Lésion ostéolytique/ostéocondensante maxillo-mandibulaire", "group": "Osseux"},
            "Opacité Sinusienne": {"fr": "Opacité du sinus maxillaire", "group": "Sinus"},
            "Dépassement Sinusien": {"fr": "Proximité/Dépassement de matériel dans le sinus", "group": "Sinus"},
            "Asymétrie ATM": {"fr": "Asymétrie ou remaniement condylien (ATM)", "group": "ATM"},
            "Proximité Nerf": {"fr": "Proximité radiculaire avec le canal alvéolaire inférieur", "group": "Nerf"}
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
