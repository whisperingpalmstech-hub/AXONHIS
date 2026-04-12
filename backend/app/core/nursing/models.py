import uuid
from sqlalchemy import Column, String, DateTime, Boolean, Float, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from app.database import Base

class NursingVitalTrend(Base):
    __tablename__ = "nursing_vital_trends"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, nullable=False, index=True)
    patient_uhid = Column(String, nullable=False)
    recorded_by = Column(String, nullable=False)
    heart_rate = Column(Integer, nullable=True)
    blood_pressure_sys = Column(Integer, nullable=True)
    blood_pressure_dia = Column(Integer, nullable=True)
    temperature_f = Column(Float, nullable=True)
    spo2 = Column(Float, nullable=True)
    respiratory_rate = Column(Integer, nullable=True)
    pain_score = Column(Integer, nullable=True)
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_abnormal = Column(Boolean, default=False)

class NursingClinicalNote(Base):
    __tablename__ = "nursing_clinical_notes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, nullable=False, index=True)
    patient_uhid = Column(String, nullable=False)
    nurse_uuid = Column(String, nullable=False)
    note_type = Column(String, nullable=False) # Shift Handover, Observation
    clinical_note = Column(Text, nullable=False)
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class MedicationAdministrationRecord(Base):
    __tablename__ = "nursing_mar_records"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, nullable=False, index=True)
    medication_name = Column(String, nullable=False)
    route = Column(String, nullable=False) # IV, PO
    frequency = Column(String, nullable=False) # BD, TDS
    scheduled_slot = Column(String, nullable=False) # 08:00
    is_administered = Column(Boolean, default=False)
    administered_by = Column(String, nullable=True)
    administered_at = Column(DateTime(timezone=True), nullable=True)
    batch_number = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

class NursingIOChart(Base):
    __tablename__ = "nursing_io_charts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, nullable=False, index=True)
    entry_type = Column(String, nullable=False) # INTAKE, OUTPUT
    category = Column(String, nullable=False) # Oral, IV Fluids, Urine
    volume_ml = Column(Float, nullable=False)
    recorded_by = Column(String, nullable=False)
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
