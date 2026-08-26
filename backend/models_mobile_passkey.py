from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.models_base import Base


class MobilePasskeyCredential(Base):
    """Single WebAuthn credential bound to one paired mobile device/user/tenant."""

    __tablename__ = "mobile_passkey_credentials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    credential_id: Mapped[str] = mapped_column(String(1024), unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    employer_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    device_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("mobile_paired_devices.device_id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    credential_public_key: Mapped[str] = mapped_column(Text, nullable=False)
    sign_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    transports: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    credential_device_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    credential_backed_up: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    enabled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)


class MobileWebAuthnChallenge(Base):
    """Short-lived, one-shot challenge scoped to one paired-device ceremony."""

    __tablename__ = "mobile_webauthn_challenges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    challenge_b64url: Mapped[str] = mapped_column(String(255), nullable=False)
    purpose: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    employer_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    device_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("mobile_paired_devices.device_id", ondelete="CASCADE"), index=True, nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
