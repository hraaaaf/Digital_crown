from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.models_base import Base


class MobilePushSubscription(Base):
    """Web Push subscription bound to exactly one paired mobile device/user/tenant."""

    __tablename__ = "mobile_push_subscriptions"
    __table_args__ = (
        UniqueConstraint("device_id", name="uq_mobile_push_subscription_device"),
        UniqueConstraint("endpoint", name="uq_mobile_push_subscription_endpoint"),
        Index("ix_mobile_push_subscription_tenant_user", "employer_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("mobile_paired_devices.device_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    employer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Capability URL: never log it. Stored only in the local/private application DB.
    endpoint: Mapped[str] = mapped_column(Text, nullable=False)
    p256dh: Mapped[str] = mapped_column(String(255), nullable=False)
    auth: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[str] = mapped_column(String(32), nullable=False, default="web")
    vapid_public_key: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
