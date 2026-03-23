"""OPD Visit Intelligence Engine — Pydantic Schemas"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID


# ── Visit Master ─────────────────────────────────────────────────────────────

class VisitCreate(BaseModel):
    patient_id: UUID
    patient_uhid: Optional[str] = None
    visit_type: str = "doctor_consultation"
    visit_source: str = "front_office"
    specialty: Optional[str] = None
    doctor_id: Optional[UUID] = None
    department: Optional[str] = None
    clinic_location: Optional[str] = None
    referral_type: Optional[str] = None
    referral_source: Optional[str] = None
    payment_entitlement: Optional[str] = None
    priority_tag: str = "normal"
    appointment_id: Optional[UUID] = None
    is_follow_up: bool = False
    parent_visit_id: Optional[UUID] = None

class VisitUpdate(BaseModel):
    status: Optional[str] = None
    priority_tag: Optional[str] = None
    doctor_id: Optional[UUID] = None
    specialty: Optional[str] = None
    department: Optional[str] = None
    queue_token: Optional[str] = None
    estimated_wait_min: Optional[int] = None

class VisitOut(BaseModel):
    id: UUID; visit_id: str; encounter_id: str; patient_id: UUID
    patient_uhid: Optional[str]; visit_date_time: datetime
    visit_type: str; visit_source: str; status: str
    specialty: Optional[str]; doctor_id: Optional[UUID]
    department: Optional[str]; clinic_location: Optional[str]
    referral_type: Optional[str]; referral_source: Optional[str]
    payment_entitlement: Optional[str]; priority_tag: str
    is_follow_up: bool; parent_visit_id: Optional[UUID]
    appointment_id: Optional[UUID]; queue_token: Optional[str]
    estimated_wait_min: Optional[int]; created_at: datetime
    class Config: from_attributes = True


# ── Complaints ───────────────────────────────────────────────────────────────

class ComplaintCreate(BaseModel):
    visit_id: UUID
    raw_complaint_text: str
    input_mode: str = "typed"
    language: str = "en"

class ComplaintOut(BaseModel):
    id: UUID; visit_id: UUID; raw_complaint_text: Optional[str]
    input_mode: str; language: str
    structured_symptoms: list; medical_keywords: list
    icpc_codes: list; icd_suggestions: list
    severity_score: Optional[float]; ai_confidence: Optional[float]
    created_at: datetime
    class Config: from_attributes = True


# ── Classification ───────────────────────────────────────────────────────────

class ClassificationCreate(BaseModel):
    visit_id: UUID
    vitals_snapshot: Optional[dict] = None  # {spo2, bp_sys, bp_dia, hr, temp}

class ClassificationOut(BaseModel):
    id: UUID; visit_id: UUID; category: str; classification_reason: Optional[str]
    triggered_rules: list; complaint_severity: Optional[float]
    vitals_abnormal: bool; has_chronic_disease: bool; age_risk: bool
    vitals_snapshot: Optional[dict]; is_override: bool
    classified_at: datetime
    class Config: from_attributes = True

class ClassificationOverride(BaseModel):
    category: str
    override_reason: str


# ── Doctor Recommendation ────────────────────────────────────────────────────

class DoctorRecommendationOut(BaseModel):
    id: UUID; visit_id: UUID; recommended_specialty: Optional[str]
    recommended_doctors: list; selection_mode: str
    selected_doctor_id: Optional[UUID]; created_at: datetime
    class Config: from_attributes = True

class DoctorSelectionUpdate(BaseModel):
    selected_doctor_id: UUID
    selection_mode: str = "manual"


# ── Questionnaire ────────────────────────────────────────────────────────────

class QuestionnaireTemplateCreate(BaseModel):
    specialty: str
    title: str
    description: Optional[str] = None
    questions: list = Field(default_factory=list)

class QuestionnaireTemplateOut(BaseModel):
    id: UUID; specialty: str; title: str; description: Optional[str]
    questions: list; is_active: bool; created_at: datetime
    class Config: from_attributes = True

class QuestionnaireResponseCreate(BaseModel):
    visit_id: UUID
    template_id: UUID
    patient_id: UUID
    responses: dict = Field(default_factory=dict)
    completion_source: Optional[str] = None

class QuestionnaireResponseOut(BaseModel):
    id: UUID; visit_id: UUID; template_id: UUID; patient_id: UUID
    responses: dict; completion_source: Optional[str]
    completed_at: Optional[datetime]; is_complete: bool; created_at: datetime
    class Config: from_attributes = True


# ── Context Snapshot ─────────────────────────────────────────────────────────

class ContextSnapshotOut(BaseModel):
    id: UUID; visit_id: UUID; patient_id: UUID
    previous_diagnoses: list; previous_prescriptions: list
    allergies: list; chronic_conditions: list
    last_visit_notes: Optional[str]; last_visit_date: Optional[datetime]
    recent_lab_reports: list; recent_radiology_reports: list
    active_medications: list; context_summary: Optional[str]
    risk_flags: list; aggregated_at: datetime
    class Config: from_attributes = True


# ── Multi-Visit Rules ────────────────────────────────────────────────────────

class MultiVisitRuleCreate(BaseModel):
    rule_name: str
    description: Optional[str] = None
    condition_type: str
    action: str
    priority: int = 0

class MultiVisitRuleOut(BaseModel):
    id: UUID; rule_name: str; description: Optional[str]
    condition_type: str; action: str; is_active: bool
    priority: int; created_at: datetime
    class Config: from_attributes = True


# ── Analytics ────────────────────────────────────────────────────────────────

class VisitAnalyticsOut(BaseModel):
    id: UUID; analytics_date: datetime; department: Optional[str]
    total_visits: int; routine_visits: int; priority_visits: int
    emergency_visits: int; completed_visits: int; cancelled_visits: int
    no_show_visits: int; avg_wait_time_min: Optional[float]
    avg_consult_time_min: Optional[float]
    top_specialties: list; top_complaints: list
    doctor_load_distribution: dict; computed_at: datetime
    class Config: from_attributes = True

class VisitDashboardSummary(BaseModel):
    period_start: str; period_end: str
    total_visits: int; completed: int; cancelled: int; no_shows: int
    emergency_count: int; priority_count: int; routine_count: int
    top_specialties: list; top_complaints: list
    avg_wait_time_min: Optional[float]
