import uuid
import enum
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import String, Boolean, Float, DateTime, ForeignKey, Enum as SQLEnum, Text, JSON, func, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# --- 1. ENUMÉRATIONS MÉTIER ---

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    DENTISTE = "DENTISTE"
    SECRETAIRE = "SECRETAIRE"

class SexeType(str, enum.Enum):
    M = "M"
    F = "F"

class ActeType(str, enum.Enum):
    SOIN = "SOIN"
    PROTHESE = "PROTHESE"
    ORTHO_SEMESTRE = "ORTHO_SEMESTRE"
    ORTHO_CONTENTION = "ORTHO_CONTENTION"


class PaiementStatut(str, enum.Enum):
    EN_ATTENTE = "EN_ATTENTE"
    PAYE = "PAYE"
    PARTIEL = "PARTIEL"
    A_ENCAISSER = "A_ENCAISSER"

class PaymentMethod(str, enum.Enum):
    ESPECES = "ESPECES"
    CARTE = "CARTE"
    VIREMENT = "VIREMENT"
    CHEQUE = "CHEQUE"

class AppointmentStatus(str, enum.Enum):
    PREVU = "PRÉVU"
    EN_SALLE_ATTENTE = "EN_S_ATTENTE" 
    EN_FAUTEUIL = "EN_FAUTEUIL"
    TERMINE = "TERMINÉ"
    ANNULE = "ANNULÉ"
 
class CabinetType(str, enum.Enum):
    PRIVE = "PRIVE"
    CLINIQUE = "CLINIQUE"

class QRCodeType(str, enum.Enum):
    NONE = "NONE"
    VALIDATION = "VALIDATION"
    VCARD = "VCARD"
    WEBSITE = "WEBSITE"
    INSTAGRAM = "INSTAGRAM"
    PAYMENT = "PAYMENT"
    WHATSAPP = "WHATSAPP"
    LOCATION = "LOCATION"

# --- 2. BASE DE DÉCLARATION ---

class Base(DeclarativeBase):
    """Classe de base pour tous les modèles SQLAlchemy."""
    pass

# --- 3. MODÈLES DE DONNÉES ---

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), default=UserRole.DENTISTE)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Gestion de Licence SaaS (Kill-Switch)
    is_licensed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    license_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    nom_complet: Mapped[Optional[str]] = mapped_column(String(255))
    specialites: Mapped[Optional[str]] = mapped_column(Text)
    adresse_complete: Mapped[Optional[str]] = mapped_column(Text)
    telephone_fixe: Mapped[Optional[str]] = mapped_column(String(20))
    telephone_mobile: Mapped[Optional[str]] = mapped_column(String(20))
    identifiants_legaux: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    permissions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    
    # Hiérarchie : Sous-comptes rattachés à un employeur (Dentiste/Admin)
    employer_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    employer: Mapped[Optional["User"]] = relationship(
        "User", remote_side="User.id", foreign_keys="User.employer_id",
        backref="team_members"
    )
    
    # Multi-tenant : Relations
    cabinet_config: Mapped[Optional["CabinetConfig"]] = relationship(
        "CabinetConfig", back_populates="owner", uselist=False
    )
    templates: Mapped[List["DocumentTemplate"]] = relationship(
        "DocumentTemplate", back_populates="user"
    )
    
    actes_realises: Mapped[List["Acte"]] = relationship(back_populates="praticien")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    def get_employer_id(self) -> int:
        """Retourne l'ID de l'employeur, ou son propre ID s'il est le compte principal."""
        return self.employer_id if self.employer_id else self.id

