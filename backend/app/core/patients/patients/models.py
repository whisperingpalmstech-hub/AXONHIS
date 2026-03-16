import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_uuid = Column(String(50), unique=True, index=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(20), nullable=False)
    primary_phone = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    status = Column(String(50), default="active", nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships mapped later via string references or imported
    identifiers = relationship("PatientIdentifier", back_populates="patient", cascade="all, delete-orphan")
    contacts = relationship("PatientContact", back_populates="patient", cascade="all, delete-orphan")
    guardians = relationship("PatientGuardian", back_populates="patient", cascade="all, delete-orphan")
    insurance = relationship("PatientInsurance", back_populates="patient", cascade="all, delete-orphan")
    consents = relationship("PatientConsent", back_populates="patient", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Patient(patient_uuid='{self.patient_uuid}', name='{self.first_name} {self.last_name}')>"
