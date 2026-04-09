"""
Clinical Encounter Flow Models

Implements the complete AI-powered clinical consultation workflow:
- Interactive questioning (one question at a time)
- Examination phase transition
- Management plan generation
- Document generation from audio
- Specialty and doctor-level prompt management
"""
from datetime import datetime
from typing import Optional
import uuid
import enum
from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey, Index, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class EncounterPhase(str, enum.Enum):
    """Phases of a clinical encounter"""
    COMPLAINT_CAPTURE = "COMPLAINT_CAPTURE"
    INTERACTIVE_QUESTIONING = "INTERACTIVE_QUESTIONING"
    EXAMINATION = "EXAMINATION"
    MANAGEMENT_PLANNING = "MANAGEMENT_PLANNING"
    DOCUMENT_GENERATION = "DOCUMENT_GENERATION"
    COMPLETED = "COMPLETED"


class ClinicalEncounterFlow(Base):
    """
    Main orchestrator for AI-powered clinical encounter flow.
    Tracks the current phase and state of the encounter.
    """
    __tablename__ = "clinical_encounter_flow"

    flow_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("md_encounter.encounter_id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("md_patient.patient_id", ondelete="CASCADE"), nullable=False, index=True)
    clinician_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    specialty_profile_id = Column(UUID(as_uuid=True), ForeignKey("md_specialty_profile.specialty_profile_id"), nullable=True, index=True)
    
    current_phase = Column(String(50), default=EncounterPhase.COMPLAINT_CAPTURE, nullable=False, index=True)
    phase_history = Column(JSONB, nullable=False, default=list)  # Track phase transitions with timestamps
    
    # Complaint capture
    chief_complaint_transcript = Column(Text, nullable=True)
    chief_complaint_language = Column(String(10), nullable=True)
    chief_complaint_analyzed = Column(Boolean, default=False)
    
    # Interactive questioning state
    question_count = Column(Integer, default=0)
    adequate_questions_reached = Column(Boolean, default=False)
    
    # Examination state
    examination_findings_transcript = Column(Text, nullable=True)
    examination_guidance_shown = Column(Boolean, default=False)
    
    # Management plan state
    management_plan_generated = Column(Boolean, default=False)
    management_plan_accepted = Column(Boolean, default=False)
    
    # Document generation state
    selected_document_types = Column(JSONB, nullable=False, default=list)
    documents_generated = Column(JSONB, nullable=False, default=list)
    
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    encounter = relationship("MdEncounter", backref="clinical_flow")
    patient = relationship("MdPatient", backref="clinical_flows")
    specialty_profile = relationship("MdSpecialtyProfile", backref="clinical_flows")

    __table_args__ = (
        Index('idx_flow_phase', 'current_phase', 'started_at'),
        Index('idx_flow_clinician', 'clinician_id', 'current_phase'),
    )


class QuestionTurn(Base):
    """
    Tracks each question-answer turn in the interactive questioning phase.
    LLM generates one question at a time, doctor asks patient, response is captured.
    """
    __tablename__ = "question_turn"

    turn_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flow_id = Column(UUID(as_uuid=True), ForeignKey("clinical_encounter_flow.flow_id", ondelete="CASCADE"), nullable=False, index=True)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("md_encounter.encounter_id", ondelete="CASCADE"), nullable=False, index=True)
    
    turn_number = Column(Integer, nullable=False)
    
    # LLM-generated question
    llm_question = Column(Text, nullable=False)
    question_context = Column(JSONB, nullable=False, default={})  # Patient data, previous answers, etc.
    prompt_used = Column(Text, nullable=True)  # Which prompt template was used
    
    # Doctor/patient response
    response_transcript = Column(Text, nullable=True)
    response_language = Column(String(10), nullable=True)
    response_audio_uri = Column(String(500), nullable=True)
    
    # LLM analysis of response
    response_analysis = Column(JSONB, nullable=True)  # Key findings, follow-up needed, etc.
    confidence_score = Column(Integer, nullable=True)  # 0-100
    
    # State
    is_complete = Column(Boolean, default=False)
    suggested_next_action = Column(String(50), nullable=True)  # CONTINUE_QUESTIONING, MOVE_TO_EXAMINATION, etc.
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    flow = relationship("ClinicalEncounterFlow", backref="question_turns")

    __table_args__ = (
        Index('idx_question_turn_flow', 'flow_id', 'turn_number'),
    )