class Patient(Base):
    __tablename__ = "patients"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    numero_dossier: Mapped[Optional[str]] = mapped_column(String(20), unique=True, index=True, nullable=True)
    nom: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    prenom: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    date_naissance: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    sexe: Mapped[str] = mapped_column(String(10), nullable=False)
    
    # Multi-tenant : Lien vers le cabinet (Dentiste propriétaire)
    employer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    telephone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    photo_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    adresse: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    assurance: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # CNOPS, CNSS, MUTUELLE_FAR, PRIVEE, AUCUNE
    antecedents_medicaux: Mapped[str | None] = mapped_column(String, nullable=True)
    
    # Fiabilité Patient (Elite System)
    manual_grade: Mapped[Optional[str]] = mapped_column(String(20), nullable=True) # PLATINUM, GOLD, SILVER, BRONZE
    grade_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    dossier: Mapped["DossierClinique"] = relationship(back_populates="patient", uselist=False, cascade="all, delete-orphan")
    actes: Mapped[List["Acte"]] = relationship(back_populates="patient", cascade="all, delete-orphan")
    panoramic_analyses: Mapped[List["PanoramicAnalysis"]] = relationship(back_populates="patient", cascade="all, delete-orphan")
    analyses: Mapped[List["CephaloAnalysis"]] = relationship(back_populates="patient", cascade="all, delete-orphan")
    documents: Mapped[List["DocumentArchive"]] = relationship("DocumentArchive", back_populates="patient", cascade="all, delete-orphan")
    appointments: Mapped[List["Appointment"]] = relationship(back_populates="patient", cascade="all, delete-orphan")

class Appointment(Base):
    __tablename__ = "appointments"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[Optional[int]] = mapped_column(ForeignKey("patients.id", ondelete="SET NULL"), nullable=True)
    patient_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # Utilisé si patient_id est nul (rdv rapide)
    
    datetime_start: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    
    motif: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[AppointmentStatus] = mapped_column(SQLEnum(AppointmentStatus), default=AppointmentStatus.PREVU)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Suivi des rappels automatisés (Twilio/WhatsMate)
    reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reminder_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Multi-tenant
    employer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    # Relation inversée
    patient: Mapped[Optional["Patient"]] = relationship(back_populates="appointments")

class DossierClinique(Base):
    __tablename__ = "dossiers_cliniques"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), unique=True, nullable=False)
    is_ortho_active: Mapped[bool] = mapped_column(Boolean, default=False)
    note_honnetete: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    antecedents_medicaux: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    patient: Mapped["Patient"] = relationship(back_populates="dossier")

class Acte(Base):
    __tablename__ = "actes"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False)
    praticien_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    type_acte: Mapped[ActeType] = mapped_column(SQLEnum(ActeType), nullable=False)
    libelle: Mapped[str] = mapped_column(String(255), nullable=False)
    montant: Mapped[float] = mapped_column(Float, nullable=False)
    date_debut: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    statut_paiement: Mapped[PaiementStatut] = mapped_column(SQLEnum(PaiementStatut), default=PaiementStatut.EN_ATTENTE)
    is_accounted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_collected: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    
    patient: Mapped["Patient"] = relationship(back_populates="actes")
    praticien: Mapped["User"] = relationship(back_populates="actes_realises")

class CephaloAnalysis(Base):
    __tablename__ = "cephalo_analyses"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False)
    image_original_path: Mapped[str] = mapped_column(String, nullable=False)
    landmarks_data: Mapped[dict] = mapped_column(JSON, default=dict)
    angles_data: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # --- CALIBRATION mm/pixel ---
    is_calibrated: Mapped[bool] = mapped_column(Boolean, default=False)
    mm_per_pixel: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    calibration_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # {p1: {x,y}, p2: {x,y}, distance_mm: float}
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    patient: Mapped["Patient"] = relationship(back_populates="analyses")

class PanoramicAnalysis(Base):
    """Stockage des analyses radiographiques panoramiques (DENTEX IA)."""
    __tablename__ = "panoramic_analyses"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False)
    
    image_path: Mapped[str] = mapped_column(String, nullable=False)
    detections_data: Mapped[dict] = mapped_column(JSON, default=dict) # Stockage structuré DENTEX
    report_narrative: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    patient: Mapped["Patient"] = relationship(back_populates="panoramic_analyses")

# ==============================================================================
# --- PHASE 2 : SMART ORDONNANCE MODELS ---
# ==============================================================================

class Medication(Base):
    """Base de connaissance des médicaments avec score de fréquence."""
    __tablename__ = "medications"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nom: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    dosage: Mapped[Optional[str]] = mapped_column(String(50))
    forme: Mapped[Optional[str]] = mapped_column(String(50))
    usage_count: Mapped[int] = mapped_column(Integer, default=0)

