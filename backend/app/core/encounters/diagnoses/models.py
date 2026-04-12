import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base

class EncounterDiagnosis(Base):
    __tablename__ = "encounter_diagnoses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"), nullable=False)
    diagnosis_code = Column(String(50), nullable=False) # e.g. ICD-10 J18.9
    diagnosis_description = Column(String(255), nullable=False)
    diagnosis_type = Column(String(50), nullable=False) # primary, secondary, provisional
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    encounter = relationship("Encounter", back_populates="diagnoses")