class ExaminationGuidance(Base):
    """
    AI-generated examination guidance when transitioning from questioning to examination.
    Displays critical things to examine based on the complaint and questioning.
    """
    __tablename__ = "examination_guidance"

    guidance_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flow_id = Column(UUID(as_uuid=True), ForeignKey("clinical_encounter_flow.flow_id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("md_encounter.encounter_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # AI-generated guidance
    critical_examinations = Column(JSONB, nullable=False, default=list)  # List of body systems/areas to examine
    examination_priorities = Column(JSONB, nullable=False, default=list)  # Ordered by importance
    specific_findings_to_look_for = Column(JSONB, nullable=False, default=list)  # Specific signs/symptoms
    red_flags = Column(JSONB, nullable=False, default=list)  # Critical warning signs
    
    prompt_used = Column(Text, nullable=True)
    confidence_score = Column(Integer, nullable=True)
    
    # Doctor's examination findings
    examination_findings_transcript = Column(Text, nullable=True)
    examination_findings_analyzed = Column(Boolean, default=False)
    structured_findings = Column(JSONB, nullable=True)  # Parsed examination findings
    
    shown_to_doctor = Column(Boolean, default=False)
    acknowledged_by_doctor = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    flow = relationship("ClinicalEncounterFlow", backref="examination_guidance")


class ManagementPlan(Base):
    """
    AI-generated full management plan after examination.
    Includes diagnoses, medications, lab orders, and follow-up recommendations.
    Editable by the doctor.
    """
    __tablename__ = "management_plan"

    plan_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flow_id = Column(UUID(as_uuid=True), ForeignKey("clinical_encounter_flow.flow_id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("md_encounter.encounter_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # AI-generated plan (original)
    original_plan = Column(JSONB, nullable=False, default={})
    original_plan_text = Column(Text, nullable=True)
    
    # Doctor-modified plan (current)
    current_plan = Column(JSONB, nullable=False, default={})
    current_plan_text = Column(Text, nullable=True)
    
    # Plan components
    suggested_diagnoses = Column(JSONB, nullable=False, default=list)
    suggested_medications = Column(JSONB, nullable=False, default=list)
    suggested_lab_orders = Column(JSONB, nullable=False, default=list)
    suggested_imaging = Column(JSONB, nullable=False, default=list)
    suggested_procedures = Column(JSONB, nullable=False, default=list)
    follow_up_recommendations = Column(JSONB, nullable=False, default=list)
    
    # Doctor actions
    is_accepted = Column(Boolean, default=False)
    is_modified = Column(Boolean, default=False)
    modification_notes = Column(Text, nullable=True)
    
    # Integration
    orders_created = Column(JSONB, nullable=False, default=list)  # Track which orders were actually created
    prescriptions_created = Column(JSONB, nullable=False, default=list)
    
    prompt_used = Column(Text, nullable=True)
    confidence_score = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    flow = relationship("ClinicalEncounterFlow", backref="management_plan")


class DoctorPromptOverride(Base):
    """
    Doctor-level prompt overrides.
    Allows individual doctors to customize AI behavior beyond specialty-level prompts.
    """
    __tablename__ = "doctor_prompt_override"

    override_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clinician_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    specialty_profile_id = Column(UUID(as_uuid=True), ForeignKey("md_specialty_profile.specialty_profile_id"), nullable=True, index=True)
    
    # Override categories
    questioning_prompt = Column(Text, nullable=True)
    examination_prompt = Column(Text, nullable=True)
    management_plan_prompt = Column(Text, nullable=True)
    documentation_prompt = Column(Text, nullable=True)
    
    # Prompt variables
    prompt_variables = Column(JSONB, nullable=False, default={})
    
    # Preferences
    question_style = Column(String(50), nullable=True)  # CONCISE, DETAILED, FRIENDLY, PROFESSIONAL
    examination_style = Column(String(50), nullable=True)
    management_style = Column(String(50), nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    specialty_profile = relationship("MdSpecialtyProfile", backref="doctor_prompt_overrides")

    __table_args__ = (
        Index('idx_doctor_prompt_specialty', 'specialty_profile_id', 'is_active'),
    )
