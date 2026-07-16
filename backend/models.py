import uuid
import enum
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import String, Boolean, Float, DateTime, ForeignKey, Enum as SQLEnum, Text, JSON, func, Integer, UniqueConstraint, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# --- 1. ENUMÉRATIONS MÉTIER ---

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    DENTISTE = "DENTISTE"
    SECRETAIRE = "SECRETAIRE"

class SubscriptionPlan(str, enum.Enum):
    GOLD    = "GOLD"     # 1 dentiste + 2 assistantes
    PREMIUM = "PREMIUM"  # 2 dentistes + 6 assistantes
    ELITE   = "ELITE"    # clinique — illimité

class ApprovalStatus(str, enum.Enum):
    PENDING  = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

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
    # Legacy statuts
    PREVU = "PRÉVU"
    EN_SALLE_ATTENTE = "EN_S_ATTENTE"
    EN_FAUTEUIL = "EN_FAUTEUIL"
    TERMINE = "TERMINÉ"
    ANNULE = "ANNULÉ"
    # Frontdesk statuts
    EN_ATTENTE_DEMANDE = "EN_ATTENTE_DEMANDE"
    EN_ATTENTE_CONFIRM = "EN_ATTENTE_CONFIRM"
    CONFIRME = "CONFIRMÉ"
    REFUSE = "REFUSÉ"
    EXPIRE = "EXPIRÉ"
    ABSENT = "ABSENT"
 
class SchedulingType(str, enum.Enum):
    EXACT_TIME = "EXACT_TIME"
    MORNING = "MORNING"
    AFTERNOON = "AFTERNOON"
    FULL_DAY = "FULL_DAY"

class AgendaMode(str, enum.Enum):
    EXACT = "EXACT"
    BLOCK = "BLOCK"

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

class PlanStatus(str, enum.Enum):
    PENDING = "pending"
    DONE = "done"
    POSTPONED = "postponed"

class LabJobStatus(str, enum.Enum):
    PRESCRIPTION = "PRESCRIPTION"
    SENT = "SENT"
    IN_PROGRESS = "IN_PROGRESS"
    TRY_IN = "TRY_IN"
    READY = "READY"
    DELIVERED = "DELIVERED"

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
    
    # SuperAdmin Features
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_suspended: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    internal_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    nom_complet: Mapped[Optional[str]] = mapped_column(String(255))
    specialites: Mapped[Optional[str]] = mapped_column(Text)
    adresse_complete: Mapped[Optional[str]] = mapped_column(Text)
    telephone_fixe: Mapped[Optional[str]] = mapped_column(String(20))
    telephone_mobile: Mapped[Optional[str]] = mapped_column(String(20))
    identifiants_legaux: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    permissions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    
    # Plans d'abonnement et workflow d'approbation équipe (M1)
    subscription_plan: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, default=SubscriptionPlan.GOLD.value)
    approval_status: Mapped[str] = mapped_column(String(20), nullable=False, default=ApprovalStatus.APPROVED.value)
    approval_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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

class LicenseHistory(Base):
    __tablename__ = "license_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    admin_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    admin: Mapped[Optional["User"]] = relationship("User", foreign_keys=[admin_id])


class TrialActivationCode(Base):
    __tablename__ = "trial_activation_codes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    nom_complet: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cabinet_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    trial_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    consumed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    created_by_admin_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    consumed_by_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_by_admin: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_admin_id])
    consumed_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[consumed_by_user_id])

