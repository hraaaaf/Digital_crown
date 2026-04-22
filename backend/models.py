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

class AppointmentStatus(str, enum.Enum):
    PREVU = "PRÉVU"
    EN_SALLE_ATTENTE = "EN_S_ATTENTE" 
    EN_FAUTEUIL = "EN_FAUTEUIL"
    TERMINE = "TERMINÉ"
    ANNULE = "ANNULÉ"
 
class CabinetType(str, enum.Enum):
    PRIVE = "PRIVE"
    CLINIQUE = "CLINIQUE"

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
    
    nom_complet: Mapped[Optional[str]] = mapped_column(String(255))
    specialites: Mapped[Optional[str]] = mapped_column(Text)
    adresse_complete: Mapped[Optional[str]] = mapped_column(Text)
    telephone_fixe: Mapped[Optional[str]] = mapped_column(String(20))
    telephone_mobile: Mapped[Optional[str]] = mapped_column(String(20))
    identifiants_legaux: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
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

class Patient(Base):
    __tablename__ = "patients"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    numero_dossier: Mapped[Optional[str]] = mapped_column(String(20), unique=True, index=True, nullable=True)
    nom: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    prenom: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    date_naissance: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    sexe: Mapped[str] = mapped_column(String(10), nullable=False)

    
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    telephone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    photo_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    adresse: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    assurance: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # CNOPS, CNSS, MUTUELLE_FAR, PRIVEE, AUCUNE
    antecedents_medicaux: Mapped[str | None] = mapped_column(String, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    dossier: Mapped["DossierClinique"] = relationship(back_populates="patient", uselist=False, cascade="all, delete-orphan")
    actes: Mapped[List["Acte"]] = relationship(back_populates="patient", cascade="all, delete-orphan")
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
    selected_template: Mapped[str] = mapped_column(String(20), default="classic", nullable=False)
    cabinet_type: Mapped[CabinetType] = mapped_column(SQLEnum(CabinetType), default=CabinetType.PRIVE, nullable=False)
    
    # Gestion des contacts granulaires (Sprint 59)
    contacts_json: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)
    
    # Templates de clôture personnalisables (Accounting)
    cloture_note_template: Mapped[str] = mapped_column(Text, nullable=False, default="Arrêtée la présente note à la somme de {total_words} TTC ({total_amount} MAD).")
    cloture_devis_template: Mapped[str] = mapped_column(Text, nullable=False, default="Arrêté le présent devis à la somme de {total_words} TTC ({total_amount} MAD).")
    
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
