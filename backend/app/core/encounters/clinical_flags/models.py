import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base

class ClinicalFlag(Base):
    __tablename__ = "clinical_flags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    flag_type = Column(String(100), nullable=False) # allergy_alert, infection_risk, fall_risk, critical_condition
    flag_description = Column(String(500), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    patient = relationship("Patient", backref="clinical_flags")
