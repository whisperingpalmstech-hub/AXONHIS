"""ER Module — Pydantic Schemas"""
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from decimal import Decimal


# ── ER Registration ──────────────────────────────────────

class ERRegistrationCreate(BaseModel):
    registration_type: str = "normal"  # urgent, normal
    patient_id: Optional[UUID] = None
    patient_name: str
    patient_uhid: Optional[str] = None
    age: Optional[int] = None
    age_unit: str = "years"
    gender: Optional[str] = None
    mobile: Optional[str] = None
    temp_id_description: Optional[str] = None
    mode_of_arrival: Optional[str] = None
    ambulance_number: Optional[str] = None
    brought_by: Optional[str] = None
    referral_source: Optional[str] = None
    chief_complaint: Optional[str] = None
    presenting_complaints: Optional[list] = None
    allergy_details: Optional[str] = None

class EREncounterOut(BaseModel):
    id: UUID
    org_id: UUID
    er_number: str
    registration_type: str
    patient_id: Optional[UUID]
    patient_name: str
    patient_uhid: Optional[str]
    age: Optional[int]
    gender: Optional[str]
    mobile: Optional[str]
    chief_complaint: Optional[str]
    status: str
    zone: Optional[str]
    priority: Optional[str]
    is_mlc: bool
    is_critical: bool
    is_ventilator: bool
    attending_doctor_name: Optional[str]
    attending_nurse_name: Optional[str]
    mode_of_arrival: Optional[str]
    arrival_time: datetime
    triage_time: Optional[datetime]
    disposition: Optional[str]
    created_at: datetime
    class Config: from_attributes = True


# ── Triage ──────────────────────────────────────────────

class ERTriageCreate(BaseModel):
    er_encounter_id: UUID
    triage_category: str  # resuscitation, emergent, urgent, less_urgent, non_urgent, dead
    temperature: Optional[Decimal] = None
    pulse: Optional[int] = None
    bp_systolic: Optional[int] = None
    bp_diastolic: Optional[int] = None
    respiratory_rate: Optional[int] = None
    spo2: Optional[Decimal] = None
    gcs_score: Optional[int] = None
    pain_score: Optional[int] = None
    blood_glucose: Optional[Decimal] = None
    airway: Optional[str] = None
    breathing: Optional[str] = None
    circulation: Optional[str] = None
    disability: Optional[str] = None
    exposure: Optional[str] = None
    allergies: Optional[str] = None
    current_medications: Optional[str] = None
    past_medical_history: Optional[str] = None
    last_meal: Optional[str] = None
    triage_notes: Optional[str] = None

class ERTriageOut(ERTriageCreate):
    id: UUID
    org_id: UUID
    triage_color: Optional[str]
    triaged_by: UUID
    triaged_by_name: Optional[str]
    triaged_at: datetime
    class Config: from_attributes = True


# ── Bed Map ─────────────────────────────────────────────

class ERBedCreate(BaseModel):
    bed_code: str
    zone: str
    bed_type: str = "stretcher"
    is_monitored: bool = False
    has_ventilator: bool = False

class ERBedOut(BaseModel):
    id: UUID
    org_id: UUID
    bed_code: str
    zone: str
    bed_type: str
    is_monitored: bool
    has_ventilator: bool
    status: str
    occupied_by_er_encounter_id: Optional[UUID]
    patient_gender: Optional[str]
    class Config: from_attributes = True

class ERBedAssignRequest(BaseModel):
    er_encounter_id: UUID
    bed_id: UUID


# ── MLC ─────────────────────────────────────────────────

class ERMlcCreate(BaseModel):
    er_encounter_id: UUID
    mlc_type: Optional[str] = None
    priority: str = "medium"
    police_station: Optional[str] = None
    police_officer_name: Optional[str] = None
    police_officer_badge: Optional[str] = None
    fir_number: Optional[str] = None
    buckle_number: Optional[str] = None
    injury_description: Optional[str] = None
    injury_details: Optional[list] = None
    legal_notes: Optional[str] = None

class ERMlcOut(ERMlcCreate):
    id: UUID
    org_id: UUID
    mlc_number: str
    status: str
    created_at: datetime
    class Config: from_attributes = True


# ── Nursing Scores ──────────────────────────────────────

class ERNursingScoreCreate(BaseModel):
    er_encounter_id: UUID
    score_type: str  # mews, sofa, apache_ii, gcs, pediatric, fall_risk, pain
    total_score: int
    risk_level: Optional[str] = None
    score_components: Optional[dict] = None
    interpretation: Optional[str] = None

class ERNursingScoreOut(ERNursingScoreCreate):
    id: UUID
    org_id: UUID
    scored_by: UUID
    scored_by_name: Optional[str]
    scored_at: datetime
    class Config: from_attributes = True


# ── Orders ──────────────────────────────────────────────

class EROrderCreate(BaseModel):
    er_encounter_id: UUID
    order_type: str  # lab, radiology, medication, procedure, consult
    order_description: str
    priority: str = "stat"

class EROrderOut(EROrderCreate):
    id: UUID
    org_id: UUID
    order_id: Optional[UUID]
    status: str
    ordered_by: UUID
    ordered_by_name: Optional[str]
    ordered_at: datetime
    completed_at: Optional[datetime]
    class Config: from_attributes = True


# ── Status Update ───────────────────────────────────────

class ERStatusUpdate(BaseModel):
    status: str
    disposition: Optional[str] = None
    disposition_department: Optional[str] = None
    attending_doctor_name: Optional[str] = None

# ── Dashboard Stats ─────────────────────────────────────

class ERDashboardStats(BaseModel):
    total_patients: int = 0
    triaged: int = 0
    in_treatment: int = 0
    awaiting_triage: int = 0
    critical: int = 0
    mlc_cases: int = 0
    beds_total: int = 0
    beds_available: int = 0
    beds_occupied: int = 0
    avg_wait_minutes: Optional[float] = None
    zone_occupancy: Optional[dict] = None