class Patient(Base):
    __tablename__ = "patients"

    # P0.4 : l'unicité de numero_dossier est désormais SCOPÉE au cabinet
    # (employer_id), pas globale — deux cabinets peuvent réutiliser le même
    # numéro sans collision. Les NULL restent autorisés en multiple (NULL
    # distinct en SQL). L'index simple est conservé pour les recherches.
    __table_args__ = (
        UniqueConstraint("numero_dossier", "employer_id", name="uq_patients_numero_dossier_employer"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    numero_dossier: Mapped[Optional[str]] = mapped_column(String(20), index=True, nullable=True)
    nom: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    prenom: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    date_naissance: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    sexe: Mapped[str] = mapped_column(String(10), nullable=False)
    
    # Multi-tenant : Lien vers le cabinet (Dentiste propriétaire)
    employer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    telephone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    telephone_2: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    telephone_3: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    photo_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    adresse: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Assurances
    assurance: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # CNOPS, CNSS, MUTUELLE_FAR, PRIVEE, AUCUNE
    assurance_privee_nom: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    assurance_complementaire: Mapped[bool] = mapped_column(Boolean, default=False)
    assurance_complementaire_nom: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Médical
    antecedents_medicaux: Mapped[str | None] = mapped_column(String, nullable=True)
    motif_consultation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Fiabilité Patient (Elite System)
    manual_grade: Mapped[Optional[str]] = mapped_column(String(20), nullable=True) # PLATINUM, GOLD, SILVER, BRONZE
    grade_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Soft-delete (P1, périmètre minimal — même pattern que JourneyMilestone) :
    # jamais de hard-delete d'un patient, uniquement masqué des points d'entrée
    # normaux (liste, doublon, GET détail). Les ~50 autres requêtes Patient du
    # backend ne filtrent pas deleted_at dans ce périmètre — dette documentée.
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    deleted_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    dossier: Mapped["DossierClinique"] = relationship(back_populates="patient", uselist=False, cascade="all, delete-orphan")
    master_plan: Mapped[Optional["TreatmentMasterPlan"]] = relationship(back_populates="patient", uselist=False, cascade="all, delete-orphan")
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
    scheduling_type: Mapped[SchedulingType] = mapped_column(SQLEnum(SchedulingType), default=SchedulingType.EXACT_TIME)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ticket_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Suivi des rappels automatisés (Twilio/WhatsMate)
    reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reminder_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Multi-tenant
    employer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Frontdesk fields (nullable, backward-compatible)
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)           # "frontdesk"|"web"|"bot"|"internal"
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)            # for standalone appointments
    confirmed_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)    # for auto-expiry of pending

    # Relation inversée
    patient: Mapped[Optional["Patient"]] = relationship(back_populates="appointments")

class DossierClinique(Base):
    __tablename__ = "dossiers_cliniques"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), unique=True, nullable=False)
    is_ortho_active: Mapped[bool] = mapped_column(Boolean, default=False)
    note_honnetete: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    antecedents_medicaux: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    patient: Mapped["Patient"] = relationship(back_populates="dossier")

class TreatmentMasterPlan(Base):
    __tablename__ = "treatment_master_plans"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    
    patient: Mapped["Patient"] = relationship(back_populates="master_plan")
    steps: Mapped[List["TreatmentPlanStep"]] = relationship(back_populates="master_plan", cascade="all, delete-orphan", order_by="TreatmentPlanStep.order_index")

class TreatmentPlanStep(Base):
    __tablename__ = "treatment_plan_steps"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("treatment_master_plans.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    assistant: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[PlanStatus] = mapped_column(SQLEnum(PlanStatus), default=PlanStatus.PENDING)
    date_str: Mapped[str] = mapped_column(String(100), default="Aujourd'hui")
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    
    master_plan: Mapped["TreatmentMasterPlan"] = relationship(back_populates="steps")

class Acte(Base):
    __tablename__ = "actes"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    praticien_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    type_acte: Mapped[ActeType] = mapped_column(SQLEnum(ActeType), nullable=False)
    libelle: Mapped[str] = mapped_column(String(255), nullable=False)
    montant: Mapped[float] = mapped_column(Float, nullable=False)
    date_debut: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    statut_paiement: Mapped[PaiementStatut] = mapped_column(SQLEnum(PaiementStatut), default=PaiementStatut.EN_ATTENTE)
    is_accounted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_collected: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    validated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Corbeille comptabilité : masque l'acte des vues de facturation/trésorerie
    # (honoraires, trésorerie latente, dettes patient) sans jamais effacer l'acte
    # clinique lui-même — l'historique de soin (habits_engine, RAG, scoring...)
    # continue de voir l'acte normalement. NULL = actif. Additive, jamais backfillé.
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)

    # UNIFY-ACT-PERSISTENCE-1 : lien optionnel vers la note d'honoraires qui a généré
    # cette ligne automatiquement (documents.py::generate_document). NULL pour tout Acte
    # créé manuellement (POST /clinical/actes) ou legacy — jamais backfillé.
    document_archive_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("document_archives.id", ondelete="SET NULL"), nullable=True, index=True
    )
    document_archive: Mapped[Optional["DocumentArchive"]] = relationship()

    notes_cliniques: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attachments: Mapped[Optional[list]] = mapped_column(JSON, default=list, nullable=True)

    patient: Mapped["Patient"] = relationship(back_populates="actes")
    praticien: Mapped["User"] = relationship(back_populates="actes_realises")

