import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from sqlalchemy import func
from backend import models, schemas
from backend.services.clinical_intelligence import clinical_intel
from backend.services.clinical_coherence import coherence_service
from backend.services.ai_advisor import ai_advisor
from backend.services.prescription_service import prescription_service
from backend.services.habits_engine import habits_engine
from backend.services.treatment_plan_engine import treatment_plan_engine

logger = logging.getLogger(__name__)

# Mappage des actes déclencheurs vers les types de documents suggérés
PREDICTIVE_MAP = {
    "extraction": ["ORDONNANCE", "CERTIFICAT"],
    "chirurgie": ["ORDONNANCE", "CERTIFICAT"],
    "implant": ["ORDONNANCE", "DEVIS"],
    "endo": ["ORDONNANCE"],
    "canalaire": ["ORDONNANCE"],
    "soin": ["NOTE_HONORAIRES"],
    "détartrage": ["NOTE_HONORAIRES"],
    "couronne": ["DEVIS", "NOTE_HONORAIRES"],
    "carie": ["NOTE_HONORAIRES"],
    "pulp": ["ORDONNANCE"],
}
class EliteManager:
    """
    Ghost Unified Intelligence Manager (GUI).
    Service central d'orchestration de l'intelligence clinique et financière.
    """

    async def get_comprehensive_intelligence(
        self, 
        db: Session, 
        patient_id: int, 
        context_type: str = "general",
        doc_data: Optional[Dict[str, Any]] = None,
        doctor_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Récupère une analyse complète (Flash Summary + Audit + Insights).
        """
        try:
            # 1. Résumé Flash (Heuristique rapide)
            summary = clinical_intel.get_patient_summary(db, patient_id)
            
            # 2. Audit de cohérence (Déterministe + IA Sémantique)
            # Si doc_data est fourni, on fait un audit spécifique, sinon audit général du dossier
            warnings = []
            if doc_data:
                warnings = await coherence_service.analyze_coherence(
                    patient_id, context_type, doc_data, db, doctor_id
                )
            
            # 3. Intelligence Prédictive & Habitudes
            insights = []
            
            # --- ANALYSE PRÉDICTIVE (Phase 3) ---
            predictive_insights = await self._get_predictive_insights(db, patient_id)
            insights.extend(predictive_insights)

            # --- INTELLIGENCE PANORAMIQUE (Flash) ---
            latest_pano = db.query(models.PanoramicAnalysis).filter(
                models.PanoramicAnalysis.patient_id == patient_id
            ).order_by(models.PanoramicAnalysis.created_at.desc()).first()

            if latest_pano:
                detections = latest_pano.detections_data.get("detections", [])
                if detections:
                    insights.append({
                        "id": f"pano_detect_{latest_pano.id}",
                        "type": "diagnostic",
                        "title": "Intelligence Panoramique",
                        "content": f"🔬 {len(detections)} anomalies détectées sur la panoramique (IA).",
                        "actionLabel": "Consulter le bilan",
                        "source_type": "DETERMINISTIC",
                        "trust_level": 1.0
                    })
            
            # --- MPL : TRIGGERS PROACTIFS (Habits Engine) ---
            proactive_triggers = habits_engine.check_proactive_triggers(db, patient_id)
            for t in proactive_triggers:
                insights.append({
                    "id": f"trigger_{t['type']}_{datetime.now().timestamp()}",
                    "type": "habit",
                    "title": t['title'],
                    "content": t['message'],
                    "actionLabel": t['action'],
                    "source_type": "DETERMINISTIC",
                    "trust_level": 0.9
                })
            
            # Conversion des warnings en insights standardisés
            for w in warnings:
                insights.append({
                    "id": f"warning_{datetime.now().timestamp()}_{warnings.index(w)}",
                    "type": "safety" if w.get("level") in ["critical", "warning"] else "suggestion",
                    "title": "Alerte Sécurité" if w.get("level") == "critical" else "Suggestion Clinique",
                    "content": w.get("message"),
                    "source_type": "HEURISTIC" if "🤖" in w.get("message", "") else "DETERMINISTIC",
                    "trust_level": 0.95 if "🤖" not in w.get("message", "") else 0.75
                })

            # Ajout automatique d'insights basés sur les antécédents si non déjà couverts
            if summary.get("risk_level") == "high" and not any(i["type"] == "safety" for i in insights):
                for alert in summary.get("alerts", []):
                    insights.append({
                        "id": f"risk_{datetime.now().timestamp()}",
                        "type": "safety",
                        "title": "Vigilance Médicale",
                        "content": alert,
                        "source_type": "DETERMINISTIC",
                        "trust_level": 1.0
                    })

            # 4. Score d'intelligence globale (Simulé pour l'instant basé sur la complétude des données)
            intel_score = self._calculate_intelligence_score(db, patient_id, summary, insights)

            return {
                "patient_summary": summary,
                "insights": insights,
                "intelligence_score": intel_score,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"EliteManager Error: {e}")
            return {
                "error": str(e),
                "intelligence_score": 0,
                "insights": []
            }

    def _calculate_intelligence_score(self, db: Session, patient_id: int, summary: Dict, insights: List) -> int:
        """
        Calcule un score de confiance/complétude (0-100).
        """
        score = 50 # Base
        
        # Complétude du dossier
        patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
        if patient:
            if patient.antecedents_medicaux: score += 10
            if patient.sexe and patient.date_naissance: score += 10
            
        # Présence d'analyses
        cephalo = db.query(models.CephaloAnalysis).filter(models.CephaloAnalysis.patient_id == patient_id).count()
        if cephalo > 0: score += 15
        
        # Présence d'imagerie
        panoramic = db.query(models.PanoramicAnalysis).filter(models.PanoramicAnalysis.patient_id == patient_id).count()
        if panoramic > 0: score += 15
        
        # Pénalité si trop de risques non gérés (théorique)
        critical_count = sum(1 for i in insights if i["type"] == "safety")
        score -= min(20, critical_count * 5)
        
        return min(100, max(0, score))

    async def _get_predictive_insights(self, db: Session, patient_id: int) -> List[Dict[str, Any]]:
        """
        Analyse les lacunes documentaires basées sur les derniers actes.
        """
        insights = []
        today = datetime.now().date()
        
        # 1. Récupérer les actes du jour
        today_acts = db.query(models.Acte).filter(
            models.Acte.patient_id == patient_id,
            func.date(models.Acte.date_debut) == today
        ).all()
        
        if not today_acts:
            return []
            
        # 2. Récupérer les documents archivés aujourd'hui
        today_docs = db.query(models.DocumentArchive).filter(
            models.DocumentArchive.patient_id == patient_id,
            func.date(models.DocumentArchive.created_at) == today
        ).all()
        doc_types = [d.document_type for d in today_docs]
        
        # 3. Corrélation Actes du Jour -> Besoins Immédiats
        for acte in today_acts:
            libelle = acte.libelle.lower()
            context_keys = [trigger for trigger in PREDICTIVE_MAP.keys() if trigger in libelle]
            
            for trigger in context_keys:
                for s in PREDICTIVE_MAP[trigger]:
                    if s not in doc_types:
                        insights.append({
                            "id": f"predictive_{trigger}_{s}_{datetime.now().timestamp()}",
                            "type": "suggestion",
                            "title": "Besoin Documentaire",
                            "content": f"Un acte de '{trigger.upper()}' a été détecté. Souhaitez-vous générer le document : {s.replace('_', ' ')} ?",
                            "actionLabel": f"Générer {s}",
                            "source_type": "DETERMINISTIC",
                            "trust_level": 0.95
                        })
        
        # 4. Mémoire Hub : Corrélation Temporelle (Devis vs Actes)
        # On cherche des devis acceptés qui n'ont pas encore de note d'honoraires associée
        pending_quotes = db.query(models.DocumentArchive).filter(
            models.DocumentArchive.patient_id == patient_id,
            models.DocumentArchive.document_type == "DEVIS",
            models.DocumentArchive.status == "ACCEPTED"
        ).all()

        for quote in pending_quotes:
            # Si le devis est accepté mais qu'aucun acte n'a été facturé aujourd'hui
            if not today_acts:
                insights.append({
                    "id": f"quote_followup_{quote.id}",
                    "type": "habit",
                    "title": "Suivi de Devis",
                    "content": f"Le devis '{quote.file_name}' est accepté. Souhaitez-vous planifier les actes ?",
                    "actionLabel": "Ouvrir Agenda",
                    "source_type": "DETERMINISTIC",
                    "trust_level": 1.0
                })

        # 5. Analyse de l'Odontogramme (Analyses Pano non traitées)
        latest_pano = db.query(models.PanoramicAnalysis).filter(
            models.PanoramicAnalysis.patient_id == patient_id
        ).order_by(models.PanoramicAnalysis.created_at.desc()).first()

        if latest_pano:
            detections = latest_pano.detections_data.get("detections", [])
            for det in detections:
                label = det.get("label", "").lower()
                if "carie" in label and "NOTE_HONORAIRES" not in doc_types:
                    insights.append({
                        "id": f"pano_predict_{det.get('fdi')}",
                        "type": "suggestion",
                        "title": "Opportunité de Soin",
                        "content": f"Lésion carieuse détectée sur la dent {det.get('fdi')} (IA). Souhaitez-vous préparer la note d'honoraires ?",
                        "actionLabel": "Facturer l'acte",
                        "source_type": "HEURISTIC",
                        "trust_level": 0.85
                    })

        return insights

    async def get_treatment_plan(self, db: Session, patient_id: int) -> Dict[str, Any]:
        """
        Génère un plan de traitement basé sur la dernière panoramique.
        """
        latest_pano = db.query(models.PanoramicAnalysis).filter(
            models.PanoramicAnalysis.patient_id == patient_id
        ).order_by(models.PanoramicAnalysis.created_at.desc()).first()

        if not latest_pano:
            return {"error": "Aucune panoramique trouvée pour ce patient."}

        detections = latest_pano.detections_data.get("detections", [])
        plan = treatment_plan_engine.generate_plan(detections)
        plan["patient_id"] = patient_id
        
        return plan

# Instance unique
elite_manager = EliteManager()
