# ==============================================================================
# FICHIER 2 : backend/services/document_factory.py (Version SaaS Multi-Tenant)
# ==============================================================================
import os
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from backend import models
from backend.services.template_engine import TemplateEngine
from backend.services.generators.ordonnance_gen import OrdonnanceGenerator
from backend.services.generators.certificat_gen import CertificatGenerator
from backend.services.generators.accounting_gen import AccountingGenerator
from backend.services.generators.libre_gen import LibreGenerator
from backend.services.generators.cephalo_gen import CephaloPDFGenerator

logger = logging.getLogger(__name__)


class DocumentFactory:
    """
    Façade S.O.L.I.D. révisée pour l'architecture SaaS Multi-Tenant.
    
    Pour les documents standards (ordonnance, certificat...), utilise le nouveau
    TemplateEngine avec les templates configurables.
    
    Pour les documents complexes (céphalométrie), conserve les générateurs
    spécialisés existants pendant la transition.
    """
    
    def __init__(self, output_dir="static/documents", static_dir="static"):
        self.output_dir = output_dir
        self.static_dir = static_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Nouveau moteur de templates SaaS
        self.template_engine = TemplateEngine(static_dir=static_dir)
        
        # Anciens générateurs (fallback et documents complexes)
        self.ord_gen = OrdonnanceGenerator(self.output_dir)
        self.cert_gen = CertificatGenerator(self.output_dir)
        self.acc_gen = AccountingGenerator(self.output_dir)
        self.libre_gen = LibreGenerator(self.output_dir)
        self.ceph_gen = CephaloPDFGenerator(self.output_dir)
    
    def _get_default_template(
        self, 
        doc_type: str, 
        db: Session, 
        user_id: int
    ) -> Optional[models.DocumentTemplate]:
        """
        Récupère le template par défaut pour un type de document.
        
        Ordre de priorité:
        1. Template personnalisé par défaut du user
        2. Template système par défaut
        3. Premier template système disponible
        """
        # Conversion du type (str) en Enum pour respecter la contrainte PostgreSQL
        enum_map = {
            'ordonnance': models.DocumentType.ORDONNANCE,
            'certificat': models.DocumentType.CERTIFICAT,
            'devis': models.DocumentType.DEVIS,
            'honoraires': models.DocumentType.NOTE_HONORAIRES,
            'note': models.DocumentType.NOTE_HONORAIRES,
            'libre': models.DocumentType.DOCUMENT_LIBRE,
            'cephalo': models.DocumentType.RAPPORT_CEPHALO
        }
        actual_type = enum_map.get(doc_type.lower(), models.DocumentType.AUTRE)
        
        # 1. Chercher template perso par défaut
        template = db.query(models.DocumentTemplate).filter(
            models.DocumentTemplate.type == actual_type,
            models.DocumentTemplate.user_id == user_id,
            models.DocumentTemplate.is_default == True
        ).first()
        
        if template:
            return template
        
        # 2. Chercher template système par défaut
        template = db.query(models.DocumentTemplate).filter(
            models.DocumentTemplate.type == actual_type,
            models.DocumentTemplate.is_system == True,
            models.DocumentTemplate.is_default == True
        ).first()
        
        if template:
            return template
        
        # 3. Premier template système disponible
        template = db.query(models.DocumentTemplate).filter(
            models.DocumentTemplate.type == actual_type,
            models.DocumentTemplate.is_system == True
        ).first()
        
        return template
    
    def _get_cabinet_config(self, user_id: int, db: Session) -> models.CabinetConfig:
        """Récupère la config du cabinet d'un utilisateur."""
        config = db.query(models.CabinetConfig).filter(
            models.CabinetConfig.owner_id == user_id
        ).first()
        
        if not config:
            raise ValueError(f"Cabinet non configuré pour l'utilisateur {user_id}")
        
        return config
    
    def _build_output_path(self, patient, doc_type: str) -> str:
        """Construit le chemin de sortie pour le PDF."""
        now = datetime.now()
        year_month = now.strftime('%Y/%m')
        
        save_dir = os.path.join(self.output_dir, year_month)
        os.makedirs(save_dir, exist_ok=True)
        
        safe_name = f"{patient.nom.upper()}_{patient.prenom.capitalize()}".replace(" ", "_")
        timestamp = now.strftime('%Y%m%d_%H%M%S')
        
        return os.path.join(save_dir, f"{doc_type.upper()}_{safe_name}_{timestamp}.pdf")
    
    # ==========================================================================
    # MÉTHODES PUBLIQUES (Interface existante préservée)
    # ==========================================================================
    
    def create_ordonnance(self, patient, data, db: Session = None, user_id: int = None):
        """
        Génère une ordonnance PDF.
        """
        try:
            # Récupérer template et config
            template = self._get_default_template('ordonnance', db, user_id)
            if not template:
                logger.warning("Template ordonnance non trouvé, fallback système ReportLab")
                return self.ord_gen.generate(patient, data, db=db, user_id=user_id)
            
            cabinet = self._get_cabinet_config(user_id, db)
            
            # Préparer le contexte
            context = {
                'patient': {
                    'nom': patient.nom,
                    'prenom': patient.prenom,
                    'age': self._calculate_age(patient.date_naissance)
                },
                'titre': 'ORDONNANCE',
                'content': self._format_medications(data.medications),
                'medications': data.medications,
                'praticien': {
                    'nom_complet': cabinet.nom_praticien or (cabinet.owner.nom_complet if cabinet.owner else "Docteur")
                },
                'date': datetime.now().strftime('%d/%m/%Y')
            }
            
            output_path = self._build_output_path(patient, 'ordonnance')
            
            return self.template_engine.generate_pdf(
                template=template,
                cabinet=cabinet,
                context=context,
                output_path=output_path
            )
            
        except Exception as e:
            logger.error(f"Erreur génération ordonnance, tentative fallback ReportLab: {e}")
            return self.ord_gen.generate(patient, data, db=db, user_id=user_id)
    
    def create_certificat(self, patient, data, db: Session = None, user_id: int = None):
        """
        Génère un certificat médical PDF.
        """
        try:
            template = self._get_default_template('certificat', db, user_id)
            if not template:
                return self.cert_gen.generate(patient, data, db=db, user_id=user_id)
            
            cabinet = self._get_cabinet_config(user_id, db)
            
            # Re-construction de la logique "Smart" Legacy pour le texte du certificat
            from datetime import date
            doc_date = getattr(data, 'doc_date', date.today())
            age = self._calculate_age(patient.date_naissance)
            gender = getattr(patient, 'sexe', 'M')
            hon = "Mr" if gender in ["Homme", "Garçon", "M", "Masculin"] else "Mme"
            
            type_repos = "Arrêt de travail" if getattr(data, 'is_work_stop', False) else "Repos médical"
            start_date_obj = getattr(data, 'start_date', None) or doc_date
            start_date_str = start_date_obj.strftime('%d/%m/%Y') if hasattr(start_date_obj, 'strftime') else str(start_date_obj)
            days = getattr(data, 'days', 1)
            reason = getattr(data, 'reason', 'son état de santé')
            dr_name = cabinet.nom_praticien or (cabinet.owner.nom_complet if cabinet.owner else "Docteur")
            
            # Nettoyage profond du préfixe Dr
            import re
            dr_name = re.sub(r'^(Dr\.?\s*)+', '', dr_name, flags=re.IGNORECASE).strip()
            
            full_cert_text = (
                f"Je soussigné, <b>Dr {dr_name}</b>, certifie que l'état de santé de "
                f"{hon} <b>{patient.nom.upper()} {patient.prenom.capitalize()}</b>, âgé(e) de {age} ans, "
                f"nécessite un <b>{type_repos}</b> de <b>{days} jours</b>, à partir du {start_date_str}.<br/><br/>"
                f"Ce certificat est délivré à l'intéressé(e) pour servir et faire valoir ce que de droit."
            )

            context = {
                'patient': {
                    'nom': patient.nom,
                    'prenom': patient.prenom,
                    'age': age,
                    'hon': hon
                },
                'titre': 'CERTIFICAT MÉDICAL',
                'content': full_cert_text,
                'praticien': {
                    'nom_complet': cabinet.nom_praticien or (cabinet.owner.nom_complet if cabinet.owner else "Docteur")
                },
                'date': datetime.now().strftime('%d/%m/%Y')
            }
            
            output_path = self._build_output_path(patient, 'certificat')
            
            return self.template_engine.generate_pdf(
                template=template,
                cabinet=cabinet,
                context=context,
                output_path=output_path
            )
            
        except Exception as e:
            logger.error(f"Erreur certificat template, fallback ReportLab: {e}")
            return self.cert_gen.generate(patient, data, db=db, user_id=user_id)
    
    def create_note_honoraires(self, patient, data, db: Session = None, user_id: int = None):
        """
        Note d'honoraires - Moteur ReportLab natif.
        """
        facture_seq = getattr(data, 'facture_numero', None)
        return self.acc_gen.generate_note(patient, data, facture_number=facture_seq, db=db, user_id=user_id)
    
    def create_devis(self, patient, data, db: Session = None, user_id: int = None):
        """
        Devis - Moteur ReportLab natif.
        """
        devis_seq = getattr(data, 'devis_numero', None)
        return self.acc_gen.generate_devis(patient, data, document_number=devis_seq, db=db, user_id=user_id)
    
    def create_document_libre(self, patient, data, db: Session = None, user_id: int = None):
        """
        Document libre - Moteur ReportLab natif.
        """
        return self.libre_gen.generate(patient, data, db=db, user_id=user_id)
    
    def create_cephalo_report(self, patient, analysis_data, db: Session = None, user_id: int = None):
        """
        Rapport céphalométrique - Moteur ReportLab natif complexe.
        """
        return self.ceph_gen.generate(patient, analysis_data, db=db, user_id=user_id)
    
    def create_bilan_report(self, patient, analysis_data, db: Session = None, user_id: int = None):
        """Alias pour create_cephalo_report."""
        return self.create_cephalo_report(patient, analysis_data, db=db, user_id=user_id)
    
    # ==========================================================================
    # UTILITAIRES
    # ==========================================================================
    
    @staticmethod
    def _calculate_age(born):
        """Calcule l'âge à partir de la date de naissance."""
        from datetime import date
        today = date.today()
        birth = born.date() if hasattr(born, 'date') else born
        return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
    
    @staticmethod
    def _format_medications(medications):
        """Formate la liste des médicaments en HTML."""
        if not medications:
            return "<p>Aucun médicament prescrit.</p>"
        
        html = ""
        for i, med in enumerate(medications, 1):
            # On utilise le gras pour tout et on enlève l'italique qui peut poser problème de couleur en fallback
            html += f"<b>{i}. {med.nom} - {med.dosage}</b><br/>"
            html += f"<b>Posologie : {med.posologie}</b><br/><br/>"
        return html
