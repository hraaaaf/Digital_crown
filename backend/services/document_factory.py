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
        # 1. Chercher template perso par défaut
        template = db.query(models.DocumentTemplate).filter(
            models.DocumentTemplate.type == doc_type,
            models.DocumentTemplate.user_id == user_id,
            models.DocumentTemplate.is_default == True
        ).first()
        
        if template:
            return template
        
        # 2. Chercher template système par défaut
        template = db.query(models.DocumentTemplate).filter(
            models.DocumentTemplate.type == doc_type,
            models.DocumentTemplate.is_system == True,
            models.DocumentTemplate.is_default == True
        ).first()
        
        if template:
            return template
        
        # 3. Premier template système disponible
        template = db.query(models.DocumentTemplate).filter(
            models.DocumentTemplate.type == doc_type,
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
    
    def create_ordonnance(self, patient, data, db: Session, user_id: int):
        """
        Génère une ordonnance PDF.
        
        Args:
            patient: Objet Patient
            data: Données de l'ordonnance (médicaments...)
            db: Session SQLAlchemy
            user_id: ID de l'utilisateur (pour récupérer son template)
        """
        try:
            # Récupérer template et config
            template = self._get_default_template('ordonnance', db, user_id)
            if not template:
                logger.warning("Template ordonnance non trouvé, fallback ancien système")
                return self.ord_gen.generate(patient, data)
            
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
            logger.error(f"Erreur génération ordonnance template: {e}")
            logger.info("Fallback vers ancien générateur")
            return self.ord_gen.generate(patient, data)
    
    def create_certificat(self, patient, data, db: Session, user_id: int):
        """Génère un certificat médical."""
        try:
            template = self._get_default_template('certificat', db, user_id)
            if not template:
                return self.cert_gen.generate(patient, data)
            
            cabinet = self._get_cabinet_config(user_id, db)
            
            context = {
                'patient': {
                    'nom': patient.nom,
                    'prenom': patient.prenom,
                    'age': self._calculate_age(patient.date_naissance)
                },
                'titre': 'CERTIFICAT MÉDICAL',
                'content': data.reason if hasattr(data, 'reason') else '',
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
            logger.error(f"Erreur génération certificat template: {e}")
            return self.cert_gen.generate(patient, data)
    
    def create_note_honoraires(self, patient, data, db: Session = None, user_id: int = None):
        """
        Note d'honoraires - conserve l'ancien générateur pour l'instant
        (document complexe avec tableaux spécifiques).
        """
        facture_seq = getattr(data, 'facture_numero', None)
        return self.acc_gen.generate_note(patient, data, facture_number=facture_seq)
    
    def create_devis(self, patient, data, db: Session = None, user_id: int = None):
        """
        Devis - conserve l'ancien générateur pour l'instant.
        """
        devis_seq = getattr(data, 'devis_numero', None)
        return self.acc_gen.generate_devis(patient, data, document_number=devis_seq)
    
    def create_document_libre(self, patient, data, db: Session = None, user_id: int = None):
        """Document libre - conserve l'ancien générateur."""
        return self.libre_gen.generate(patient, data)
    
    def create_cephalo_report(self, patient, analysis_data):
        """
        Rapport céphalométrique - conserve le générateur spécialisé
        (document technique complexe avec dessins).
        """
        return self.ceph_gen.generate(patient, analysis_data)
    
    def create_bilan_report(self, patient, analysis_data):
        """Alias pour create_cephalo_report."""
        return self.create_cephalo_report(patient, analysis_data)
    
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
        
        html = "<ul>"
        for i, med in enumerate(medications, 1):
            html += f"<li><strong>{i}. {med.nom}</strong> - {med.dosage}<br>"
            html += f"<em>{med.posologie}</em></li>"
        html += "</ul>"
        return html
