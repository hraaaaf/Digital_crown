from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, LargeBinary, String, Text, UniqueConstraint, text
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


class PatientCompanionRelayBinding(Base):
    """Local-only relay routing/capabilities for one Patient Companion access."""

    __tablename__ = "patient_companion_relay_bindings"
    __table_args__ = (
        UniqueConstraint("access_id", name="uq_pc_relay_binding_access"),
        Index("ix_pc_relay_binding_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    access_id: Mapped[int] = mapped_column(
        ForeignKey("patient_companion_accesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relay_url: Mapped[str] = mapped_column(Text, nullable=False)
    cabinet_inbox_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    patient_inbox_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    protected_cabinet_read_cap_b64: Mapped[str] = mapped_column(Text, nullable=False)
    protected_patient_write_cap_b64: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)


class PatientCompanionRelayOutbox(Base):
    """Durable encrypted ACK awaiting delivery to the patient relay inbox."""

    __tablename__ = "patient_companion_relay_outbox"
    __table_args__ = (
        UniqueConstraint(
            "binding_id",
            "source_envelope_id",
            name="uq_pc_relay_outbox_binding_source",
        ),
        UniqueConstraint("ack_envelope_id", name="uq_pc_relay_outbox_ack_envelope"),
        Index("ix_pc_relay_outbox_binding_delivery", "binding_id", "delivered_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    binding_id: Mapped[int] = mapped_column(
        ForeignKey("patient_companion_relay_bindings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_envelope_id: Mapped[str] = mapped_column(String(36), nullable=False)
    ack_envelope_id: Mapped[str] = mapped_column(String(36), nullable=False)
    blob: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)


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


class PatientCompanionEmergencyPhotoUpload(Base):
    """Temporary cabinet-side assembly state for one patient-originated emergency photo."""

    __tablename__ = "patient_companion_emergency_photo_uploads"
    __table_args__ = (
        UniqueConstraint("access_id", "public_id", name="uq_pc07_photo_upload_access_public"),
        Index("ix_pc07_photo_upload_access_status", "access_id", "status"),
        Index("ix_pc07_photo_upload_expires_at", "expires_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    public_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    access_id: Mapped[int] = mapped_column(
        ForeignKey("patient_companion_accesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    employer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    object_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    byte_size: Mapped[int] = mapped_column(nullable=False)
    chunk_count: Mapped[int] = mapped_column(nullable=False)
    captured_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="UPLOADING", index=True)
    asset_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("clinical_assets.id", ondelete="SET NULL"), nullable=True, index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class PatientCompanionEmergencyPhotoChunk(Base):
    """One authenticated plaintext chunk after remote-envelope decryption."""

    __tablename__ = "patient_companion_emergency_photo_chunks"
    __table_args__ = (
        UniqueConstraint("upload_id", "chunk_index", name="uq_pc07_photo_chunk_upload_index"),
        Index("ix_pc07_photo_chunk_upload", "upload_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    upload_id: Mapped[int] = mapped_column(
        ForeignKey("patient_companion_emergency_photo_uploads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(nullable=False)
    chunk_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


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
    consumed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)


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


class PatientCompanionQuestionnaireDefinition(Base):
    """Cabinet-scoped immutable questionnaire version exposed only by assignment."""

    __tablename__ = "patient_companion_questionnaire_definitions"
    __table_args__ = (
        UniqueConstraint(
            "employer_id", "lineage_key", "version",
            name="uq_pc_questionnaire_definition_lineage_version",
        ),
        Index("ix_pc_questionnaire_definition_tenant_status", "employer_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    public_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, index=True,
        default=lambda: str(uuid.uuid4()),
    )
    employer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    lineage_key: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    version: Mapped[int] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    questions_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    retired_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class PatientCompanionQuestionnaireAssignment(Base):
    """Explicit patient assignment for one immutable questionnaire version."""

    __tablename__ = "patient_companion_questionnaire_assignments"
    __table_args__ = (
        UniqueConstraint(
            "employer_id", "patient_id", "questionnaire_id",
            name="uq_pc_questionnaire_assignment_patient_version",
        ),
        Index(
            "ix_pc_questionnaire_assignment_tenant_patient_status",
            "employer_id", "patient_id", "status",
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
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    questionnaire_id: Mapped[int] = mapped_column(
        ForeignKey("patient_companion_questionnaire_definitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="ASSIGNED", index=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)


class PatientCompanionQuestionnaireSubmission(Base):
    """Immutable patient-reported answers pending explicit cabinet review."""

    __tablename__ = "patient_companion_questionnaire_submissions"
    __table_args__ = (
        UniqueConstraint("assignment_id", name="uq_pc_questionnaire_submission_assignment"),
        Index(
            "ix_pc_questionnaire_submission_tenant_status",
            "employer_id", "status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    public_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, index=True,
        default=lambda: str(uuid.uuid4()),
    )
    assignment_id: Mapped[int] = mapped_column(
        ForeignKey("patient_companion_questionnaire_assignments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    access_id: Mapped[int] = mapped_column(
        ForeignKey("patient_companion_accesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    employer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    questionnaire_id: Mapped[int] = mapped_column(
        ForeignKey("patient_companion_questionnaire_definitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    answers_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="PENDING_REVIEW", index=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reviewed_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    reviewer_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class PatientCompanionConsentRequest(Base):
    """Cabinet-issued request to acknowledge/sign one exact shared document version."""

    __tablename__ = "patient_companion_consent_requests"
    __table_args__ = (
        Index(
            "ix_pc_consent_request_tenant_patient_status",
            "employer_id", "patient_id", "status",
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
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    document_id: Mapped[int] = mapped_column(
        ForeignKey("document_archives.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    share_grant_id: Mapped[int] = mapped_column(
        ForeignKey("patient_companion_share_grants.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    document_group_id: Mapped[str] = mapped_column(String(64), nullable=False)
    document_version: Mapped[int] = mapped_column(nullable=False)
    document_file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    document_file_size: Mapped[int] = mapped_column(nullable=False)
    created_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)


class PatientCompanionConsentEvidence(Base):
    """Detached patient-signature evidence bound to one exact consent request/document hash."""

    __tablename__ = "patient_companion_consent_evidence"
    __table_args__ = (
        UniqueConstraint("consent_request_id", name="uq_pc_consent_evidence_request"),
        Index("ix_pc_consent_evidence_tenant_signed", "employer_id", "signed_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    public_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, index=True,
        default=lambda: str(uuid.uuid4()),
    )
    consent_request_id: Mapped[int] = mapped_column(
        ForeignKey("patient_companion_consent_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    access_id: Mapped[int] = mapped_column(
        ForeignKey("patient_companion_accesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    employer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    signature_png: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    signature_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    signature_size: Mapped[int] = mapped_column(nullable=False)
    signed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class PatientCompanionMessage(Base):
    """Canonical access-scoped secure text message between one Patient Companion access and cabinet staff."""

    __tablename__ = "patient_companion_messages"
    __table_args__ = (
        UniqueConstraint(
            "access_id",
            "client_message_id",
            name="uq_pc08_message_access_client",
        ),
        Index(
            "ix_pc08_message_access_created",
            "access_id",
            "created_at",
        ),
        Index(
            "ix_pc08_message_tenant_patient_access",
            "employer_id",
            "patient_id",
            "access_id",
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
    client_message_id: Mapped[str] = mapped_column(String(36), nullable=False)
    sender_kind: Mapped[str] = mapped_column(String(16), nullable=False)
    sender_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    staff_read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    staff_read_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    patient_received_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    patient_read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