class ClinicalCategory(Base):
    """Catégories cliniques (Extraction, Chirurgie, Soins, etc.)."""
    __tablename__ = "clinical_categories"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    label: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    
    protocols: Mapped[List["ClinicalProtocol"]] = relationship(back_populates="category", cascade="all, delete-orphan")

class ClinicalProtocol(Base):
    """Protocoles de prescription par défaut par catégorie."""
    __tablename__ = "clinical_protocols"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("clinical_categories.id"), nullable=False)
    variant_name: Mapped[str] = mapped_column(String(100), nullable=False) # Ex: Standard, Allergique
    
    # Stockage structuré de la liste des médicaments et posologies
    medications_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    category: Mapped["ClinicalCategory"] = relationship(back_populates="protocols")

# ==============================================================================
# --- SPRINT 1 : SMART BILLING / CATALOGUE DES ACTES ---
# ==============================================================================

class ClinicalActCatalog(Base):
    """Catalogue intelligent des actes cliniques pour l'autocomplétion."""
    __tablename__ = "clinical_act_catalog"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    base_price: Mapped[float] = mapped_column(Float, nullable=False)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)

# ==============================================================================
# --- ARCHIVAGE DOCUMENTS - GESTION VERSIONNEE ET CORBEILLE ---
# ==============================================================================

class DocumentType(str, enum.Enum):
    RAPPORT_CEPHALO = "RAPPORT_CEPHALO"
    ORDONNANCE = "ORDONNANCE"
    CERTIFICAT = "CERTIFICAT"
    DEVIS = "DEVIS"
    NOTE_HONORAIRES = "NOTE_HONORAIRES"
    LETTRE_MEDICALE = "LETTRE_MEDICALE"
    DOCUMENT_LIBRE = "DOCUMENT_LIBRE"
    PHOTO_CLINIQUE = "PHOTO_CLINIQUE"
    RADIOGRAPHIE = "RADIOGRAPHIE"
    MOULAGE = "MOULAGE"
    BILAN = "BILAN"
    AUTRE = "AUTRE"

class DocumentStatus(str, enum.Enum):
    ACTIF = "ACTIF"
    SUPPRIME = "SUPPRIME"
    ARCHIVE = "ARCHIVE"

