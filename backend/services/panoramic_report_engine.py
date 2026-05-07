import datetime
import logging

logger = logging.getLogger(__name__)

class PanoramicReportEngine:
    """
    Générateur de rapport Markdown purement déterministe.
    Remplace les LLM (Ollama/Groq) pour garantir le Zéro-Hallucination (Medico-Legal 100%).
    Consommation RAM: ~0 Mo. Temps d'exécution: < 1ms.
    """
    def generate_markdown(self, analysis_data: dict) -> str:
        try:
            teeth = analysis_data.get("teeth", [])
            general = analysis_data.get("general_findings", [])
            
            lines = []
            lines.append("# Rapport d'Analyse Panoramique Assistée par IA")
            lines.append(f"*Généré automatiquement le {datetime.datetime.now().strftime('%d/%m/%Y à %H:%M')}*")
            lines.append("\n---")
            
            # 1. Bilan Odontologique Détaillé
            lines.append("\n## 1. Bilan Odontologique")
            
            # Filtrer les dents ayant des pathologies/soins (les dents 100% saines sont ignorées pour la clarté)
            teeth_with_findings = [t for t in teeth if len(t.get("findings", [])) > 0]
            
            if not teeth_with_findings:
                lines.append("- *Aucune lésion carieuse, inclusion ou soin antérieur identifié.*")
            else:
                # Tri strict par numéro FDI
                teeth_with_findings.sort(key=lambda x: x["fdi_number"])
                
                for t in teeth_with_findings:
                    fdi = t["fdi_number"]
                    findings = t["findings"]
                    
                    finding_texts = []
                    for f in findings:
                        # Conversion de la probabilité en pourcentage
                        conf = round(f.get("confidence", 0) * 100)
                        label = f.get('label', 'Anomalie')
                        finding_texts.append(f"{label} ({conf}%)")
                    
                    lines.append(f"- **Dent {fdi}** : {', '.join(finding_texts)}")
            
            # 2. Observations Structurelles (Sinus, Os, Kystes)
            lines.append("\n## 2. Observations Structurelles & Anatomiques")
            if general:
                for g in general:
                    conf = round(g.get("confidence", 0) * 100)
                    lines.append(f"- **{g.get('label', 'Élément anatomique')}** détecté avec certitude à {conf}%.")
            else:
                lines.append("- *Aucune anomalie osseuse, parodontale ou kystique majeure isolée.*")
            
            # 3. Disclaimer Médico-Légal
            lines.append("\n---\n")
            lines.append("> ⚠️ **Avis de responsabilité médico-légale**")
            lines.append("> *Ce rapport est généré déterministement par le réseau de neurones convolutifs (CNN) Loki-Silvres V8.*")
            lines.append("> *Il constitue un outil de dépistage visuel (Computer-Aided Detection) et ne remplace en aucun cas l'examen clinique et le jugement souverain du chirurgien-dentiste.*")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération déterministe du rapport : {e}")
            return "## Rapport Indisponible\nErreur lors du traitement des données."

# Instance Singleton prête à être exportée
panoramic_report_engine = PanoramicReportEngine()
