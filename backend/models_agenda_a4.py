from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint

from backend.models_base import Base


class AgendaResource(Base):
    """Tenant-scoped physical resource used by exact-time appointments."""

    __tablename__ = "agenda_resources"

    id = Column(Integer, primary_key=True)
    employer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(120), nullable=False)
    resource_type = Column(String(20), nullable=False, default="CHAIR")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("employer_id", "name", name="uq_agenda_resources_tenant_name"),
        Index("ix_agenda_resources_tenant_active", "employer_id", "is_active"),
    )
