# Digital Crown Routers Package

# P0-E compatibility bridge.
# The Alembic migration, schemas and installment router already define
# InstallmentPlan.acte_id. Register the missing SQLAlchemy mapped attribute
# before router modules are imported so fresh Base.metadata.create_all()
# databases and migrated databases share the same ORM contract.
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import mapped_column

from backend import models

if not hasattr(models.InstallmentPlan, "acte_id"):
    models.InstallmentPlan.acte_id = mapped_column(
        Integer,
        ForeignKey("actes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
