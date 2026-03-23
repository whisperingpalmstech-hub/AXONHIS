"""
OPD Visit Intelligence Engine — Database Models
Tables: visit_master, visit_complaints, visit_classification, visit_priority,
        visit_questionnaire_responses, visit_doctor_recommendation, visit_context_snapshot,
        visit_questionnaire_templates, multi_visit_rules
"""
import uuid
from datetime import datetime
from enum import StrEnum
from sqlalchemy import (
    Column, String, Text, DateTime, Boolean, Integer, Float,
    ForeignKey, Index, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


# ── Enums ────────────────────────────────────────────────────────────────────

class VisitType(StrEnum):
    doctor_consultation = "doctor_consultation"
    follow_up = "follow_up"
    diagnostic = "diagnostic"
    teleconsultation = "teleconsultation"
    day_care = "day_care"
    emergency_opd = "emergency_opd"

class VisitSource(StrEnum):
    mobile_app = "mobile_app"
    kiosk = "kiosk"
    front_office = "front_office"
    appointment_arrival = "appointment_arrival"
    face_recognition = "face_recognition"
    qr_checkin = "qr_checkin"

class PriorityTag(StrEnum):
    emergency = "emergency"      # red
    priority = "priority"        # orange
    vip = "vip"                  # blue
    review = "review"            # green
    normal = "normal"            # white

class ClassificationCategory(StrEnum):
    routine = "routine"
    priority = "priority"
    emergency_opd = "emergency_opd"

class VisitStatus(StrEnum):
    created = "created"
    triage_pending = "triage_pending"
    in_queue = "in_queue"
    with_nurse = "with_nurse"
    with_doctor = "with_doctor"
    diagnostic_pending = "diagnostic_pending"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no_show"

class ComplaintInputMode(StrEnum):
    voice = "voice"
    typed = "typed"
    chatbot = "chatbot"
    kiosk_questionnaire = "kiosk_questionnaire"


# ── 1. Visit Master ─────────────────────────────────────────────────────────

class VisitMaster(Base):
    __tablename__ = "visit_master"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visit_id = Column(String(32), unique=True, nullable=False, index=True)
    encounter_id = Column(String(32), unique=True, nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), nullable=False)
    patient_uhid = Column(String(50), nullable=True)

    visit_date_time = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    visit_type = Column(String(30), default=VisitType.doctor_consultation)
    visit_source = Column(String(30), default=VisitSource.front_office)
    status = Column(String(30), default=VisitStatus.created)

    specialty = Column(String(100), nullable=True)
    doctor_id = Column(UUID(as_uuid=True), nullable=True)
    department = Column(String(100), nullable=True)
    clinic_location = Column(String(200), nullable=True)

    referral_type = Column(String(50), nullable=True)  # self, doctor, hospital
    referral_source = Column(String(200), nullable=True)
    payment_entitlement = Column(String(50), nullable=True)  # cash, insurance, corporate

    priority_tag = Column(String(20), default=PriorityTag.normal)
    is_follow_up = Column(Boolean, default=False)
    parent_visit_id = Column(UUID(as_uuid=True), nullable=True)

    appointment_id = Column(UUID(as_uuid=True), nullable=True)
    billing_id = Column(UUID(as_uuid=True), nullable=True)

    queue_token = Column(String(20), nullable=True)
    estimated_wait_min = Column(Integer, nullable=True)

    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_visit_patient", "patient_id"),
        Index("ix_visit_doctor", "doctor_id"),
        Index("ix_visit_date", "visit_date_time"),
        Index("ix_visit_status", "status"),
        Index("ix_visit_priority", "priority_tag"),
    )


# ── 2. Visit Complaints (AI Complaint Capture) ──────────────────────────────

class VisitComplaint(Base):
    __tablename__ = "visit_complaints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visit_id = Column(UUID(as_uuid=True), ForeignKey("visit_master.id"), nullable=False)

    raw_complaint_text = Column(Text, nullable=True)
    input_mode = Column(String(30), default=ComplaintInputMode.typed)
    language = Column(String(10), default="en")

    # AI-extracted data
    structured_symptoms = Column(JSON, default=list)   # ["chest pain", "dizziness"]
    medical_keywords = Column(JSON, default=list)       # ["cardiac", "syncope"]
    icpc_codes = Column(JSON, default=list)             # [{"code": "K01", "label": "Chest pain"}]
    icd_suggestions = Column(JSON, default=list)        # ICD-10 suggestions

    severity_score = Column(Float, nullable=True)       # 0-10 AI severity
    ai_confidence = Column(Float, nullable=True)        # 0-1 confidence

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("ix_complaint_visit", "visit_id"),
    )


# ── 3. Visit Classification ─────────────────────────────────────────────────

