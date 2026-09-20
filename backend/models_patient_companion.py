from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models_base import Base


class PatientCompanionIdentity(Base):
    """External patient/device identity. Never a cabinet User."""

    __tablename__ = "patient_companion_identities"
    __table_args__ = (
        UniqueConstraint("provider", "subject", name="uq_patient_companion_identity_provider_subject"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="firebase")
    subject: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)

    accesses: Mapped[list["PatientCompanionAccess"]] = relationship(
        back_populates="identity",
        cascade="all, delete-orphan",
    )


class PatientCompanionAccess(Base):
    """Many-to-many authorization between one external identity and patient records."""

    __tablename__ = "patient_companion_accesses"
    __table_args__ = (
        UniqueConstraint(
            "identity_id",
            "employer_id",
            "patient_id",
            name="uq_patient_companion_access_identity_tenant_patient",
        ),
        Index(
            "ix_patient_companion_access_tenant_patient",
            "employer_id",
            "patient_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    public_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    identity_id: Mapped[int] = mapped_column(
        ForeignKey("patient_companion_identities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    employer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relationship_type: Mapped[str] = mapped_column(String(24), nullable=False, default="SELF")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)

    identity: Mapped["PatientCompanionIdentity"] = relationship(back_populates="accesses")


class PatientCompanionInvitation(Base):
    """Short-lived single-use cabinet invitation for local device pairing or legacy verified identity activation."""

    __tablename__ = "patient_companion_invitations"
    __table_args__ = (
        Index(
            "ix_patient_companion_invitation_tenant_patient",
            "employer_id",
            "patient_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    public_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    employer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    manual_code_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    recipient_type: Mapped[str] = mapped_column(String(16), nullable=False)
    recipient_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    relationship_type: Mapped[str] = mapped_column(String(24), nullable=False, default="SELF")
    created_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    consumed_by_identity_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("patient_companion_identities.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    consumed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)


class PatientCompanionShareGrant(Base):
    """Explicit allow-list entry for patient-visible document/media metadata."""

    __tablename__ = "patient_companion_share_grants"
    __table_args__ = (
        UniqueConstraint(
            "employer_id",
            "patient_id",
            "resource_type",
            "resource_id",
            name="uq_patient_companion_share_resource",
        ),
        Index(
            "ix_patient_companion_share_tenant_patient",
            "employer_id",
            "patient_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    public_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
    )
    employer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    resource_type: Mapped[str] = mapped_column(String(32), nullable=False)
    resource_id: Mapped[int] = mapped_column(nullable=False)
    granted_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)


class PatientCompanionCabinetRemoteKey(Base):
    """OS-protected cabinet private key + public JWK metadata for remote transport."""

    __tablename__ = "patient_companion_cabinet_remote_keys"
    __table_args__ = (
        Index(
            "ix_pc_cabinet_remote_key_tenant_use_status",
            "employer_id",
            "key_use",
            "status",
        ),
        Index(
            "uq_pc_cabinet_remote_key_one_active_per_use",
            "employer_id",
            "key_use",
            unique=True,
            sqlite_where=text("status = 'ACTIVE'"),
            postgresql_where=text("status = 'ACTIVE'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    employer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    key_use: Mapped[str] = mapped_column(String(8), nullable=False)
    public_jwk_json: Mapped[str] = mapped_column(Text, nullable=False)
    protected_private_jwk_b64: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    retired_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)


class PatientCompanionRemoteKeyset(Base):
    """Pinned patient public keys + cabinet key IDs for one access generation."""

    __tablename__ = "patient_companion_remote_keysets"
    __table_args__ = (
        Index("ix_pc_remote_keyset_access_status", "access_id", "status"),
        Index(
            "uq_pc_remote_keyset_one_active_per_access",
            "access_id",
            unique=True,
            sqlite_where=text("status = 'ACTIVE'"),
            postgresql_where=text("status = 'ACTIVE'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    public_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        index=True,
        default=lambda: str(uuid.uuid4()),
    )
    access_id: Mapped[int] = mapped_column(
        ForeignKey("patient_companion_accesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    patient_signing_kid: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    patient_signing_public_jwk_json: Mapped[str] = mapped_column(Text, nullable=False)
    patient_encryption_kid: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    patient_encryption_public_jwk_json: Mapped[str] = mapped_column(Text, nullable=False)
    cabinet_signing_kid: Mapped[str] = mapped_column(String(36), nullable=False)
    cabinet_encryption_kid: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    retired_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)


class PatientCompanionRemoteReceipt(Base):
    """Persistent replay/idempotency ledger for decrypted remote commands."""

    __tablename__ = "patient_companion_remote_receipts"
    __table_args__ = (
        UniqueConstraint(
            "access_id",
            "message_id",
            name="uq_pc_remote_receipt_access_message",
        ),
        UniqueConstraint(
            "access_id",
            "idempotency_key",
            name="uq_pc_remote_receipt_access_idempotency",
        ),
        Index("ix_pc_remote_receipt_access_status", "access_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    access_id: Mapped[int] = mapped_column(
        ForeignKey("patient_companion_accesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    message_id: Mapped[str] = mapped_column(String(36), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(36), nullable=False)
    operation: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="PROCESSING", index=True)
    response_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class PatientCompanionAppointmentRef(Base):
    """Opaque patient-facing reference for one cabinet appointment row."""

    __tablename__ = "patient_companion_appointment_refs"
    __table_args__ = (
        UniqueConstraint(
            "employer_id",
            "appointment_id",
            name="uq_pc_appointment_ref_tenant_appointment",
        ),
        Index(
            "ix_pc_appointment_ref_tenant_patient",
            "employer_id",
            "patient_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    public_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        index=True,
        default=lambda: str(uuid.uuid4()),
    )
    employer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    appointment_id: Mapped[int] = mapped_column(
        ForeignKey("appointments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class PatientCompanionAgendaSlot(Base):
    """Short-lived cabinet-issued opaque booking option for Patient Companion."""

    __tablename__ = "patient_companion_agenda_slots"
    __table_args__ = (
        Index("ix_pc_agenda_slot_tenant_expiry", "employer_id", "expires_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    public_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, index=True,
        default=lambda: str(uuid.uuid4()),
    )
    employer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    practitioner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    resource_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("agenda_resources.id", ondelete="CASCADE"), nullable=True, index=True,
    )
    datetime_start: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    duration_minutes: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)


class PatientCompanionPractitionerRef(Base):
    """Opaque alias for a cabinet practitioner exposed to Patient Companion."""

    __tablename__ = "patient_companion_practitioner_refs"
    __table_args__ = (
        UniqueConstraint(
            "employer_id",
            "practitioner_id",
            name="uq_pc_practitioner_ref_tenant_practitioner",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    public_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, index=True,
        default=lambda: str(uuid.uuid4()),
    )
    employer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    practitioner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
