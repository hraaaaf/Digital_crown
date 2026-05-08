# -*- coding: utf-8 -*-
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.models import Patient, Acte, Medication
from backend.services.ai_coherence import ai_coherence
from backend.services.prescription_service import prescription_service

logger = logging.getLogger(__name__)

class ClinicalCoherenceService:
    """
    Moteur de vigilance clinique pour Digital Crown.
    Analyse la cohérence entre les actes et les prescriptions.
    """
    
    async def analyze_coherence(self, patient_id: int, doc_type: str, doc_data: Dict[str, Any], db: Session, doctor_id: int = None) -> List[Dict[str, Any]]:
        """
        Analyse globale (Déterministe + IA) et retourne une liste d'alertes.
        """
        warnings = []
        
        # 1. Analyse Déterministe (Phase 1)
        if doc_type == "ordonnance":
            warnings.extend(self._check_ordonnance_coherence(patient_id, doc_data, db))
        elif doc_type in ["devis", "note"]:
            warnings.extend(self._check_accounting_coherence(patient_id, doc_data, db))
            
        # 2. Analyse IA Sémantique (Phase 2)
        try:
            patient = db.query(Patient).filter(Patient.id == patient_id).first()
            if patient:
                # Récupération des habitudes du docteur si dispo
                doctor_habits = {}
                if doctor_id:
                    doctor_habits = prescription_service.get_doctor_habits_summary(db, doctor_id)

                # Utilisation de date_debut pour le tri
                recent_acts = db.query(Acte).filter(Acte.patient_id == patient_id).order_by(Acte.date_debut.desc()).limit(10).all()
                act_list = [a.libelle for a in recent_acts]
                
                patient_info = {
                    "age": self._calculate_age(patient.date_naissance) if patient.date_naissance else None,
                    "genre": patient.sexe,
                    "antecedents": patient.antecedents_medicaux,
                    "doctor_habits": doctor_habits
                }
                
                ia_warnings = await ai_coherence.analyze_with_ia(patient_info, doc_type, doc_data, act_list)
                if ia_warnings:
                    logger.info(f"🤖 IA Coherence: {len(ia_warnings)} alertes trouvées.")
                    # Ajouter un marqueur "IA" aux messages pour la transparence UX
                    for w in ia_warnings:
                        w["message"] = f"🤖 {w['message']}"
                    warnings.extend(ia_warnings)
        except Exception as e:
            logger.error(f"Erreur fusion IA Coherence: {e}")
            
        if warnings:
            logger.info(f"🚨 Clinical Coherence: {len(warnings)} alertes totales pour Patient {patient_id}")
            
        return warnings

    def _calculate_age(self, born):
        if not born: return 30
        from datetime import datetime
        today = datetime.now()
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

    def _check_ordonnance_coherence(self, patient_id: int, doc_data: Dict[str, Any], db: Session) -> List[Dict[str, Any]]:
        warnings = []
        medications = doc_data.get("medications", [])
        
        # Détecter si des antibiotiques sont prescrits
        antibiotics = [m for m in medications if self._is_antibiotic(m.get("nom", ""))]
        
        if antibiotics:
            logger.info(f"💊 Antibiotiques détectés: {[a['nom'] for a in antibiotics]}")
            # Vérifier si un acte chirurgical ou endo a été réalisé récemment
            recent_acts = db.query(Acte).filter(
                Acte.patient_id == patient_id
            ).order_by(Acte.date_debut.desc()).limit(5).all()
            
            invasive_acts = [a for a in recent_acts if self._is_invasive_act(a.libelle)]
            
            if not invasive_acts:
                warnings.append({
                    "level": "warning",
                    "message": f"Prescription d'antibiotique ({', '.join([a['nom'] for a in antibiotics])}) sans acte chirurgical récent détecté dans le dossier."
                })
        
        # Vérification des dosages vides
        for med in medications:
            if not med.get("dosage") or med.get("dosage").strip() == "":
                warnings.append({
                    "level": "info",
                    "message": f"Le dosage pour '{med.get('nom')}' est vide. Vérifiez la précision de l'ordonnance."
                })
        
        # 2. Vérification AINS vs Ulcère (Phase 1+)
        has_nsaid = any(self._is_nsaid(m.get("nom", "")) for m in medications)
        if has_nsaid:
            patient = db.query(Patient).filter(Patient.id == patient_id).first()
            if patient and self._is_stomach_risk(patient.antecedents_medicaux):
                warnings.append({
                    "level": "critical",
                    "message": "🚨 Alerte Gastrique : Prescription d'anti-inflammatoire (AINS) détectée chez un patient avec antécédents d'ulcère/gastrite."
                })

        return warnings

    def _check_accounting_coherence(self, patient_id: int, doc_data: Dict[str, Any], db: Session) -> List[Dict[str, Any]]:
        warnings = []
        # Phase 1 : Simple détection de montant à 0
        items = doc_data.get("items", []) or doc_data.get("payments", [])
        for item in items:
            prix = item.get("prix_unitaire", 0) or item.get("montant", 0)
            if float(prix) == 0:
                warnings.append({
                    "level": "info",
                    "message": f"Acte '{item.get('description', item.get('libelle', 'Inconnu'))}' avec montant à 0 MAD. Est-ce un acte gracieux ?"
                })
        return warnings

    def _is_antibiotic(self, name: str) -> bool:
        keywords = [
            "amox", "augmentin", "clamoxyl", "levamox", "curam", "ciblor", 
            "flagyl", "metronidazole", "spiramycine", "bi-rodogyl", "rodogyl", "birodogyl",
            "zithromax", "azithromycine", "josacine", "clindamycine", "dalacine",
            "penicilline", "extencilline", "cefadroxil", "oracefal", "pyostacine"
        ]
        return any(k in name.lower() for k in keywords)

    def _is_nsaid(self, name: str) -> bool:
        """Détecte les Anti-Inflammatoires Non Stéroïdiens (AINS)."""
        keywords = [
            "ibuprofene", "advil", "nurofen", "acigam", "brufen", "nurodol", "agifene", "algantil", "analgyl", "antarene",
            "diclofenac", "voltarene", "diclo pharma", "naproxene", "apranax", "naprosyne", 
            "ketoprofene", "profenid", "bi-profenid", "flexen", "ketoflex", "ketum",
            "nifluril", "niflumique", "surgam", "tiaprofénique"
        ]
        return any(k in name.lower() for k in keywords)

    def _is_stomach_risk(self, antecedents: str) -> bool:
        """Détecte les risques gastriques dans les antécédents."""
        if not antecedents: return False
        keywords = ["ulcère", "ulcere", "gastrite", "estomac", "reflux", "gerd", "rgo"]
        return any(k in antecedents.lower() for k in keywords)

    def _is_invasive_act(self, act_name: str) -> bool:
        keywords = [
            "extraction", "chirurgie", "implant", "endo", "canalaire", 
            "pulpotomie", "reprise", "sinus", "greffe", "resection",
            "lambeau", "curetage", "surfaçage", "detartrage", "détartrage",
            "pulpectomie", "obturation canalaire", "apicale"
        ]
        return any(k in act_name.lower() for k in keywords)

# Instance singleton
coherence_service = ClinicalCoherenceService()
