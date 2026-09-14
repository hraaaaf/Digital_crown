from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text, func

from backend.models_base import Base


class PatientClinicalContext(Base):
    """Practitioner-entered durable patient facts used by Prescription Intelligence.

    This table deliberately stores patient facts only. It does not encode dose rules,
    prescription-specific indications, contraindication thresholds, diagnostic stages,
    or clinical readiness.
    """

    __tablename__ = "patient_clinical_contexts"

    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), primary_key=True)
    employer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    weight_kg = Column(Float, nullable=True)

    medication_allergy_status = Column(String(32), nullable=False, default="UNKNOWN", server_default="UNKNOWN")
    medication_allergies = Column(JSON, nullable=True)

    renal_context_status = Column(String(32), nullable=False, default="UNKNOWN", server_default="UNKNOWN")
    renal_context_note = Column(Text, nullable=True)

    hepatic_context_status = Column(String(32), nullable=False, default="UNKNOWN", server_default="UNKNOWN")
    hepatic_context_note = Column(Text, nullable=True)

    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    updated_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
