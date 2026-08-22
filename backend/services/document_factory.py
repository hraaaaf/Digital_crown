# ==============================================================================
# FICHIER 2 : backend/services/document_factory.py (Version SaaS Multi-Tenant)
# ==============================================================================
import os
import logging
import uuid
from datetime import datetime, date
from sqlalchemy.orm import Session

from backend import models, schemas
from backend.services.generators.ordonnance_gen import OrdonnanceGenerator
from backend.services.generators.certificat_gen import CertificatGenerator
from backend.services.generators.tenant_aware_accounting_gen import TenantAwareAccountingGenerator
from backend.services.generators.libre_gen import LibreGenerator
from backend.services.generators.bilan_ortho_gen import BilanOrthoPDFGenerator
from backend.services.generators.installment_gen import generate_installment_plan
from backend.services.archive_service import ArchiveService
from backend.services.certificate_payload_policy import normalize_and_validate_certificate_data
from backend.services.honoraires_contract import validate_honoraires_document_data

logger = logging.getLogger(__name__)

class DocumentFactory:
    """
    Façade S.O.L.I.D. révisée pour l'architecture SaaS Multi-Tenant.
    """
    
    def __init__(self, output_dir="static/documents", static_dir="static"):
        self.output_dir = output_dir
        self.static_dir = static_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Générateurs PDF réellement utilisés par les routes produit.
        self.ord_gen = OrdonnanceGenerator(self.output_dir)
        self.cert_gen = CertificatGenerator(self.output_dir)
        self.acc_gen = TenantAwareAccountingGenerator(self.output_dir)
        self.libre_gen = LibreGenerator(self.output_dir)
        self.ceph_gen = BilanOrthoPDFGenerator(self.output_dir)
    
    def _get_cabinet_config(self, user_id: int, db: Session) -> models.CabinetConfig:
        """Récupère la config du cabinet — filtre sur l'employeur (isolation multi-tenant)."""
        user = db.query(models.User).filter(models.User.id == user_id).first()
        employer_id = user.get_employer_id() if user else user_id
        config = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == employer_id).first()
        if not config:
            raise ValueError(f"Cabinet non configuré pour l'employeur {employer_id}")
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

    def _create_settings_preview_ordonnance(self, patient, data, db: Session, user_id: int, custom_config: dict):
        """Génère un PDF de preview Settings dans un espace isolé et borné par utilisateur."""
        preview_root = os.path.join(self.output_dir, ".previews", "settings_branding", str(user_id or "anonymous"))
        os.makedirs(preview_root, exist_ok=True)

        # Une seule génération de preview conservée par utilisateur : la suivante
        # remplace la précédente au lieu de polluer le dossier des vrais documents.
        for root, _, files in os.walk(preview_root):
            for filename in files:
                if filename.lower().endswith(".pdf"):
                    try:
                        os.remove(os.path.join(root, filename))
                    except OSError as exc:
                        logger.warning("Impossible de nettoyer un ancien preview Settings %s: %s", filename, exc)

        preview_config = dict(custom_config or {})
        preview_config.pop("settings_preview", None)
        preview_generator = OrdonnanceGenerator(preview_root)
        return preview_generator.generate(patient, data, db=db, user_id=user_id, custom_config=preview_config)
    
    # ==========================================================================
    # MÉTHODES PUBLIQUES
    # ==========================================================================
    
    def create_ordonnance(self, patient, data, db: Session = None, user_id: int = None, custom_config: dict = None):
        """Génère une ordonnance PDF via ReportLab (Stable v1.2 Ghost Elite)."""
        if custom_config and custom_config.get("settings_preview"):
            return self._create_settings_preview_ordonnance(patient, data, db, user_id, custom_config)
        return self.ord_gen.generate(patient, data, db=db, user_id=user_id, custom_config=custom_config)

    def create_certificat(self, patient, data, db: Session = None, user_id: int = None):
        """Génère un certificat médical PDF après validation du contrat P3."""
        validated_data = normalize_and_validate_certificate_data(data)
        return self.cert_gen.generate(patient, validated_data, db=db, user_id=user_id)

    def create_note_honoraires(self, patient, data, db: Session = None, user_id: int = None):
        validated_data = validate_honoraires_document_data(data)
        facture_seq = getattr(validated_data, 'facture_numero', None)
        return self.acc_gen.generate_note(patient, validated_data, facture_number=facture_seq, db=db, user_id=user_id)
    
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

            # Lire les flags de pré-bilan et avertissements
            is_pre_bilan = analysis.get("_is_pre_bilan", False) if isinstance(analysis, dict) else False
            validation_warnings = analysis.get("_validation_warnings", []) if isinstance(analysis, dict) else []

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
                radio_image_path=radio_image_path,
                is_pre_bilan=is_pre_bilan,
                validation_warnings=validation_warnings
            )
            return self.ceph_gen.generate(vm)
        except Exception as e:
            logger.error(f"Erreur rapport céphalo: {e}")
            raise
            
    def create_installment_plan(self, db: Session, plan_id: int, user_id: int, archive: bool = True) -> dict:
        """
        Génère un PDF d'échéancier de paiement Ortho/Autre.

        En mode preview (`archive=False`), aucune archive BDD n'est créée.
        """
        actor = db.query(models.User).filter(models.User.id == user_id).first()
        if not actor:
            raise ValueError("Utilisateur introuvable")

        plan = db.query(models.InstallmentPlan).filter(models.InstallmentPlan.id == plan_id).first()
        if not plan:
            raise ValueError("Plan introuvable")

        patient = plan.patient
        if not patient or patient.employer_id != actor.get_employer_id():
            raise ValueError("Accès refusé: le plan n'appartient pas au cabinet de l'utilisateur")

        config = self._get_cabinet_config(user_id, db)
        filepath = generate_installment_plan(plan, patient, config, self.output_dir)

        if not archive:
            return {
                "url": f"/static/documents/{os.path.basename(filepath)}",
                "archive_id": None,
                "filename": os.path.basename(filepath)
            }

        archive_obj = ArchiveService.archive_document(
            db=db,
            patient_id=patient.id,
            user_id=user_id,
            document_type="echeancier",
            title=f"Échéancier - {plan.title}",
            file_path=filepath,
            data_snapshot={"plan_id": plan.id},
        )

        return {
            "url": f"/static/documents/{os.path.basename(filepath)}",
            "archive_id": archive_obj.id,
            "filename": os.path.basename(filepath)
        }