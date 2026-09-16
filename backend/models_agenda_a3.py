from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint

from backend.models import Base


class PractitionerAgendaSettings(Base):
    """Optional practitioner schedule override.

    Absence of a row means full inheritance from the cabinet schedule. The JSON
    payload only stores practitioner working intervals; effective availability is
    always the intersection with the cabinet schedule at runtime.
    """

    __tablename__ = "practitioner_agenda_settings"

    id = Column(Integer, primary_key=True)
    employer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    practitioner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    weekly_schedule_json = Column(Text, nullable=False)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "employer_id",
            "practitioner_id",
            name="uq_practitioner_agenda_settings_tenant_practitioner",
        ),
        Index(
            "ix_practitioner_agenda_settings_tenant_practitioner",
            "employer_id",
            "practitioner_id",
        ),
    )


class PractitionerAgendaException(Base):
    """Practitioner-only absence/leave interval."""

    __tablename__ = "practitioner_agenda_exceptions"

    id = Column(Integer, primary_key=True)
    employer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    practitioner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    reason = Column(String(255), nullable=False, default="Indisponibilité praticien")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index(
            "ix_practitioner_agenda_exceptions_tenant_practitioner_dates",
            "employer_id",
            "practitioner_id",
            "start_date",
            "end_date",
        ),
    )
