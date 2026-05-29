from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
import enum

from backend.database import Base

class LabJobStatus(enum.Enum):
    PRESCRIPTION = "PRESCRIPTION"
    SENT = "SENT"
    IN_PROGRESS = "IN_PROGRESS"
    TRY_IN = "TRY_IN"
    READY = "READY"
    DELIVERED = "DELIVERED"

class LabJob(Base):
    __tablename__ = "lab_jobs"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    act_id = Column(Integer, ForeignKey("actes.id"), nullable=False)
    lab_id = Column(Integer, ForeignKey("labs.id"), nullable=True)

    material = Column(String, nullable=False)
    shade = Column(String, nullable=True)
    type = Column(String, nullable=False)  # e.g., "Couronne Zircone"
    tooth_number = Column(String, nullable=True)

    notes = Column(Text, nullable=True)
    deadline = Column(DateTime, nullable=False)
    status = Column(Enum(LabJobStatus), default=LabJobStatus.PRESCRIPTION, nullable=False)
    is_remake = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = relationship("Patient", backref="lab_jobs")
    act = relationship("Act", backref="lab_jobs")
    lab = relationship("Lab", backref="lab_jobs")

    @hybrid_property
    def is_late(self) -> bool:
        if self.status in (LabJobStatus.READY, LabJobStatus.DELIVERED):
            return False
        return datetime.utcnow() > self.deadline

    def __repr__(self):
        return f"<LabJob id={self.id} patient_id={self.patient_id} status={self.status}>"
