# ==============================================================================
# FICHIER 2 : backend/services/document_factory.py (Version SaaS Multi-Tenant)
# ==============================================================================
import os
import logging
import uuid
from datetime import datetime, date
from typing import Optional
from sqlalchemy.orm import Session

from backend import models, schemas
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
    
    def _get_default_template(self, doc_type: str, db: Session, user_id: int) -> Optional[models.DocumentTemplate]:
        """Récupère le template par défaut pour un type de document."""
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
        
        if template: return template
        
        # 2. Chercher template système par défaut
        template = db.query(models.DocumentTemplate).filter(
            models.DocumentTemplate.type == actual_type,
            models.DocumentTemplate.is_system == True,
            models.DocumentTemplate.is_default == True
        ).first()
        
        return template or db.query(models.DocumentTemplate).filter(
            models.DocumentTemplate.type == actual_type,
            models.DocumentTemplate.is_system == True
        ).first()
    
    def _get_cabinet_config(self, user_id: int, db: Session) -> models.CabinetConfig:
        """Récupère la config du cabinet d'un utilisateur."""
        config = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == user_id).first()
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

    def _calculate_age(self, born):
        """Calcule l'âge à partir de la date de naissance."""
        if not born: return 0
        today = date.today()
        birth = born.date() if hasattr(born, 'date') else born
        return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
    
    # ==========================================================================
    # MÉTHODES PUBLIQUES
    # ==========================================================================
    
    def create_ordonnance(self, patient, data, db: Session = None, user_id: int = None):
        """Génère une ordonnance PDF via WeasyPrint (Elite) ou ReportLab."""
        if not db or not user_id:
            return self.ord_gen.generate(patient, data, db=db, user_id=user_id)
            
        try:
            template = self._get_default_template('ordonnance', db, user_id)
            cabinet = self._get_cabinet_config(user_id, db)
            
            # Signature QR
            from backend.services.qr_service import qr_service
            doc_id = str(uuid.uuid4())
            qr_url = qr_service.generate_document_qr(document_id=doc_id, public_id=cabinet.public_id)
            
            age = self._calculate_age(patient.date_naissance)
            context = {
                'patient': {
                    'nom': patient.nom.upper() if patient.nom else "PATIENT",
                    'prenom': patient.prenom.capitalize() if patient.prenom else "",
                    'age': age if age > 0 else "??",
                },
                'praticien': {
                    'nom_complet': f"Dr. {cabinet.nom_praticien}" if cabinet and cabinet.nom_praticien else (f"Dr. {cabinet.owner.nom_complet}" if (cabinet and cabinet.owner) else "Docteur")
                },
                'date_generation': getattr(data, 'doc_date', datetime.now().strftime('%d/%m/%Y')),
                'titre': "Ordonnance",
                'medications': data.medications,
                'page_size': 'A5',
                'custom': {'qr_code_url': qr_url}
            }
            
            output_path = self._build_output_path(patient, 'ordonnance')
            if template:
                template.body_html = "ordonnance_elite.html"
            
            return self.template_engine.generate_pdf(template, cabinet, context, output_path)
        except Exception as e:
            logger.error(f"Erreur create_ordonnance (WeasyPrint): {e}")
            return self.ord_gen.generate(patient, data, db=db, user_id=user_id)

    def create_certificat(self, patient, data, db: Session = None, user_id: int = None):
        """Génère un certificat médical PDF via WeasyPrint (Elite)."""
        try:
            cabinet = self._get_cabinet_config(user_id, db)
            template = self._get_default_template('certificat', db, user_id)
            
            age = self._calculate_age(patient.date_naissance)
            gender = getattr(patient, 'sexe', 'M')
            hon = "Mr" if gender in ["Homme", "Garçon", "M"] else "Madame"
            type_repos = "Arrêt de travail" if getattr(data, 'is_work_stop', False) else "Repos médical"
            
            def parse_date(d):
                if not d: return datetime.now()
                if isinstance(d, (datetime, date)): return d
                try: return datetime.strptime(d, '%Y-%m-%d')
                except: return datetime.now()

            doc_date_obj = parse_date(getattr(data, 'doc_date', None))
            start_date_obj = parse_date(getattr(data, 'start_date', None))
            
            from backend.services.qr_service import qr_service
            doc_id = str(uuid.uuid4())
            qr_url = qr_service.generate_document_qr(document_id=doc_id, public_id=cabinet.public_id)
            
            context = {
                'patient': {
                    'nom': patient.nom.upper() if patient.nom else "PATIENT",
                    'prenom': patient.prenom.capitalize() if patient.prenom else "",
                    'age': age if age > 0 else "??",
                },
                'praticien': {
                    'nom_complet': f"Dr. {cabinet.nom_praticien}" if cabinet and cabinet.nom_praticien else (f"Dr. {cabinet.owner.nom_complet}" if (cabinet and cabinet.owner) else "Docteur")
                },
                'date_generation': doc_date_obj.strftime('%d/%m/%Y'),
                'start_date': start_date_obj.strftime('%d/%m/%Y'),
                'certif_days': getattr(data, 'days', 3),
                'hon': hon,
                'type_repos': type_repos,
                'page_size': 'A5',
                'custom': {'qr_code_url': qr_url}
            }
            
            output_path = self._build_output_path(patient, 'certificat')
            if template:
                template.body_html = "certificat_elite.html"
            
            return self.template_engine.generate_pdf(template, cabinet, context, output_path)
            
        except Exception as e:
            logger.error(f"Erreur create_certificat (WeasyPrint): {e}")
            return self.cert_gen.generate(patient, data, db=db, user_id=user_id)

    def create_note_honoraires(self, patient, data, db: Session = None, user_id: int = None):
        facture_seq = getattr(data, 'facture_numero', None)
        return self.acc_gen.generate_note(patient, data, facture_number=facture_seq, db=db, user_id=user_id)
    
    def create_devis(self, patient, data, db: Session = None, user_id: int = None):
        devis_seq = getattr(data, 'devis_numero', None)
        return self.acc_gen.generate_devis(patient, data, document_number=devis_seq, db=db, user_id=user_id)
    
    def create_document_libre(self, patient, data, db: Session = None, user_id: int = None):
        return self.libre_gen.generate(patient, data, db=db, user_id=user_id)
    
    def create_cephalo_report(self, patient, analysis, db: Session = None, user_id: int = None):
        try:
            cabinet, user = None, None
            if db and user_id:
                cabinet = self._get_cabinet_config(user_id, db)
                user = db.query(models.User).filter(models.User.id == user_id).first()
            
            results_dict = analysis.results if hasattr(analysis, 'results') else analysis.get('results', analysis)
            radio_image_path = analysis.image_path if hasattr(analysis, 'image_path') else analysis.get('image_path')

            vm = schemas.CephaloViewModel(
                patient_nom=patient.nom,
                patient_prenom=patient.prenom,
                patient_age=str(self._calculate_age(patient.date_naissance)),
                patient_id=getattr(patient, 'id', None),
                analysis=schemas.CephaloAnalysisResult.model_validate(results_dict),
                cabinet_config={
                    "primary_color": cabinet.primary_color if cabinet else "#1A365D",
                    "logo_path": cabinet.logo_path if cabinet else None,
                    "margin_top": cabinet.margin_top if cabinet else 4.5,
                    "margin_bottom": cabinet.margin_bottom if cabinet else 3.5
                },
                doctor_name=f"Dr. {user.nom.upper()} {user.prenom.capitalize()}" if user else "Dr. Saninova",
                radio_image_path=radio_image_path
            )
            return self.ceph_gen.generate(vm)
        except Exception as e:
            logger.error(f"Erreur rapport céphalo: {e}")
            raise
