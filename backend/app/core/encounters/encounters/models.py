import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base

class Encounter(Base):
    __tablename__ = "encounters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    encounter_uuid = Column(String(50), unique=True, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    encounter_type = Column(String(50), nullable=False) # OP, IP, ER, FOLLOW_UP 
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    department = Column(String(100), nullable=False)
    status = Column(String(50), default="scheduled") # scheduled, in_progress, completed, cancelled
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", backref="patient_encounters")
    doctor = relationship("User", backref="doctor_encounters")
    diagnoses = relationship("EncounterDiagnosis", back_populates="encounter", cascade="all, delete-orphan")
    notes = relationship("EncounterNote", back_populates="encounter", cascade="all, delete-orphan")
    timeline_events = relationship("EncounterTimeline", back_populates="encounter", cascade="all, delete-orphan")
