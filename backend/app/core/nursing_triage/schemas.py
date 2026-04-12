from typing import Optional, List, Dict, Any
from pydantic import BaseModel, root_validator
from uuid import UUID
from datetime import datetime
from .models import TriageStatus

# ── Vitals Engine ───────────────────────────────────────────────────────────

class NursingVitalsCreate(BaseModel):
    visit_id: UUID
    patient_id: UUID
    org_id: Optional[UUID] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    heart_rate: Optional[int] = None
    respiratory_rate: Optional[int] = None
    temperature_celsius: Optional[float] = None
    oxygen_saturation_spo2: Optional[int] = None
    
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    # BMI auto-calculated in service if both present
    
    blood_glucose: Optional[float] = None
    pain_score: Optional[int] = None
    gcs_score: Optional[int] = None

class NursingVitalsOut(NursingVitalsCreate):
    id: UUID
    bmi: Optional[float] = None
    is_manual_entry: bool
    recorded_at: datetime
    class Config:
        from_attributes = True

# ── Worklist Engine ─────────────────────────────────────────────────────────

class NursingWorklistCreate(BaseModel):
    visit_id: UUID
    patient_id: UUID
    org_id: Optional[UUID] = None
    priority_level: str = "normal"

class NursingWorklistOut(NursingWorklistCreate):
    id: UUID
    assigned_nurse_id: Optional[UUID] = None
    triage_status: TriageStatus
    called_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    class Config:
        from_attributes = True

# ── Assessment & Templates ──────────────────────────────────────────────────

class NursingAssessmentCreate(BaseModel):
    visit_id: UUID
    patient_id: UUID
    org_id: Optional[UUID] = None
    template_used: Optional[str] = None
    chief_complaint: Optional[str] = None
    allergy_information: Optional[str] = None
    past_medical_history: Optional[str] = None
    medication_history: Optional[str] = None
    family_history: Optional[str] = None
    social_history: Optional[str] = None
    nursing_observations: Optional[str] = None

class NursingAssessmentOut(NursingAssessmentCreate):
    id: UUID
    recorded_at: datetime
    class Config:
        from_attributes = True

class NursingTemplateCreate(BaseModel):
    name: str
    specialty: Optional[str] = "General"
    fields: List[Dict[str, str]] = []

class NursingTemplateOut(NursingTemplateCreate):
    id: UUID
    is_active: bool
    class Config:
        from_attributes = True

# ── Document & Priority ─────────────────────────────────────────────────────

class DocumentUploadCreate(BaseModel):
    visit_id: UUID
    patient_id: UUID
    org_id: Optional[UUID] = None
    document_type: str
    file_path: str
    file_format: str

class DocumentUploadOut(DocumentUploadCreate):
    id: UUID
    uploaded_at: datetime
    class Config:
        from_attributes = True

class PriorityUpdateOut(BaseModel):
    id: UUID
    visit_id: UUID
    previous_priority: str
    new_priority: str
    trigger_reason: str
    updated_at: datetime
    class Config:
        from_attributes = True

# ── Doctor Notification Context ─────────────────────────────────────────────

class DoctorNotificationContext(BaseModel):
    visit_id: UUID
    vitals_summary: Optional[NursingVitalsOut]
    assessment_notes: Optional[NursingAssessmentOut]
    documents: List[DocumentUploadOut]
    priority_flag: str
