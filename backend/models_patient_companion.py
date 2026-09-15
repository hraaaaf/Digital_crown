from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models_base import Base


class PatientCompanionIdentity(Base):
    """External patient identity. Never a cabinet User."""

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
    """Short-lived single-use cabinet invitation for pairing a verified Firebase identity."""

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
