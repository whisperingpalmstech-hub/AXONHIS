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
    encounter_type = Column(String(50), nullable=True, default="opd")
    
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

# ── Extension for Universal EMR Subsystems ───────────────────────────

class ClinicalComplaint(Base):
    """ICPC compliant structured clinical complaint"""
    __tablename__ = "doctor_clinical_complaints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visit_id = Column(UUID(as_uuid=True), nullable=False)
    patient_id = Column(UUID(as_uuid=True), nullable=False)
    encounter_type = Column(String(50), nullable=True) # opd, ipd, er
    
    icpc_code = Column(String(50), nullable=True)
    complaint_description = Column(Text, nullable=False)
    duration = Column(String(50), nullable=True)
    severity = Column(String(50), nullable=True)
    associated_observations = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)

class PatientMedicalHistory(Base):
    """Persistent patient clinical history"""
    __tablename__ = "doctor_patient_medical_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    category = Column(String(100), nullable=False) # surgical, medical, family, allergy, medication, lifestyle, immunization
    description = Column(Text, nullable=False)
    status = Column(String(50), default="active") # active, resolved, inactive
    diagnosed_date = Column(String(50), nullable=True)
    
    recorded_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)

class ExaminationRecord(Base):
    """Structured systemic examination"""
    __tablename__ = "doctor_examination_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visit_id = Column(UUID(as_uuid=True), nullable=False)
    patient_id = Column(UUID(as_uuid=True), nullable=False)
    
    general_examination = Column(Text, nullable=True)
    systemic_examination = Column(JSON, nullable=True) # e.g. {"cvs": "...", "resp": "..."}
    local_examination = Column(Text, nullable=True)
    
    recorded_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)

class DiagnosisRecord(Base):
    """Standardized ICD-10 diagnosis record"""
    __tablename__ = "doctor_diagnosis_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visit_id = Column(UUID(as_uuid=True), nullable=False)
    patient_id = Column(UUID(as_uuid=True), nullable=False)
    
    icd_code = Column(String(50), nullable=True)
    diagnosis_description = Column(Text, nullable=False)
    diagnosis_type = Column(String(50), default="provisional") # provisional, final
    is_primary = Column(Boolean, default=False)
    
    recorded_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)

class EMRConsultationVitals(Base):
    """Vitals captured explicitly for the consultation"""
    __tablename__ = "doctor_consultation_vitals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visit_id = Column(UUID(as_uuid=True), nullable=False)
    patient_id = Column(UUID(as_uuid=True), nullable=False)
    
    temperature = Column(String(20), nullable=True)
    pulse_rate = Column(String(20), nullable=True)
    respiratory_rate = Column(String(20), nullable=True)
    bp_systolic = Column(Integer, nullable=True)
    bp_diastolic = Column(Integer, nullable=True)
    spo2 = Column(String(20), nullable=True)
    height_cm = Column(String(20), nullable=True)
    weight_kg = Column(String(20), nullable=True)
    bmi = Column(String(20), nullable=True)
    
    recorded_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    org_id = Column(UUID(as_uuid=True), nullable=True, index=True)