class DocumentArchive(Base):
    """
    Systeme d'archivage intelligent avec :
    - Versioning automatique (meme doc = nouvelle version)
    - Detection des doublons (hash du fichier)
    - Corbeille avec recuperation (1 an)
    - Metadonnees riches (tags, notes)
    """
    __tablename__ = "document_archives"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Relations
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    patient: Mapped["Patient"] = relationship("Patient", back_populates="documents")
    
    uploaded_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    # Identification du document
    document_type: Mapped[DocumentType] = mapped_column(SQLEnum(DocumentType), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Versioning - Groupe de versions
    document_group_id: Mapped[str] = mapped_column(String(64), index=True)
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    is_latest_version: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    # Detection des doublons
    file_hash: Mapped[str] = mapped_column(String(64), index=True)
    file_size: Mapped[int] = mapped_column(Integer)
    
    # Chemins de stockage
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Metadonnees
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    
    # Statut et cycle de vie
    status: Mapped[DocumentStatus] = mapped_column(SQLEnum(DocumentStatus), default=DocumentStatus.ACTIF, index=True)
    
    # Tresorerie & Flux (Phase 1)
    is_accounted: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    payment_status: Mapped[PaiementStatut] = mapped_column(SQLEnum(PaiementStatut), default=PaiementStatut.EN_ATTENTE, index=True)
    is_collected: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    
    # Dates importantes
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    permanent_delete_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Contexte clinique (pour les rapports)
    clinical_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    analysis_id: Mapped[Optional[int]] = mapped_column(ForeignKey("cephalo_analyses.id"), nullable=True)



# ==============================================================================
# MODÈLES MULTI-TENANT (Phase SaaS)
# ==============================================================================

class CabinetConfig(Base):
    """
    Configuration unique par cabinet dentaire.
    Multi-tenant : chaque User (dentiste) a sa config.
    """
    __tablename__ = "cabinet_configs"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Multi-tenant : Ownership (1-1 avec User)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        unique=True, 
        nullable=False
    )
    owner: Mapped["User"] = relationship("User", back_populates="cabinet_config")
    
    # Identifiant public pour URLs (non séquentiel, sécurisé)
    public_id: Mapped[str] = mapped_column(
        String(16), 
        unique=True, 
        index=True,
        default=lambda: uuid.uuid4().hex[:16]
    )
    
    nom_cabinet: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    nom_praticien: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    nom_praticien_ar: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    
    # Logo : chemin relatif isolé par clinic_id
    logo_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Letterhead (Papier en-tête A4) : chemin relatif
    letterhead_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # En-tête Bilingue (max 6 lignes chacun)
    header_lines_fr: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    header_lines_ar: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    specialty_ids: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    
    # Pied de page
    footer_address: Mapped[str] = mapped_column(Text, nullable=False, default="")
    footer_phones: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    
    # Identifiants légaux (Copie dans config pour accès rapide PDF)
    ice: Mapped[str] = mapped_column(String(50), nullable=True, default="")
    if_: Mapped[str] = mapped_column(String(50), nullable=True, default="")  # 'if' est réservé
    inpe: Mapped[str] = mapped_column(String(50), nullable=True, default="")
    
    # Paramètres globaux de style
    primary_color: Mapped[str] = mapped_column(String(7), default="#003380", nullable=False)
    secondary_color: Mapped[str] = mapped_column(String(7), default="#1e40af", nullable=False)
    accent_color: Mapped[str] = mapped_column(String(7), default="#60a5fa", nullable=False)
    font_fr: Mapped[str] = mapped_column(String(50), default="Helvetica")
    font_ar: Mapped[str] = mapped_column(String(50), default="Amiri")
    
    # Options watermark
    watermark_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    watermark_opacity: Mapped[float] = mapped_column(default=0.10)
    
    # Marges personnalisées (utile pour le mode Letterhead)
    margin_top: Mapped[float] = mapped_column(Float, default=3.6, nullable=False)
    margin_bottom: Mapped[float] = mapped_column(Float, default=3.2, nullable=False)
    
    # État
    is_initialized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    selected_theme: Mapped[str] = mapped_column(String(20), default="elite", nullable=False)
    app_accent_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True, default=None)
    selected_template: Mapped[str] = mapped_column(String(20), default="classic", nullable=False)
    cabinet_type: Mapped[CabinetType] = mapped_column(SQLEnum(CabinetType), default=CabinetType.PRIVE, nullable=False)
    header_scale: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    header_font_scale: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    header_logo_scale: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    header_line_height: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    footer_font_scale: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    footer_qr_scale: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    footer_line_height: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    
    # Gestion des contacts granulaires (Sprint 59)
    contacts_json: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)
    
    # QR Code Strategy (Elite v4.0)
    qr_code_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    qr_code_type: Mapped[QRCodeType] = mapped_column(SQLEnum(QRCodeType), default=QRCodeType.VCARD, nullable=False)
    qr_code_value: Mapped[Optional[str]] = mapped_column(String(500), nullable=True) # URL ou @handle
    qr_code_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    qr_code_label: Mapped[Optional[str]] = mapped_column(String(100), nullable=True) # Ex: "Suivez-nous sur Instagram"
    qr_code_style: Mapped[str] = mapped_column(String(20), default="dots", nullable=False) # classic, dots, rounded, elite
    
    # Templates de clôture personnalisables (Accounting)
    cloture_note_template: Mapped[str] = mapped_column(Text, nullable=False, default="Arrêtée la présente note à la somme de : {total_words}.")
    cloture_devis_template: Mapped[str] = mapped_column(Text, nullable=False, default="Arrêté le présent devis à la somme de : {total_words}.")
    
    # Options d'affichage UI (Elite v4.1)
    show_patient_badges: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    performance_mode: Mapped[bool] = mapped_column(Boolean, default=False, server_default='false')
    clinical_tips_enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default='true')
    hide_header: Mapped[bool] = mapped_column(Boolean, default=True, server_default='true')
    hide_footer: Mapped[bool] = mapped_column(Boolean, default=True, server_default='true')

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class DocumentTemplate(Base):
    """
    Templates de documents PDF.
    Multi-tenant : 
    - Templates système : user_id=None, is_system=True (visibles par tous)
    - Templates perso : user_id=X, is_system=False (visibles uniquement par ce user)
    """
    __tablename__ = "document_templates"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Classification
    type: Mapped[DocumentType] = mapped_column(SQLEnum(DocumentType), nullable=False, index=True)
    style_key: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Métadonnées
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Multi-tenant & Visibilité
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True
    )
    user: Mapped[Optional["User"]] = relationship("User", back_populates="templates")
    
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Contenu (Sécurisé)
    body_html: Mapped[str] = mapped_column(Text, nullable=False)
    design_config: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

