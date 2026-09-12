"""P0 multi-practitioner agenda model extension.

Keeps the historical ``backend.models.Appointment`` class as the canonical model while
registering the additive practitioner column before metadata ``create_all`` runs.
"""
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import mapped_column, relationship

from . import models


if "praticien_id" not in models.Appointment.__table__.c:
    models.Appointment.praticien_id = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    models.Appointment.praticien = relationship(
        "User",
        foreign_keys=[models.Appointment.praticien_id],
    )
