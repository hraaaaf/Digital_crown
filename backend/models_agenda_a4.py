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


def install_agenda_resource_model() -> None:
    """Register A4's nullable appointment FK on shared metadata exactly once."""
    from backend import models

    table = models.Appointment.__table__
    if "resource_id" in table.c:
        return
    column = Column(
        "resource_id",
        Integer,
        ForeignKey("agenda_resources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    table.append_column(column)
    models.Appointment.resource_id = column
