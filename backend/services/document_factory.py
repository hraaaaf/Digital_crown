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
from backend.services.generators.bilan_ortho_gen import BilanOrthoPDFGenerator
from backend.services.generators.installment_gen import generate_installment_plan

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
        self.ceph_gen = BilanOrthoPDFGenerator(self.output_dir)
    
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
    
    def create_ordonnance(self, patient, data, db: Session = None, user_id: int = None, custom_config: dict = None):
        """Génère une ordonnance PDF via ReportLab (Stable v1.2 Ghost Elite)."""
        return self.ord_gen.generate(patient, data, db=db, user_id=user_id, custom_config=custom_config)

    def create_certificat(self, patient, data, db: Session = None, user_id: int = None):
        """Génère un certificat médical PDF via ReportLab (Stable v1.2 Ghost Elite)."""
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
            radio_image_path = getattr(analysis, 'image_path', getattr(analysis, 'image_original_path', None))

            vm = schemas.CephaloViewModel(
                patient_nom=patient.nom,
                patient_prenom=patient.prenom,
                patient_age=str(self._calculate_age(patient.date_naissance)),
                patient_id=getattr(patient, 'id', None),
                analysis=schemas.CephaloAnalysisResult.model_validate(results_dict),
                cabinet_config={
                    "primary_color": cabinet.primary_color if cabinet else "#1A365D",
                    "secondary_color": cabinet.secondary_color if cabinet else "#64748B",
                    "logo_path": cabinet.logo_path if cabinet else None,
                    "margin_top": cabinet.margin_top if cabinet else 4.5,
                    "margin_bottom": cabinet.margin_bottom if cabinet else 3.5,
                    "qr_code_style": cabinet.qr_code_style if cabinet else "dots",
                    "qr_code_color": cabinet.qr_code_color if cabinet else None,
                    "qr_code_enabled": cabinet.qr_code_enabled if cabinet else False
                },
                doctor_name=user.nom_complet if user and user.nom_complet.startswith("Dr") else (f"Dr. {user.nom_complet}" if user and user.nom_complet else "Dr. Saninova"),
                radio_image_path=radio_image_path
            )
            return self.ceph_gen.generate(vm)
        except Exception as e:
            logger.error(f"Erreur rapport céphalo: {e}")
            raise
            
    def create_installment_plan(self, db: Session, plan_id: int, user_id: int) -> dict:
        """
        Génère un PDF d'échéancier de paiement Ortho/Autre.
        """
        plan = db.query(models.InstallmentPlan).filter(models.InstallmentPlan.id == plan_id).first()
        if not plan:
            raise ValueError("Plan introuvable")
            
        patient = plan.patient
        clinic = db.query(models.Clinic).filter(models.Clinic.employer_id == patient.employer_id).first()
        if not clinic:
            raise ValueError("Clinique non trouvée")
            
        filepath = generate_installment_plan(plan, patient, clinic, self.output_dir)
        
        # Archiver
        archive = models.DocumentArchive(
            patient_id=patient.id,
            clinic_id=clinic.id,
            document_type="echeancier",
            title=f"Échéancier - {plan.title}",
            file_path=filepath,
            created_by=user_id,
            data_snapshot={"plan_id": plan.id}
        )
        db.add(archive)
        db.commit()
        db.refresh(archive)
        
        return {
            "url": f"/static/documents/{os.path.basename(filepath)}",
            "archive_id": archive.id,
            "filename": os.path.basename(filepath)
        }
