from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from .models import ConsultStatus

# ── 1. Doctor Worklist Dashboard ───────────────────────────────────────────

class DoctorWorklistCreate(BaseModel):
    doctor_id: UUID
    visit_id: UUID
    patient_id: UUID
    priority_indicator: str = "normal"
    queue_position: Optional[int] = None

class DoctorWorklistOut(DoctorWorklistCreate):
    id: UUID
    status: ConsultStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    class Config: from_attributes = True

# ── 3. AI Clinical Scribe & Notes ───────────────────────────────────────────

class ConsultationNoteInput(BaseModel):
    visit_id: UUID
    doctor_id: UUID
    chief_complaint: Optional[str] = None
    history_present_illness: Optional[str] = None
    physical_examination: Optional[str] = None
    diagnosis: Optional[str] = None
    plan: Optional[str] = None
    generated_by_ai: bool = False
    audio_reference_url: Optional[str] = None

class ConsultationNoteOut(ConsultationNoteInput):
    id: UUID
    created_at: datetime
    updated_at: datetime
    class Config: from_attributes = True

class ScribeAudioInput(BaseModel):
    doctor_id: UUID
    audio_data_base64: str

# ── 5. AI Diagnosis & Order Suggestion Engine ───────────────────────────────

class AISuggestionEngineInput(BaseModel):
    visit_id: UUID
    symptoms: str
    vitals: Optional[Dict[str, Any]] = None
    age: Optional[int] = None
    gender: Optional[str] = None

class AISuggestionOutput(BaseModel):
    suggested_diagnoses: List[str]
    recommended_lab_tests: List[str]
    recommended_imaging_studies: List[str]

# ── 6. Clinical Documentation Templates ──────────────────────────────────────

class DoctorClinicalTemplateCreate(BaseModel):
    name: str
    specialty: str = "General"
    chief_complaint_template: Optional[str] = None
    history_template: Optional[str] = None
    physical_template: Optional[str] = None
    plan_template: Optional[str] = None

class DoctorClinicalTemplateOut(DoctorClinicalTemplateCreate):
    id: UUID
    is_active: bool
    class Config: from_attributes = True

# ── 8. Voice-to-Text & Structured Prescription ──────────────────────────────

class PrescriptionInput(BaseModel):
    visit_id: UUID
    doctor_id: UUID
    medicine_name: str
    strength: Optional[str] = None
    dosage: str
    frequency: str
    duration: str
    instructions: Optional[str] = None

class PrescriptionOut(PrescriptionInput):
    id: UUID
    prescribed_at: datetime
    class Config: from_attributes = True

class VoicePrescriptionInput(BaseModel):
    doctor_id: UUID
    voice_command_text: str

# ── 7. Diagnostic Ordering ──────────────────────────────────────────────────

class DiagnosticOrderInput(BaseModel):
    visit_id: UUID
    doctor_id: UUID
    order_type: str # lab, radiology
    test_name: str
    instructions: Optional[str] = None

class DiagnosticOrderOut(DiagnosticOrderInput):
    id: UUID
    status: str
    ordered_at: datetime
    class Config: from_attributes = True

# ── 9. Clinical Summary Generatr ────────────────────────────────────────────

class ClinicalSummaryOut(BaseModel):
    id: UUID
    visit_id: UUID
    doctor_id: UUID
    summary_content: Dict[str, Any]
    pdf_url: Optional[str] = None
    generated_at: datetime
    class Config: from_attributes = True

# ── 10. Follow-Up & Certificate Management ──────────────────────────────────

class FollowUpRecordInput(BaseModel):
    visit_id: UUID
    action_type: str 
    target_date: Optional[datetime] = None
    target_specialty: Optional[str] = None
    notes: Optional[str] = None
    certificate_url: Optional[str] = None

class FollowUpRecordOut(FollowUpRecordInput):
    id: UUID
    created_at: datetime
    class Config: from_attributes = True

# ── 2. Patient Timeline EMR Viewer ──────────────────────────────────────────

class PatientTimelineNode(BaseModel):
    node_type: str # diagnosis, lab_result, radiology_report, visit, rx, allergy
    date: str
    title: str
    details: Optional[str] = None
    reference_id: Optional[str] = None

class PatientTimelineEMRViewer(BaseModel):
    patient_id: UUID
    chronological_nodes: List[PatientTimelineNode]