class DoctorPrescriptionPreference(Base):
    """
    Surcharges personnalisées des protocoles d'ordonnance par médecin.
    Permet une logique de priorité : Préférence Doc > Protocole Système.
    """
    __tablename__ = "doctor_prescription_preferences"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    doctor_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    act_code: Mapped[str] = mapped_column(String, index=True, nullable=False) # ex: EXTRACTION_SIMPLE
    
    # Stocke la liste des médicaments [ {name, dosage, forme, posologie}, ... ]
    drugs_json: Mapped[Dict] = mapped_column(JSON, nullable=False)
    
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Relations
    doctor: Mapped["User"] = relationship("User")

class DoctorMedicationHabit(Base):
    """
    Système de mémoire "Habits v2".
    Enregistre la fréquence d'utilisation des médicaments, dosages et posologies par praticien.
    """
    __tablename__ = "doctor_medication_habits"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    doctor_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    medication_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    dosage: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    posologie: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    usage_count: Mapped[int] = mapped_column(Integer, default=1)
    last_used: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

class DoctorActHabit(Base):
    """
    Système de mémoire des actes fréquents.
    Enregistre la fréquence d'utilisation des actes cliniques par praticien.
    """
    __tablename__ = "doctor_act_habits"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    doctor_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    act_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    base_price: Mapped[float] = mapped_column(Float, default=0.0)
    
    usage_count: Mapped[int] = mapped_column(Integer, default=1)
    last_used: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

class DoctorActCorrelation(Base):
    """
    Apprentissage des séquences d'actes (Smart Bundling).
    Stocke la probabilité que l'acte B suive l'acte A.
    """
    __tablename__ = "doctor_act_correlations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    doctor_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    act_a: Mapped[str] = mapped_column(String(255), index=True)
    act_b: Mapped[str] = mapped_column(String(255), index=True)
    
    occurrence_count: Mapped[int] = mapped_column(Integer, default=1)
    last_detected: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

class DoctorTriggerHabit(Base):
    """
    Machine à états proactive (Triggers).
    Stocke des règles apprises ou configurées basées sur des événements cliniques.
    """
    __tablename__ = "doctor_trigger_habits"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    doctor_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    trigger_type: Mapped[str] = mapped_column(String(50), index=True) # ex: PHASE_END, AGE_THRESHOLD
    context_key: Mapped[str] = mapped_column(String(100)) # ex: ORTHO_CONTENTION
    
    action_suggestion: Mapped[str] = mapped_column(String(255)) # ex: Commander fils contention
    priority: Mapped[int] = mapped_column(Integer, default=1)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

# ==============================================================================
# --- PHASE 5 : PAYMENT TRACKING & INSTALLMENTS ---
# ==============================================================================

class Payment(Base):
    """
    Table des encaissements réels pour suivre la trésorerie et la solvabilité patient.
    """
    __tablename__ = "payments"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    payment_method: Mapped[PaymentMethod] = mapped_column(SQLEnum(PaymentMethod), default=PaymentMethod.ESPECES)
    payment_date: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)
    
    # Liens optionnels vers un acte ou une échéance
    acte_id: Mapped[Optional[int]] = mapped_column(ForeignKey("actes.id", ondelete="SET NULL"), nullable=True)
    installment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("installments.id", ondelete="SET NULL"), nullable=True)
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    patient: Mapped["Patient"] = relationship()
    acte: Mapped[Optional["Acte"]] = relationship()
    installment: Mapped[Optional["Installment"]] = relationship()

class InstallmentPlan(Base):
    """
    Plan de paiement global (ex: Traitement Ortho, Implantologie).
    Regroupe plusieurs échéances.
    """
    __tablename__ = "installment_plans"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False) # Ex: Traitement Ortho 2024
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Relations
    patient: Mapped["Patient"] = relationship()
    installments: Mapped[List["Installment"]] = relationship(
        back_populates="plan", 
        cascade="all, delete-orphan",
        order_by="Installment.due_date"
    )

