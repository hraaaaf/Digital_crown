import uuid
import enum
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import String, Boolean, Float, DateTime, ForeignKey, Enum as SQLEnum, Text, JSON, func, Integer, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models_base import Base

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
    manual_code: Mapped[Optional[str]] = mapped_column(String(6), nullable=True, index=True)
    employer_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    public_id: Mapped[str] = mapped_column(String(16), nullable=False)
    master_key: Mapped[str] = mapped_column(String(64), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="DENTISTE", nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class MobilePairedDevice(Base):
    """Appareil mobile appairé, lié à un utilisateur réel et à son cabinet."""
    __tablename__ = "mobile_paired_devices"

    device_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    employer_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    client_public_key_hex: Mapped[str] = mapped_column(String(130), nullable=False)
    refresh_jti: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)

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