class CephaloAnalysis(Base):
    __tablename__ = "cephalo_analyses"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
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
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    
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
    category_id: Mapped[int] = mapped_column(ForeignKey("clinical_categories.id", ondelete="CASCADE"), nullable=False)
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
# --- SPRINT 6 : CATALOGUE DYNAMIQUE (Spécialités, Pathologies, Actes) ---
# ==============================================================================

class Specialty(Base):
    """Spécialités dentaires (ex: Orthodontie, Implantologie, Soins Conservateurs)"""
    __tablename__ = "specialties"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    color: Mapped[Optional[str]] = mapped_column(String(20), nullable=True) # Couleur UI
    
    pathologies: Mapped[List["Pathology"]] = relationship("Pathology", back_populates="specialty", cascade="all, delete-orphan")
    acts: Mapped[List["CatalogAct"]] = relationship("CatalogAct", back_populates="specialty", cascade="all, delete-orphan")

class Pathology(Base):
    """Pathologies documentées par spécialité"""
    __tablename__ = "pathologies"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    specialty_id: Mapped[int] = mapped_column(ForeignKey("specialties.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    specialty: Mapped["Specialty"] = relationship("Specialty", back_populates="pathologies")

class CatalogAct(Base):
    """Actes rattachés aux spécialités pour agenda, devis et odontogramme"""
    __tablename__ = "catalog_acts"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    specialty_id: Mapped[int] = mapped_column(ForeignKey("specialties.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True) # NGAP ou interne
    base_price: Mapped[float] = mapped_column(Float, default=0.0)
    color: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    specialty: Mapped["Specialty"] = relationship("Specialty", back_populates="acts")

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
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
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
    validated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
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
    
    # Identifiant de la clinique parente (si type=CLINIQUE ou multi-cabinets)
    clinic_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    
    nom_cabinet: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    nom_praticien: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    nom_praticien_ar: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    
    # Logo : chemin relatif isolé par clinic_id
    logo_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Letterhead (Papier en-tête A5) : chemin relatif
    letterhead_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    use_letterhead: Mapped[bool] = mapped_column(Boolean, default=False)
    
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
    # Décalage manette (cm) appliqué par-dessus la position calculée par le
    # template d'en-tête actif — colonnes ajoutées via migrate_cabinet_config_columns()
    # (nullable pour les lignes existantes, _get_val() retombe sur 0.0).
    header_logo_offset_x: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=0.0)
    header_logo_offset_y: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=0.0)

    # Gestion des contacts granulaires (Sprint 59)
    contacts_json: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)
    
    # QR Code Strategy (Elite v4.0)
    qr_code_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    qr_code_type: Mapped[QRCodeType] = mapped_column(SQLEnum(QRCodeType), default=QRCodeType.VCARD, nullable=False)
    qr_code_value: Mapped[Optional[str]] = mapped_column(String(500), nullable=True) # URL ou @handle
    qr_code_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    qr_code_label: Mapped[Optional[str]] = mapped_column(String(100), nullable=True) # Ex: "Suivez-nous sur Instagram"
    qr_code_style: Mapped[str] = mapped_column(String(20), default="dots", nullable=False) # classic, dots, rounded, elite
    # Décalage manette (cm) appliqué par-dessus la position ancrée bas-droite du QR
    qr_code_offset_x: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=0.0)
    qr_code_offset_y: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=0.0)
    
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
    doctor_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
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
    doctor_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
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
    doctor_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
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
    doctor_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
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
    doctor_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
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
    validated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
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
    # nullable : les alertes cabinet (stock, agenda) n'ont pas de patient associé
    patient_id: Mapped[Optional[int]] = mapped_column(ForeignKey("patients.id"), index=True, nullable=True)
    alert_type: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    action: Mapped[str] = mapped_column(String(255), default="")
    priority: Mapped[int] = mapped_column(Integer, default=2)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    snoozed_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    patient: Mapped[Optional["Patient"]] = relationship("Patient", foreign_keys=[patient_id])


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
    role: Mapped[str] = mapped_column(String(50), default="DENTISTE", nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

# ==============================================================================
# GHOST BRAIN V2 - MEMORY & PROACTIVITY
# ==============================================================================

class GhostMemoryLog(Base):
    """
    Mémoire du Bot (NLG Expert). Stocke les déductions passées pour ne pas se répéter
    et donner une notion de continuité (conscience temporelle) à l'analyse clinique.
    """
    __tablename__ = "ghost_memory_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # nullable : insights cabinet (stock, agenda) n'ont pas de patient
    patient_id: Mapped[Optional[int]] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), index=True, nullable=True)
    employer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    insight_type: Mapped[str] = mapped_column(String(50), index=True) # URGENCE, ORTHO, PHARMACOLOGIE, TEMPOREL, STOCK
    content: Mapped[str] = mapped_column(Text, nullable=False)
    context_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False) # Hash de l'état clinique
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)

    patient: Mapped["Patient"] = relationship("Patient", foreign_keys=[patient_id])


