"""OPD Nursing Clinical Triage Engine — Database Models"""
import uuid
from datetime import datetime
from enum import StrEnum
from sqlalchemy import (
    Column, String, Text, DateTime, Boolean, Integer, Float,
    ForeignKey, Index, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class TriageStatus(StrEnum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"

class NursingWorklist(Base):
    """Dynamically populated worklist for nurses to track triage tasks"""
    __tablename__ = "nursing_worklist"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visit_id = Column(UUID(as_uuid=True), nullable=False)
    patient_id = Column(UUID(as_uuid=True), nullable=False)
    assigned_nurse_id = Column(UUID(as_uuid=True), nullable=True)
    
    triage_status = Column(String(30), default=TriageStatus.pending)
    priority_level = Column(String(30), default="normal") # normal, priority, emergency
    
    called_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_nursing_worklist_status", "triage_status"),
        Index("ix_nursing_worklist_visit", "visit_id"),
    )

class NursingVitals(Base):
    """Real-time structured vitals capture"""
    __tablename__ = "nursing_vitals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visit_id = Column(UUID(as_uuid=True), nullable=False)
    patient_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Core Vitals
    blood_pressure_systolic = Column(Integer, nullable=True)
    blood_pressure_diastolic = Column(Integer, nullable=True)
    heart_rate = Column(Integer, nullable=True)
    respiratory_rate = Column(Integer, nullable=True)
    temperature_celsius = Column(Float, nullable=True)
    oxygen_saturation_spo2 = Column(Integer, nullable=True)
    
    # Anthropometrics
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    bmi = Column(Float, nullable=True)
    
    # Optional Vitals
    blood_glucose = Column(Float, nullable=True)
    pain_score = Column(Integer, nullable=True) # 0-10
    gcs_score = Column(Integer, nullable=True)
    
    # Device Meta
    device_id = Column(String(100), nullable=True)
    is_manual_entry = Column(Boolean, default=True)
    
    recorded_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class NursingAssessment(Base):
    """Patient Clinical History Capture & Templates responses"""
    __tablename__ = "nursing_assessment"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visit_id = Column(UUID(as_uuid=True), nullable=False)
    patient_id = Column(UUID(as_uuid=True), nullable=False)
    template_used = Column(String(100), nullable=True)
    
    chief_complaint = Column(Text, nullable=True)
    allergy_information = Column(Text, nullable=True)
    past_medical_history = Column(Text, nullable=True)
    medication_history = Column(Text, nullable=True)
    family_history = Column(Text, nullable=True)
    social_history = Column(Text, nullable=True)
    
    nursing_observations = Column(Text, nullable=True)
    
    recorded_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class NursingTemplate(Base):
    """Configurable Clinical Templates for specialty specific routing"""
    __tablename__ = "nursing_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    specialty = Column(String(100), nullable=True)
    
    fields = Column(JSON, default=list) # e.g. [{"name": "chief_complaint", "type": "text"}]
    is_active = Column(Boolean, default=True)

class NursingDocumentUpload(Base):
    """For uploading previous reports, lab records etc at triage"""
    __tablename__ = "nursing_document_uploads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visit_id = Column(UUID(as_uuid=True), nullable=False)
    patient_id = Column(UUID(as_uuid=True), nullable=False)
    
    document_type = Column(String(50), nullable=False) # lab, radiology, prescription, photo
    file_path = Column(String(255), nullable=False)
    file_format = Column(String(20), nullable=False) # pdf, jpg, png, dicom
    
    uploaded_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class TriagePriorityUpdate(Base):
    """Audit log of abnormal vitals tripping priority adjustments"""
    __tablename__ = "triage_priority_updates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visit_id = Column(UUID(as_uuid=True), nullable=False)
    
    previous_priority = Column(String(30), nullable=False)
    new_priority = Column(String(30), nullable=False)
    
    trigger_reason = Column(Text, nullable=False) # e.g., "SpO2 < 92"
    vitals_snapshot = Column(JSON, nullable=True)
    
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)
