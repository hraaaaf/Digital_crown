from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text, func

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

    # C2 durable facts. These fields remain factual context only; they do not imply
    # that any prescription rule is ready or clinically indicated.
    penicillin_allergy_status = Column(String(32), nullable=False, default="UNKNOWN", server_default="UNKNOWN")
    ie_cardiac_risk_category = Column(String(64), nullable=False, default="UNKNOWN", server_default="UNKNOWN")

    renal_context_status = Column(String(32), nullable=False, default="UNKNOWN", server_default="UNKNOWN")
    renal_context_note = Column(Text, nullable=True)

    hepatic_context_status = Column(String(32), nullable=False, default="UNKNOWN", server_default="UNKNOWN")
    hepatic_context_note = Column(Text, nullable=True)

    pregnancy_status = Column(String(32), nullable=False, default="UNKNOWN", server_default="UNKNOWN")
    breastfeeding_status = Column(String(32), nullable=False, default="UNKNOWN", server_default="UNKNOWN")
    current_medications_status = Column(String(32), nullable=False, default="UNKNOWN", server_default="UNKNOWN")
    current_medications = Column(JSON, nullable=True)

    # N4.3B backoffice-only antithrombotic facts. These remain explicit patient facts;
    # no drug class is inferred from free-text medication names.
    anticoagulant_status = Column(String(32), nullable=False, default="UNKNOWN", server_default="UNKNOWN")
    anticoagulants = Column(JSON, nullable=True)
    antiplatelet_status = Column(String(32), nullable=False, default="UNKNOWN", server_default="UNKNOWN")
    antiplatelets = Column(JSON, nullable=True)
    antithrombotic_classes = Column(JSON, nullable=True)
    antithrombotic_combination_status = Column(String(32), nullable=False, default="UNKNOWN", server_default="UNKNOWN")
    warfarin_inr = Column(Float, nullable=True)
    warfarin_inr_checked_at = Column(DateTime, nullable=True)
    warfarin_inr_current = Column(Boolean, nullable=True)
    lmwh_dose_class = Column(String(32), nullable=False, default="UNKNOWN", server_default="UNKNOWN")

    # N4.3B MRONJ prevention facts remain backoffice-only. No diagnostic staging
    # or CTX-based risk score is persisted here.
    mronj_medication_status = Column(String(32), nullable=False, default="UNKNOWN", server_default="UNKNOWN")
    mronj_agents = Column(JSON, nullable=True)
    mronj_agent_class = Column(String(32), nullable=False, default="UNKNOWN", server_default="UNKNOWN")
    mronj_indication = Column(String(32), nullable=False, default="UNKNOWN", server_default="UNKNOWN")
    mronj_route = Column(String(32), nullable=False, default="UNKNOWN", server_default="UNKNOWN")
    mronj_duration_months = Column(Integer, nullable=True)
    mronj_concurrent_risk_therapy = Column(JSON, nullable=True)
    active_oral_infection_or_inflammation = Column(String(32), nullable=False, default="UNKNOWN", server_default="UNKNOWN")
    suspected_or_known_mronj = Column(String(32), nullable=False, default="UNKNOWN", server_default="UNKNOWN")

    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    updated_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