# ==============================================================================
# TREATMENT JOURNEY — JALONS MANUELS
# ==============================================================================

class MilestoneType(str, enum.Enum):
    DIAGNOSTIC = "DIAGNOSTIC"
    DEVIS_VALIDE = "DEVIS_VALIDE"
    CONTROLE = "CONTROLE"
    CLOTURE = "CLOTURE"


class JourneyMilestone(Base):
    """
    Jalon métier manuel du parcours patient (diagnostic établi, devis validé, contrôle,
    clôture) — n'a PAS de donnée backing ailleurs en base. Ne sert jamais à dupliquer des
    événements déjà présents dans actes/documents/paiements/radios : ceux-ci restent dans
    leurs tables sources et sont agrégés à la lecture par patient_journey_service.
    """
    __tablename__ = "journey_milestones"
    __table_args__ = (
        Index("ix_journey_milestones_employer_patient_date", "employer_id", "patient_id", "milestone_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), index=True, nullable=False)
    # Pas de CASCADE : la suppression d'un compte propriétaire ne doit jamais entraîner la
    # suppression silencieuse de jalons cliniques/administratifs.
    employer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)

    milestone_type: Mapped[MilestoneType] = mapped_column(SQLEnum(MilestoneType, name="milestone_type"), nullable=False, index=True)
    milestone_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    deleted_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    patient: Mapped["Patient"] = relationship("Patient", foreign_keys=[patient_id])


# ==============================================================================
# LAB JOBS — SUIVI DES TRAVAUX PROTHÉTIQUES
# ==============================================================================

class Lab(Base):
    """Laboratoire dentaire partenaire."""
    __tablename__ = "labs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class LabJob(Base):
    """Travail prothétique envoyé au laboratoire."""
    __tablename__ = "lab_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False)
    act_id: Mapped[int] = mapped_column(ForeignKey("actes.id"), nullable=False)
    lab_id: Mapped[Optional[int]] = mapped_column(ForeignKey("labs.id"), nullable=True)

    material: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    shade: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    type: Mapped[str] = mapped_column(String(255), nullable=False)
    tooth_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    deadline: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[LabJobStatus] = mapped_column(SQLEnum(LabJobStatus), default=LabJobStatus.PRESCRIPTION, nullable=False)
    is_remake: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    patient: Mapped["Patient"] = relationship("Patient")
    act: Mapped["Acte"] = relationship("Acte")
    lab: Mapped[Optional["Lab"]] = relationship("Lab")

    @property
    def is_late(self) -> bool:
        if self.status in (LabJobStatus.READY, LabJobStatus.DELIVERED):
            return False
        return datetime.now() > self.deadline

# ==============================================================================
# STOCK — GESTION DES CONSOMMABLES ET MATÉRIAUX
# ==============================================================================

class StockCategorie(str, enum.Enum):
    CONSOMMABLE = "CONSOMMABLE"
    MATERIAU    = "MATERIAU"
    MEDICAMENT  = "MEDICAMENT"
    EQUIPEMENT  = "EQUIPEMENT"

class StockItem(Base):
    """Article de stock du cabinet (consommable, matériau, médicament, équipement)."""
    __tablename__ = "stock_items"

    id:          Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    nom:           Mapped[str]            = mapped_column(String(255), nullable=False)
    categorie:     Mapped[StockCategorie] = mapped_column(SQLEnum(StockCategorie), nullable=False)
    quantite:      Mapped[float]          = mapped_column(Float, nullable=False, default=0.0)
    seuil_alerte:  Mapped[float]          = mapped_column(Float, nullable=False, default=5.0)
    unite:         Mapped[str]            = mapped_column(String(50), nullable=False, default="unité")
    prix_unitaire: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fournisseur:   Mapped[Optional[str]]   = mapped_column(String(255), nullable=True)
    notes:         Mapped[Optional[str]]   = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


# ==============================================================================
# PARTNER MARKETPLACE - COMMANDES PARTENAIRE
# ==============================================================================

class PartnerOrderStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SENT_TO_PARTNER = "SENT_TO_PARTNER"
    MODIFIED_AFTER_SEND = "MODIFIED_AFTER_SEND"
    CONFIRMED = "CONFIRMED"
    FULFILLED = "FULFILLED"
    CANCELLED = "CANCELLED"


class PartnerSettlementBasis(str, enum.Enum):
    SENT_TO_PARTNER = "SENT_TO_PARTNER"
    CONFIRMED = "CONFIRMED"
    FULFILLED = "FULFILLED"


class PartnerRevenueModel(str, enum.Enum):
    COMMISSION_PERCENT = "COMMISSION_PERCENT"
    DISCOUNT_RESALE = "DISCOUNT_RESALE"
    FIXED_FEE_PER_ORDER = "FIXED_FEE_PER_ORDER"


class PartnerProductAvailability(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    ON_REQUEST = "ON_REQUEST"
    DISCONTINUED = "DISCONTINUED"


class PartnerOrder(Base):
    """Commande partenaire capturee dans DigitalCrown, isolee par cabinet."""
    __tablename__ = "partner_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    order_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    partner_id: Mapped[str] = mapped_column(String(100), nullable=False, default="default-partner")
    partner_name: Mapped[str] = mapped_column(String(255), nullable=False, default="Partenaire")
    status: Mapped[PartnerOrderStatus] = mapped_column(SQLEnum(PartnerOrderStatus), nullable=False, default=PartnerOrderStatus.DRAFT)
    settlement_basis: Mapped[PartnerSettlementBasis] = mapped_column(
        SQLEnum(PartnerSettlementBasis), nullable=False, default=PartnerSettlementBasis.SENT_TO_PARTNER
    )
    revenue_model: Mapped[PartnerRevenueModel] = mapped_column(
        SQLEnum(PartnerRevenueModel), nullable=False, default=PartnerRevenueModel.COMMISSION_PERCENT
    )
    strategy_label: Mapped[str] = mapped_column(String(255), nullable=False, default="Commission sur envoi")
    commission_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    discount_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    fixed_fee_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    customer_full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_clinic: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_phone: Mapped[str] = mapped_column(String(50), nullable=False)
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_city: Mapped[str] = mapped_column(String(120), nullable=False)
    customer_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    lines_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    estimated_total: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sent_total: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    current_total: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    recognized_base_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    recognized_revenue_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    revenue_delta_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    partner_reference: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    status_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_partner_update_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    events: Mapped[List["PartnerOrderEvent"]] = relationship(
        "PartnerOrderEvent",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="PartnerOrderEvent.created_at.desc()"
    )


class PartnerOrderEvent(Base):
    """Historique de recalcul et de statut pour audit commercial."""
    __tablename__ = "partner_order_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("partner_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(60), nullable=False)
    previous_status: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    new_status: Mapped[str] = mapped_column(String(60), nullable=False)
    previous_total: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    new_total: Mapped[float] = mapped_column(Float, nullable=False)
    revenue_before: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    revenue_after: Mapped[float] = mapped_column(Float, nullable=False)
    delta_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payload_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)

    order: Mapped["PartnerOrder"] = relationship("PartnerOrder", back_populates="events")