class Installment(Base):
    """
    Échéance individuelle au sein d'un plan.
    """
    __tablename__ = "installments"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("installment_plans.id", ondelete="CASCADE"), nullable=False)
    
    label: Mapped[str] = mapped_column(String(255), nullable=False) # Ex: Avance, Versement 1
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    paid_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    status: Mapped[str] = mapped_column(String(20), default="EN_ATTENTE") # EN_ATTENTE, PAYE, PARTIEL
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    plan: Mapped["InstallmentPlan"] = relationship(back_populates="installments")

# ==============================================================================
# --- OBSERVABILITY : AUDIT LOGS ---
# ==============================================================================

class AuditLog(Base):
    """
    Journal d'audit pour la tracabilite des actions sensibles.
    """
    __tablename__ = "audit_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)
    
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    employer_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    
    action: Mapped[str] = mapped_column(String(100), index=True) # DELETE, UPDATE, LOGIN_FAIL, ACCESS_DENIED
    resource_type: Mapped[str] = mapped_column(String(50), index=True) # Patient, Analysis, User
    resource_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    severity: Mapped[str] = mapped_column(String(20), default="INFO") # INFO, WARNING, CRITICAL
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    user: Mapped[Optional["User"]] = relationship("User")


class RevokedToken(Base):
    """
    Stockage persistant des tokens révoqués (JTI Blacklist).
    """
    __tablename__ = "revoked_tokens"

    jti: Mapped[str] = mapped_column(String(255), primary_key=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)


class AIFeedback(Base):
    """Retours praticien sur les insights IA — alimente le learning loop."""
    __tablename__ = "ai_feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    insight_type: Mapped[str] = mapped_column(String(50))
    insight_content: Mapped[str] = mapped_column(Text)
    action: Mapped[str] = mapped_column(String(20))  # accept / reject / edit
    corrected_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    employer_id: Mapped[int] = mapped_column(Integer, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class ProactiveAlert(Base):
    """E2 — Alertes proactives générées par le scheduler quotidien."""
    __tablename__ = "proactive_alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    employer_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    alert_type: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    action: Mapped[str] = mapped_column(String(255), default="")
    priority: Mapped[int] = mapped_column(Integer, default=2)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    patient: Mapped["Patient"] = relationship("Patient", foreign_keys=[patient_id])


class DeviceToken(Base):
    """E5 — Token FCM pour les notifications push mobiles."""
    __tablename__ = "device_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    employer_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    fcm_token: Mapped[str] = mapped_column(String(512), unique=True)
    platform: Mapped[str] = mapped_column(String(16), default="android")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


# ==============================================================================
# DONNÉES CLINIQUES (Contre-indications, Pharmacopée, Protocoles)
# Versionnées en DB pour permettre les mises à jour sans redéploiement.
# ==============================================================================

class ClinicalContraindication(Base):
    """Antécédent → liste de molécules contre-indiquées."""
    __tablename__ = "clinical_contraindications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    antecedent: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    molecule: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class ClinicalDrug(Base):
    """Molécule → noms commerciaux marocains, dosages, forme galénique."""
    __tablename__ = "clinical_drugs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    molecule: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    brand_names: Mapped[list] = mapped_column(JSON, default=list)
    dosages: Mapped[list] = mapped_column(JSON, default=list)
    form: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class ClinicalProtocolDB(Base):
    """Procédure → molécules recommandées + conseil post-opératoire (versionnées en DB)."""
    __tablename__ = "clinical_protocols_db"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    procedure: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    molecules: Mapped[list] = mapped_column(JSON, default=list)
    advice: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


# ==============================================================================
# APPAIRAGE MOBILE ZKA — TOKEN ÉPHÉMÈRE
# La masterKey ne transite jamais dans une URL. Le QR encode un UUID 5min.
# Le mobile échange ce token contre les credentials via POST /api/mobile/claim-token.
# ==============================================================================

class ZKAPairingToken(Base):
    """Token éphémère à usage unique pour l'appairage mobile ZKA."""
    __tablename__ = "zka_pairing_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    employer_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    public_id: Mapped[str] = mapped_column(String(16), nullable=False)
    master_key: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

