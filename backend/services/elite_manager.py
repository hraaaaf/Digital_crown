import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from sqlalchemy import func
from backend import models, schemas
from backend.services.clinical_intelligence import clinical_intel
from backend.services.clinical_coherence import coherence_service
from backend.services.ai_advisor import ai_advisor
from backend.services.prescription_service import prescription_service
from backend.services.habits_engine import habits_engine
from backend.services.treatment_plan_engine import treatment_plan_engine
from backend.services.rag_context import build_patient_rag_context

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

            # 1b. Enrichissement RAG — contexte historique patient
            rag_ctx = build_patient_rag_context(patient_id, db)

            # 2. Audit de cohérence déterministe.
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
                        "type": "suggestion",
                        "title": "Repérage Panoramique",
                        "content": f"{len(detections)} repère(s) dentaire(s) automatique(s) disponible(s) sur la panoramique. Aucune anomalie n'est conclue automatiquement.",
                        "actionLabel": "Consulter le bilan",
                        "source_type": "DETERMINISTIC",
                        "trust_level": 1.0
                    })
            
            # --- RAG-BASED INSIGHTS (historique 24 mois) ---
            if rag_ctx.get("acts_count_24m", 0) >= 5:
                insights.append({
                    "id": f"rag_history_{patient_id}",
                    "type": "suggestion",
                    "title": "Historique Clinique Enrichi",
                    "content": f"{rag_ctx['acts_count_24m']} actes sur 24 mois. Tendance céphalométrique : {rag_ctx.get('cephalo_trend', 'N/A')}.",
                    "actionLabel": "Voir le dossier",
                    "source_type": "DETERMINISTIC",
                    "trust_level": 0.95,
                })
            pano_landmarks = rag_ctx.get("panoramic_landmarks", [])
            if pano_landmarks:
                insights.append({
                    "id": f"rag_pano_{patient_id}",
                    "type": "suggestion",
                    "title": "Repérages Panoramiques Récents",
                    "content": "Repères dentaires automatiques récents : " + ", ".join(pano_landmarks[:3]) + ". Aucune anomalie n'est conclue automatiquement.",
                    "source_type": "DETERMINISTIC",
                    "trust_level": 1.0,
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
            
            # --- MPL : PRÉDICTION STOCK PAR ANTICIPATION (Tips Confrère) ---
            if doctor_id:
                stock_insights = self._get_predictive_stock_insights(db, doctor_id)
                insights.extend(stock_insights)

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

            # --- VIGILANCE FINANCIERE ACTIVE (Phase C) ---
            total_acts = db.query(func.sum(models.Acte.montant)).filter(models.Acte.patient_id == patient_id).scalar() or 0.0
            total_payments = db.query(func.sum(models.Payment.amount)).filter(models.Payment.patient_id == patient_id).scalar() or 0.0
            solde_impaye = max(0.0, total_acts - total_payments)
            
            if solde_impaye >= 1000.0:
                insights.append({
                    "id": f"financial_alert_{datetime.now().timestamp()}",
                    "type": "financial_risk",
                    "title": "Vigilance Trésorerie",
                    "content": f"Reste à payer critique de {solde_impaye:,.2f} MAD sur les actes réalisés.",
                    "actionLabel": "Consulter le solde",
                    "source_type": "DETERMINISTIC",
                    "trust_level": 1.0
                })
            elif solde_impaye > 0.0:
                insights.append({
                    "id": f"financial_alert_{datetime.now().timestamp()}",
                    "type": "financial",
                    "title": "Solde Patient",
                    "content": f"Solde débiteur restant : {solde_impaye:,.2f} MAD.",
                    "actionLabel": "Détails paiements",
                    "source_type": "DETERMINISTIC",
                    "trust_level": 1.0
                })

            # Aucun score global : les dimensions clinique, documentaire et financière restent séparées.
            intel_score = None

            # 5. Apprentissage Heuristique (Pondération et Filtrage selon historique)
            if doctor_id:
                insights = self._apply_heuristic_learning(db, insights, doctor_id)

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
                "intelligence_score": None,
                "insights": []
            }

    def _apply_heuristic_learning(self, db: Session, insights: List[Dict], employer_id: int) -> List[Dict]:
        """
        Ajuste le niveau de confiance et filtre les insights (Pilier 2 - Apprentissage Heuristique).
        Basé sur l'historique des feedbacks (accept/reject) pour cet employeur.
        """
        try:
            feedbacks = db.query(
                models.AIFeedback.insight_type, 
                models.AIFeedback.action, 
                func.count(models.AIFeedback.id)
            ).filter(
                models.AIFeedback.employer_id == employer_id
            ).group_by(models.AIFeedback.insight_type, models.AIFeedback.action).all()

            stats = {}
            for row in feedbacks:
                itype, action, count = row[0], row[1], row[2]
                if itype not in stats:
                    stats[itype] = {"accept": 0, "reject": 0}
                if action in ["accept", "reject"]:
                    stats[itype][action] += count

            filtered_insights = []
            for insight in insights:
                itype = insight.get("type", "suggestion")
                # Ignorer les alertes vitales ou financières pour le filtrage
                if itype in ["financial_risk", "safety"]:
                    filtered_insights.append(insight)
                    continue

                if itype in stats:
                    total = stats[itype]["accept"] + stats[itype]["reject"]
                    if total >= 3:
                        reject_rate = stats[itype]["reject"] / total
                        if reject_rate > 0.8:
                            # Heuristique : Si rejeté > 80% du temps (min 3 fois), on masque l'alerte
                            continue
                        
                        current_trust = insight.get("trust_level", 1.0)
                        penalty = reject_rate * 0.4
                        insight["trust_level"] = round(max(0.1, current_trust - penalty), 2)
                
                filtered_insights.append(insight)
            return filtered_insights
        except Exception as e:
            logger.error(f"Heuristic Learning Error: {e}")
            return insights

    def _calculate_intelligence_score(self, db: Session, patient_id: int, summary: Dict, insights: List, solde_impaye: float = 0.0) -> int:
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

        # Pénalité de solvabilité
        if solde_impaye >= 1000.0:
            score -= 15
        
        return min(100, max(0, score))

    async def _get_predictive_insights(self, db: Session, patient_id: int) -> List[Dict[str, Any]]:
        """
        Analyse les lacunes documentaires basées sur les derniers actes.
        """
        insights = []
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 1. Récupérer les actes du jour (Optimisé)
        today_acts = db.query(models.Acte).filter(
            models.Acte.patient_id == patient_id,
            models.Acte.date_debut >= today_start
        ).all()
        
        # 2. Récupérer les types de documents archivés aujourd'hui (Optimisé, évite de charger les fichiers)
        today_docs = db.query(models.DocumentArchive.document_type).filter(
            models.DocumentArchive.patient_id == patient_id,
            models.DocumentArchive.created_at >= today_start
        ).all()
        doc_types = [d[0] for d in today_docs]
        
        # 3. Corrélation Actes du Jour -> Besoins Immédiats
        if today_acts:
            for acte in today_acts:
                libelle = acte.libelle.lower()
                context_keys = [trigger for trigger in PREDICTIVE_MAP.keys() if trigger in libelle]
                
                for trigger in context_keys:
                    for s in PREDICTIVE_MAP[trigger]:
                        if s not in doc_types:
                            insights.append({
                                "id": f"predictive_{trigger}_{s}_{now.timestamp()}",
                                "type": "suggestion",
                                "title": "Besoin Documentaire",
                                "content": f"Un acte de '{trigger.upper()}' a été détecté. Souhaitez-vous générer le document : {s.replace('_', ' ')} ?",
                                "actionLabel": f"Générer {s}",
                                "source_type": "DETERMINISTIC",
                                "trust_level": 0.95
                            })
        
        # 4. Mémoire Hub : Corrélation Temporelle (Devis vs Actes)
        pending_quotes = db.query(models.DocumentArchive).filter(
            models.DocumentArchive.patient_id == patient_id,
            models.DocumentArchive.document_type == "DEVIS",
            models.DocumentArchive.status == "ACTIF"
        ).all()

        for quote in pending_quotes:
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

        # 5. Les labels panoramiques automatiques, y compris les labels historiques,
        # ne deviennent jamais un diagnostic clinique ni une suggestion de facturation.

        return insights

    def _get_predictive_stock_insights(self, db: Session, doctor_id: int) -> List[Dict[str, Any]]:
        """
        Analyse l'agenda de la semaine à venir pour suggérer proactivement de vérifier les stocks requis.
        """
        insights = []
        try:
            today = datetime.now()
            one_week_later = today + timedelta(days=7)
            
            # Récupérer les rendez-vous de la semaine
            appointments = db.query(models.Appointment).filter(
                models.Appointment.employer_id == doctor_id,
                models.Appointment.datetime_start >= today,
                models.Appointment.datetime_start <= one_week_later,
                models.Appointment.status != models.AppointmentStatus.ANNULE
            ).all()
            
            # Comptage des catégories d'actes
            counts = {
                "endo": 0,
                "composite": 0,
                "implant": 0,
                "chirurgie": 0
            }
            
            for app in appointments:
                motif = (app.motif or "").lower()
                notes = (app.notes or "").lower()
                text = f"{motif} {notes}"
                
                if any(x in text for x in ["canalaire", "endo", "racine", "dévitalisation"]):
                    counts["endo"] += 1
                elif any(x in text for x in ["composite", "soin", "plombage", "restauration", "carie"]):
                    counts["composite"] += 1
                elif "implant" in text:
                    counts["implant"] += 1
                elif any(x in text for x in ["extraction", "avulsion", "sagesse", "chirurgie"]):
                    counts["chirurgie"] += 1
            
            # Génération des insights proactifs (tips de confrère dentiste)
            if counts["endo"] > 1:
                insights.append({
                    "id": f"stock_endo_{today.timestamp()}",
                    "type": "suggestion",
                    "title": "Tips Confrère : Stock Endo",
                    "content": f"Cher confrère, je vois que tu prévois {counts['endo']} traitements canalaires cette semaine. Pense à vérifier ton stock de limes rotatives (ProTaper, WaveOne) et de pointes de papier absorbantes.",
                    "actionLabel": "Vérifier le stock",
                    "source_type": "DETERMINISTIC",
                    "trust_level": 0.95
                })
            
            if counts["composite"] > 1:
                insights.append({
                    "id": f"stock_composite_{today.timestamp()}",
                    "type": "suggestion",
                    "title": "Tips Confrère : Stock Soins",
                    "content": f"Pour info, {counts['composite']} soins composites sont programmés cette semaine. Assure-toi d'avoir un niveau suffisant de seringues de composite (teintes A2, A3) et d'adhésif universel (bonding).",
                    "actionLabel": "Consulter le stock",
                    "source_type": "DETERMINISTIC",
                    "trust_level": 0.95
                })
                
            if counts["implant"] > 0:
                insights.append({
                    "id": f"stock_implant_{today.timestamp()}",
                    "type": "suggestion",
                    "title": "Tips Confrère : Chirurgie Implant",
                    "content": f"Alerte chirurgicale : {counts['implant']} pose(s) d'implants de prévue(s). Valide bien la présence des diamètres requis, des vis de cicatrisation adaptées et des piliers de transfert dans ton tiroir.",
                    "actionLabel": "Checklist Implant",
                    "source_type": "DETERMINISTIC",
                    "trust_level": 0.95
                })
                
            if counts["chirurgie"] > 1:
                insights.append({
                    "id": f"stock_chirurgie_{today.timestamp()}",
                    "type": "suggestion",
                    "title": "Tips Confrère : Logistique Chir",
                    "content": f"Avec {counts['chirurgie']} chirurgies/extractions à venir, vérifie ton approvisionnement en fils de suture (résorbables 4-0/5-0) et en carpules d'anesthésique à l'articaïne.",
                    "actionLabel": "Checklist Chirurgie",
                    "source_type": "DETERMINISTIC",
                    "trust_level": 0.95
                })
                
        except Exception as e:
            logger.error(f"Error generating stock insights: {e}")
            
        return insights

    async def get_treatment_plan(self, db: Session, patient_id: int) -> Dict[str, Any]:
        """La génération automatique d'un plan clinique est désactivée en P0 fail-closed."""
        return {
            "error": "Génération automatique du plan de traitement désactivée. Validation clinique du praticien requise.",
            "patient_id": patient_id,
        }

# Instance unique
elite_manager = EliteManager()
