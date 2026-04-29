import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class PanoramicExpertEngine:
    """
    Deterministic Expert System for Dental Panoramic Analysis.
    Translates raw AI detections into structured, clinical French narratives.
    No LLM, 100% Local, 100% Fast.
    """
    
    def __init__(self):
        # Mapping des pathologies DENTEX vers le Français Médical
        self.nomenclature = {
            "Caries": "Carie dentaire",
            "Deep Caries": "Carie profonde avec risque pulpaire",
            "Periapical Lesions": "Lésion périapicale / Abcès",
            "Impacted Teeth": "Dent incluse ou enclavée"
        }
        
        # Définition des quadrants FDI
        self.quadrants = {
            1: "Secteur Supérieur Droit",
            2: "Secteur Supérieur Gauche",
            3: "Secteur Inférieur Gauche",
            4: "Secteur Inférieur Droit"
        }

    def generate_report(self, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyse les détections et produit un rapport structuré par secteur.
        """
        if not detections:
            return {
                "summary": "Examen dans les limites de la normale.",
                "narrative": "L'analyse automatique n'a détecté aucune anomalie radiologique significative sur ce cliché panoramique.",
                "severity": "LOW"
            }

        # 1. Groupement par quadrant
        by_quadrant = {1: [], 2: [], 3: [], 4: []}
        for det in detections:
            tooth = det.get("tooth", 0)
            if 11 <= tooth <= 48:
                quadrant = tooth // 10
                if quadrant in by_quadrant:
                    by_quadrant[quadrant].append(det)

        # 2. Rédaction du rapport narratif
        sections = []
        findings_count = len(detections)
        
        for q_id, q_name in self.quadrants.items():
            q_findings = by_quadrant[q_id]
            if q_findings:
                lines = [f"### {q_name}"]
                for f in q_findings:
                    path_fr = self.nomenclature.get(f["pathology"], f["pathology"])
                    lines.append(f"• **Dent {f['tooth']}** : {path_fr} (Indice de confiance : {f.get('confidence', 0)*100:.0f}%)")
                sections.append("\n".join(lines))

        summary = f"L'IA a identifié {findings_count} point(s) d'attention clinique nécessitant un contrôle visuel."
        narrative = "## Compte-rendu d'Analyse Panoramique\n\n" + summary + "\n\n" + "\n\n".join(sections)
        
        # Ajout d'une recommandation automatique
        narrative += "\n\n### Recommandations :\n- Vérification clinique des zones signalées.\n- Corrélation avec la symptomatologie du patient."

        return {
            "summary": summary,
            "narrative": narrative,
            "findings_count": findings_count,
            "severity": "MEDIUM" if findings_count < 3 else "HIGH"
        }

# Singleton
panoramic_expert_engine = PanoramicExpertEngine()