class PartnerSupplier(Base):
    """Fournisseur partenaire du cabinet, configurable pour futur import API."""
    __tablename__ = "partner_suppliers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    supplier_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    badge: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    promise: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    api_base_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    sync_mode: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="manual")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    meta_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    products: Mapped[List["PartnerCatalogProduct"]] = relationship(
        "PartnerCatalogProduct",
        back_populates="supplier",
        cascade="all, delete-orphan",
        order_by="PartnerCatalogProduct.sort_order.asc(), PartnerCatalogProduct.name.asc()"
    )


class PartnerCatalogProduct(Base):
    """Produit catalogue partenaire, pret pour import externe et storefront."""
    __tablename__ = "partner_catalog_products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("partner_suppliers.id", ondelete="CASCADE"), nullable=False, index=True)

    external_product_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    dental_category: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    dental_specialty: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    unit: Mapped[str] = mapped_column(String(80), nullable=False, default="unite")
    price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    availability: Mapped[PartnerProductAvailability] = mapped_column(
        SQLEnum(PartnerProductAvailability), nullable=False, default=PartnerProductAvailability.AVAILABLE
    )
    short_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    long_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    benefits_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    supplier: Mapped["PartnerSupplier"] = relationship("PartnerSupplier", back_populates="products")


# ==============================================================================
# --- PHASE 6 : CROWN BOT SESSIONS (CHAT HISTORY) ---
# ==============================================================================

