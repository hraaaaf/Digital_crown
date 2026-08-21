from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint

from backend.models import Base


class TreatmentPlanCatalogSnapshot(Base):
    """Immutable-by-value catalog data attached to the current treatment-plan step."""

    __tablename__ = "treatment_plan_catalog_snapshots"
    __table_args__ = (UniqueConstraint("step_id", name="uq_treatment_plan_catalog_snapshot_step"),)

    id = Column(Integer, primary_key=True, index=True)
    step_id = Column(Integer, ForeignKey("treatment_plan_steps.id", ondelete="CASCADE"), nullable=False, index=True)
    act_id = Column(Integer, nullable=False)
    code = Column(String, nullable=True)
    name = Column(String, nullable=False)
    price = Column(Numeric(12, 2), nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def as_payload(self) -> dict:
        return {
            "act_id": self.act_id,
            "code": self.code,
            "name": self.name,
            "price": float(self.price or 0),
        }