class VisitClassification(Base):
    __tablename__ = "visit_classification"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visit_id = Column(UUID(as_uuid=True), ForeignKey("visit_master.id"), nullable=False, unique=True)

    category = Column(String(20), default=ClassificationCategory.routine)
    classification_reason = Column(Text, nullable=True)
    triggered_rules = Column(JSON, default=list)  # rule IDs that fired

    # Inputs used
    complaint_severity = Column(Float, nullable=True)
    vitals_abnormal = Column(Boolean, default=False)
    has_chronic_disease = Column(Boolean, default=False)
    age_risk = Column(Boolean, default=False)

    vitals_snapshot = Column(JSON, nullable=True)  # {spo2, bp_sys, bp_dia, hr, temp}
    is_override = Column(Boolean, default=False)
    override_by = Column(UUID(as_uuid=True), nullable=True)
    override_reason = Column(Text, nullable=True)

    classified_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("ix_classification_visit", "visit_id"),
    )


# ── 4. Visit Doctor Recommendation ──────────────────────────────────────────

class VisitDoctorRecommendation(Base):
    __tablename__ = "visit_doctor_recommendation"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visit_id = Column(UUID(as_uuid=True), ForeignKey("visit_master.id"), nullable=False)

    recommended_specialty = Column(String(100), nullable=True)
    recommended_doctors = Column(JSON, default=list)  # [{doctor_id, name, score, reason}]

    # Inputs
    based_on_symptoms = Column(JSON, default=list)
    based_on_icpc = Column(JSON, default=list)
    based_on_history = Column(Boolean, default=False)
    previous_doctor_id = Column(UUID(as_uuid=True), nullable=True)

    selection_mode = Column(String(20), default="auto")  # auto, manual, patient_preference
    selected_doctor_id = Column(UUID(as_uuid=True), nullable=True)
    selected_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("ix_recommendation_visit", "visit_id"),
    )


# ── 5. Visit Questionnaire Templates ────────────────────────────────────────

class VisitQuestionnaireTemplate(Base):
    __tablename__ = "visit_questionnaire_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    specialty = Column(String(100), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    questions = Column(JSON, default=list)
    # [{id, text, type: "text"|"choice"|"scale"|"boolean", options: [], required: bool}]

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("ix_questionnaire_specialty", "specialty"),
    )


# ── 6. Visit Questionnaire Responses ────────────────────────────────────────

class VisitQuestionnaireResponse(Base):
    __tablename__ = "visit_questionnaire_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visit_id = Column(UUID(as_uuid=True), ForeignKey("visit_master.id"), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey("visit_questionnaire_templates.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), nullable=False)

    responses = Column(JSON, default=dict)  # {question_id: answer}
    completion_source = Column(String(30), nullable=True)  # mobile_app, kiosk, nurse_tablet
    completed_at = Column(DateTime(timezone=True), nullable=True)
    is_complete = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("ix_qresponse_visit", "visit_id"),
    )


# ── 7. Visit Context Snapshot ────────────────────────────────────────────────

class VisitContextSnapshot(Base):
    __tablename__ = "visit_context_snapshot"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visit_id = Column(UUID(as_uuid=True), ForeignKey("visit_master.id"), nullable=False, unique=True)
    patient_id = Column(UUID(as_uuid=True), nullable=False)

    # Auto-aggregated clinical context
    previous_diagnoses = Column(JSON, default=list)
    previous_prescriptions = Column(JSON, default=list)
    allergies = Column(JSON, default=list)
    chronic_conditions = Column(JSON, default=list)
    last_visit_notes = Column(Text, nullable=True)
    last_visit_date = Column(DateTime(timezone=True), nullable=True)
    recent_lab_reports = Column(JSON, default=list)
    recent_radiology_reports = Column(JSON, default=list)
    active_medications = Column(JSON, default=list)

    # Summary
    context_summary = Column(Text, nullable=True)
    risk_flags = Column(JSON, default=list)  # ["diabetes", "hypertension"]

    aggregated_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("ix_context_visit", "visit_id"),
    )


# ── 8. Multi-Visit Rules ────────────────────────────────────────────────────

class MultiVisitRule(Base):
    __tablename__ = "multi_visit_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    condition_type = Column(String(50), nullable=False)
    # same_doctor_same_day, different_specialty, diagnostic_after_consult

    action = Column(String(50), nullable=False)
    # mark_follow_up, create_new_visit, link_diagnostic

    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


# ── 9. Visit Analytics Snapshot ──────────────────────────────────────────────

class VisitAnalyticsSnapshot(Base):
    __tablename__ = "visit_analytics_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analytics_date = Column(DateTime(timezone=True), nullable=False)
    department = Column(String(100), nullable=True)

    total_visits = Column(Integer, default=0)
    routine_visits = Column(Integer, default=0)
    priority_visits = Column(Integer, default=0)
    emergency_visits = Column(Integer, default=0)

    completed_visits = Column(Integer, default=0)
    cancelled_visits = Column(Integer, default=0)
    no_show_visits = Column(Integer, default=0)

    avg_wait_time_min = Column(Float, nullable=True)
    avg_consult_time_min = Column(Float, nullable=True)

    top_specialties = Column(JSON, default=list)
    top_complaints = Column(JSON, default=list)
    doctor_load_distribution = Column(JSON, default=dict)

    computed_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("ix_visit_analytics_date", "analytics_date"),
    )
