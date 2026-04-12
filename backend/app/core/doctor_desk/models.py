"""AI Doctor Desk & Intelligent EMR Engine — Database Models"""
import uuid
from datetime import datetime
from enum import StrEnum
from sqlalchemy import (
    Column, String, Text, DateTime, Boolean, Integer,
    ForeignKey, Index, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class ConsultStatus(StrEnum):
    waiting = "waiting"
    in_consultation = "in_consultation"
    completed = "completed"
    referred = "referred"

class DoctorWorklist(Base):
    """Real-time doctor assigned patient list synced with Smart Queue"""
    __tablename__ = "doctor_worklist"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doctor_id = Column(UUID(as_uuid=True), nullable=False)
    visit_id = Column(UUID(as_uuid=True), nullable=False)
    patient_id = Column(UUID(as_uuid=True), nullable=False)
    
    status = Column(String(30), default=ConsultStatus.waiting)
    priority_indicator = Column(String(30), default="normal") 
    queue_position = Column(Integer, nullable=True)
    
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)

class ConsultationNote(Base):
    """Structured clinical SOAP notes populated via AI or templates"""
    __tablename__ = "doctor_consultation_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visit_id = Column(UUID(as_uuid=True), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), nullable=False)
    
    chief_complaint = Column(Text, nullable=True)
    history_present_illness = Column(Text, nullable=True)
    physical_examination = Column(Text, nullable=True)
    diagnosis = Column(Text, nullable=True)
    plan = Column(Text, nullable=True)
    
    # AI Scribe Metadata
    generated_by_ai = Column(Boolean, default=False)
    audio_reference_url = Column(String(255), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)

class DoctorClinicalTemplate(Base):
    """Reusable blocks per specialty (General, Cardiology, etc)"""
    __tablename__ = "doctor_clinical_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    specialty = Column(String(100), nullable=True)
    
    chief_complaint_template = Column(Text, nullable=True)
    history_template = Column(Text, nullable=True)
    physical_template = Column(Text, nullable=True)
    plan_template = Column(Text, nullable=True)
    
    is_active = Column(Boolean, default=True)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)

class DoctorPrescription(Base):
    """Independent prescription log managed by Doctor Desk"""
    __tablename__ = "doctor_prescriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visit_id = Column(UUID(as_uuid=True), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), nullable=False)
    
    medicine_name = Column(String(255), nullable=False)
    strength = Column(String(100), nullable=True)
    dosage = Column(String(100), nullable=False)
    frequency = Column(String(100), nullable=False)
    duration = Column(String(100), nullable=False)
    instructions = Column(Text, nullable=True)
    
    prescribed_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)

class DoctorDiagnosticOrder(Base):
    """Laboratory & Radiology orders dispatched from Doctor Desk"""
    __tablename__ = "doctor_diagnostic_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visit_id = Column(UUID(as_uuid=True), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), nullable=False)
    
    order_type = Column(String(50), nullable=False) # lab, radiology, procedure
    test_name = Column(String(255), nullable=False)
    status = Column(String(50), default="ordered") # ordered, in_progress, completed
    instructions = Column(Text, nullable=True)
    
    ordered_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)

class DoctorClinicalSummary(Base):
    """Automatically compiled visit summary ready for export"""
    __tablename__ = "doctor_clinical_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visit_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    doctor_id = Column(UUID(as_uuid=True), nullable=False)
    
    summary_content = Column(JSON, nullable=False) # structured map of complaints, dx, rx, orders
    pdf_url = Column(String(255), nullable=True)
    
    generated_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class FollowUpRecord(Base):
    """Tracks future appointments, referrals, and medical certificates generated"""
    __tablename__ = "doctor_follow_up_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visit_id = Column(UUID(as_uuid=True), nullable=False)
    
    action_type = Column(String(50), nullable=False) # follow_up_appointment, referral, admission, medical_certificate
    target_date = Column(DateTime(timezone=True), nullable=True)
    target_specialty = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    certificate_url = Column(String(255), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