class BotSession(Base):
    """
    Historique des sessions du chatbot par utilisateur (isolation stricte).
    employer_id = tenant du cabinet, user_id = auteur de la session.
    """
    __tablename__ = "bot_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    employer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    # Contexte patient : si la conversation est ouverte depuis un dossier patient,
    # elle est rattachée à ce patient (historique par patient + injection auto de l'entité).
    patient_id: Mapped[Optional[int]] = mapped_column(ForeignKey("patients.id", ondelete="SET NULL"), nullable=True, index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False, default="Nouvelle Conversation")
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    
    messages: Mapped[List["BotMessage"]] = relationship("BotMessage", back_populates="session", cascade="all, delete-orphan", order_by="BotMessage.created_at")

class BotMessage(Base):
    """
    Messages individuels au sein d'une session de bot.
    """
    __tablename__ = "bot_messages"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(ForeignKey("bot_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    sender: Mapped[str] = mapped_column(String(20), nullable=False) # 'user' or 'bot'
    text: Mapped[str] = mapped_column(Text, nullable=False)
    
    # JSON pour stocker action_type, suggestions, et pending_action
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    session: Mapped["BotSession"] = relationship("BotSession", back_populates="messages")


class BotPendingAction(Base):
    """
    Action bot stockee cote serveur — seul l'ID est expose au client.
    Le frontend ne peut pas forger l'action, seulement la confirmer par ID.
    Expire automatiquement apres 30 minutes (non execute = dead).
    """
    __tablename__ = "bot_pending_actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(
        ForeignKey("bot_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    employer_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    params_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # pending | executed | expired | cancelled
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")

    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

class CabinetSettings(Base):
    __tablename__ = "cabinet_settings"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True, default=1)
    
    # Horaires
    opening_time_morning: Mapped[Optional[str]] = mapped_column(String(5), default="09:00")
    closing_time_morning: Mapped[Optional[str]] = mapped_column(String(5), default="13:00")
    opening_time_afternoon: Mapped[Optional[str]] = mapped_column(String(5), default="14:00")
    closing_time_afternoon: Mapped[Optional[str]] = mapped_column(String(5), default="18:00")
    is_continuous: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Configuration Agenda
    agenda_mode: Mapped[AgendaMode] = mapped_column(SQLEnum(AgendaMode), default=AgendaMode.EXACT)
    use_tickets: Mapped[bool] = mapped_column(Boolean, default=False)

class AgendaException(Base):
    __tablename__ = "agenda_exceptions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    is_holiday: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
