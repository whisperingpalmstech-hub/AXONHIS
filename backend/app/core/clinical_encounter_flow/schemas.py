"""
Clinical Encounter Flow Schemas

Pydantic schemas for the clinical encounter flow API.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from enum import Enum


class EncounterPhase(str, Enum):
    """Phases of a clinical encounter"""
    COMPLAINT_CAPTURE = "COMPLAINT_CAPTURE"
    INTERACTIVE_QUESTIONING = "INTERACTIVE_QUESTIONING"
    EXAMINATION = "EXAMINATION"
    MANAGEMENT_PLANNING = "MANAGEMENT_PLANNING"
    DOCUMENT_GENERATION = "DOCUMENT_GENERATION"
    COMPLETED = "COMPLETED"


# ── Clinical Encounter Flow ──────────────────────────────────────────────────

class ClinicalEncounterFlowCreate(BaseModel):
    encounter_id: UUID
    patient_id: UUID
    clinician_id: UUID
    specialty_profile_id: Optional[UUID] = None


class ClinicalEncounterFlowUpdate(BaseModel):
    current_phase: Optional[EncounterPhase] = None
    chief_complaint_transcript: Optional[str] = None
    chief_complaint_language: Optional[str] = None
    chief_complaint_analyzed: Optional[bool] = None
    adequate_questions_reached: Optional[bool] = None
    examination_findings_transcript: Optional[str] = None
    management_plan_accepted: Optional[bool] = None
    selected_document_types: Optional[List[str]] = None


class ClinicalEncounterFlowResponse(BaseModel):
    flow_id: UUID
    encounter_id: UUID
    patient_id: UUID
    clinician_id: UUID
    specialty_profile_id: Optional[UUID]
    current_phase: str
    phase_history: List[Dict[str, Any]]
    chief_complaint_transcript: Optional[str]
    chief_complaint_language: Optional[str]
    chief_complaint_analyzed: bool
    question_count: int
    adequate_questions_reached: bool
    examination_findings_transcript: Optional[str]
    examination_guidance_shown: bool
    management_plan_generated: bool
    management_plan_accepted: bool
    selected_document_types: List[str]
    documents_generated: List[Dict[str, Any]]
    started_at: datetime
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Question Turn ────────────────────────────────────────────────────────────

class QuestionTurnCreate(BaseModel):
    flow_id: UUID
    encounter_id: UUID
    response_transcript: Optional[str] = None
    response_language: Optional[str] = None
    response_audio_uri: Optional[str] = None


class QuestionTurnResponse(BaseModel):
    turn_id: UUID
    flow_id: UUID
    encounter_id: UUID
    turn_number: int
    llm_question: str
    question_context: Dict[str, Any]
    prompt_used: Optional[str]
    response_transcript: Optional[str]
    response_language: Optional[str]
    response_audio_uri: Optional[str]
    response_analysis: Optional[Dict[str, Any]]
    confidence_score: Optional[int]
    is_complete: bool
    suggested_next_action: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Examination Guidance ─────────────────────────────────────────────────────

class ExaminationGuidanceCreate(BaseModel):
    flow_id: UUID
    encounter_id: UUID
    examination_findings_transcript: Optional[str] = None


class ExaminationGuidanceResponse(BaseModel):
    guidance_id: UUID
    flow_id: UUID
    encounter_id: UUID
    critical_examinations: List[Dict[str, Any]]
    examination_priorities: List[Dict[str, Any]]
    specific_findings_to_look_for: List[str]
    red_flags: List[str]
    prompt_used: Optional[str]
    confidence_score: Optional[int]
    examination_findings_transcript: Optional[str]
    examination_findings_analyzed: bool
    structured_findings: Optional[Dict[str, Any]]
    shown_to_doctor: bool
    acknowledged_by_doctor: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Management Plan ───────────────────────────────────────────────────────────

class ManagementPlanCreate(BaseModel):
    flow_id: UUID
    encounter_id: UUID
    current_plan: Optional[Dict[str, Any]] = None
    current_plan_text: Optional[str] = None
    suggested_diagnoses: Optional[List[Dict[str, Any]]] = None
    suggested_medications: Optional[List[Dict[str, Any]]] = None
    suggested_lab_orders: Optional[List[Dict[str, Any]]] = None
    suggested_imaging: Optional[List[Dict[str, Any]]] = None
    suggested_procedures: Optional[List[Dict[str, Any]]] = None
    follow_up_recommendations: Optional[List[str]] = None


class ManagementPlanUpdate(BaseModel):
    current_plan: Optional[Dict[str, Any]] = None
    current_plan_text: Optional[str] = None
    is_accepted: Optional[bool] = None
    is_modified: Optional[bool] = None
    modification_notes: Optional[str] = None


class ManagementPlanResponse(BaseModel):
    plan_id: UUID
    flow_id: UUID
    encounter_id: UUID
    original_plan: Dict[str, Any]
    original_plan_text: Optional[str]
    current_plan: Dict[str, Any]
    current_plan_text: Optional[str]
    suggested_diagnoses: List[Dict[str, Any]]
    suggested_medications: List[Dict[str, Any]]
    suggested_lab_orders: List[Dict[str, Any]]
    suggested_imaging: List[Dict[str, Any]]
    suggested_procedures: List[Dict[str, Any]]
    follow_up_recommendations: List[str]
    is_accepted: bool
    is_modified: bool
    modification_notes: Optional[str]
    orders_created: List[Dict[str, Any]]
    prescriptions_created: List[Dict[str, Any]]
    prompt_used: Optional[str]
    confidence_score: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Doctor Prompt Override ───────────────────────────────────────────────────

class DoctorPromptOverrideCreate(BaseModel):
    clinician_id: UUID
    specialty_profile_id: Optional[UUID] = None
    questioning_prompt: Optional[str] = None
    examination_prompt: Optional[str] = None
    management_plan_prompt: Optional[str] = None
    documentation_prompt: Optional[str] = None
    prompt_variables: Optional[Dict[str, Any]] = None
    question_style: Optional[str] = None
    examination_style: Optional[str] = None
    management_style: Optional[str] = None


class DoctorPromptOverrideUpdate(BaseModel):
    questioning_prompt: Optional[str] = None
    examination_prompt: Optional[str] = None
    management_plan_prompt: Optional[str] = None
    documentation_prompt: Optional[str] = None
    prompt_variables: Optional[Dict[str, Any]] = None
    question_style: Optional[str] = None
    examination_style: Optional[str] = None
    management_style: Optional[str] = None
    is_active: Optional[bool] = None


class DoctorPromptOverrideResponse(BaseModel):
    override_id: UUID
    clinician_id: UUID
    specialty_profile_id: Optional[UUID]
    questioning_prompt: Optional[str]
    examination_prompt: Optional[str]
    management_plan_prompt: Optional[str]
    documentation_prompt: Optional[str]
    prompt_variables: Dict[str, Any]
    question_style: Optional[str]
    examination_style: Optional[str]
    management_style: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Request/Response for Flow Operations ─────────────────────────────────────

class StartConsultationRequest(BaseModel):
    encounter_id: UUID
    patient_id: UUID
    clinician_id: UUID
    specialty_profile_id: Optional[UUID] = None


class SubmitComplaintRequest(BaseModel):
    flow_id: UUID
    complaint_transcript: str
    language: Optional[str] = "en"


class SubmitAnswerRequest(BaseModel):
    flow_id: UUID
    encounter_id: UUID
    answer_transcript: str
    language: Optional[str] = "en"


class SubmitExaminationFindingsRequest(BaseModel):
    flow_id: UUID
    examination_transcript: str
    language: Optional[str] = "en"


class GenerateDocumentsRequest(BaseModel):
    flow_id: UUID
    encounter_id: UUID
    document_types: List[str]  # e.g., ["clinic_letter", "prescription", "lab_orders"]


class NextQuestionResponse(BaseModel):
    question: str
    turn_id: UUID
    turn_number: int
    suggested_next_action: Optional[str]
    should_move_to_examination: bool


class PhaseTransitionResponse(BaseModel):
    previous_phase: str
    new_phase: str
    reason: str
    guidance: Optional[Dict[str, Any]] = None
