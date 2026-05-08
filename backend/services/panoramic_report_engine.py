import datetime
import logging

logger = logging.getLogger(__name__)

class PanoramicReportEngine:
    """
    Générateur de rapport Panoramique ELITE (v1.8).
    Consomme une liste plate de détections et génère un bilan structuré.
    """
    def generate_markdown(self, detections_data: dict) -> str:
        try:
            detections = detections_data.get("detections", [])
            
            lines = []
            lines.append("# Rapport d'Analyse Panoramique Elite IA")
            lines.append(f"*Généré automatiquement le {datetime.datetime.now().strftime('%d/%m/%Y à %H:%M')}*")
            lines.append("\n---")
            
            if not detections:
                lines.append("\n## Bilan Clinique")
                lines.append("- *Aucune anomalie significative détectée sur cet examen.*")
                lines.append("- *L'intégrité des structures osseuses et dentaires semble respectée.*")
            else:
                # Groupement par dent pour un rapport plus lisible
                teeth_map = {}
                for d in detections:
                    fdi = d.get("fdi") or d.get("tooth")
                    if fdi not in teeth_map:
                        teeth_map[fdi] = []
                    teeth_map[fdi].append(d)
                
                lines.append("\n## 1. Anomalies Dentaires Identifiées")
                # Tri par numéro FDI
                sorted_fdi = sorted(teeth_map.keys())
                
                for fdi in sorted_fdi:
                    findings = teeth_map[fdi]
                    finding_texts = []
                    for f in findings:
                        conf = round(f.get("confidence", 0) * 100)
                        label = f.get("label", f.get("pathology", "Anomalie"))
                        finding_texts.append(f"{label} ({conf}%)")
                    
                    lines.append(f"- **Dent {fdi}** : {', '.join(finding_texts)}")
                
            # Disclaimer Médico-Légal
            lines.append("\n---\n")
            lines.append("> ⚠️ **Avis de responsabilité médico-légale**")
            lines.append("> *Ce diagnostic est une assistance à la détection par IA (CAD - Computer-Aided Detection).*")
            lines.append("> *Le chirurgien-dentiste reste seul souverain dans l'interprétation finale et la décision thérapeutique.*")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"Erreur Report Engine : {e}")
            return "## Rapport Indisponible\nErreur lors de la génération du bilan."

panoramic_report_engine = PanoramicReportEngine()
