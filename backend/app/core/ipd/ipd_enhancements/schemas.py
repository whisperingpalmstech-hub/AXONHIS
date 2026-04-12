"""IPD Enhancements — Schemas"""
from typing import Optional, List
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from decimal import Decimal

class AdmissionEstimateCreate(BaseModel):
    patient_name: str
    admission_request_id: Optional[UUID] = None
    patient_id: Optional[UUID] = None
    bed_category: Optional[str] = None
    expected_stay_days: int = 3
    package_id: Optional[UUID] = None

class AdmissionEstimateOut(BaseModel):
    id: UUID; org_id: UUID; patient_name: str; bed_category: Optional[str]
    expected_stay_days: int; total_estimated_cost: Decimal; deposit_required: Decimal
    insurance_coverage: Decimal; patient_liability: Decimal; status: str; created_at: datetime
    class Config: from_attributes = True

class PreAuthCreate(BaseModel):
    patient_id: UUID; admission_id: Optional[UUID] = None
    insurance_detail_id: Optional[UUID] = None; requested_amount: Decimal
    diagnosis_codes: Optional[list] = None; procedure_codes: Optional[list] = None
    expected_stay_days: Optional[int] = None; bed_category: Optional[str] = None; remarks: Optional[str] = None

class PreAuthOut(BaseModel):
    id: UUID; org_id: UUID; patient_id: UUID; pre_auth_number: Optional[str]
    requested_amount: Decimal; approved_amount: Optional[Decimal]; status: str
    requested_at: datetime; responded_at: Optional[datetime]
    class Config: from_attributes = True

class PreAuthResponse(BaseModel):
    action: str  # approve, reject, enhance
    approved_amount: Optional[Decimal] = None; response_notes: Optional[str] = None

class DischargeSummaryCreate(BaseModel):
    admission_id: UUID; patient_id: UUID
    admission_diagnosis: Optional[str] = None; discharge_diagnosis: Optional[str] = None
    clinical_summary: Optional[str] = None; hospital_course: Optional[str] = None
    procedures_performed: Optional[list] = None; condition_at_discharge: str = "improved"
    discharge_medications: Optional[list] = None; diet_instructions: Optional[str] = None
    follow_up_instructions: Optional[list] = None; warning_signs: Optional[str] = None
    discharge_type: str = "normal"

class DischargeSummaryOut(BaseModel):
    id: UUID; org_id: UUID; summary_number: str; admission_id: UUID; patient_id: UUID
    discharge_diagnosis: Optional[str]; condition_at_discharge: Optional[str]
    discharge_type: str; status: str; created_at: datetime
    class Config: from_attributes = True

class DietOrderCreate(BaseModel):
    admission_id: UUID; patient_id: UUID; diet_type: str
    special_instructions: Optional[str] = None; allergies: Optional[str] = None
    meal_preference: str = "veg"; fluid_restriction: Optional[str] = None

class DietOrderOut(BaseModel):
    id: UUID; org_id: UUID; diet_type: str; meal_preference: str
    is_active: bool; ordered_by_name: Optional[str]; created_at: datetime
    class Config: from_attributes = True

class ConsentFormCreate(BaseModel):
    admission_id: UUID; patient_id: UUID; consent_type: str
    procedure_name: Optional[str] = None; consent_details: Optional[str] = None
    risks_explained: bool = False; alternatives_explained: bool = False

class ConsentFormOut(BaseModel):
    id: UUID; org_id: UUID; consent_type: str; procedure_name: Optional[str]
    status: str; signed_at: Optional[datetime]; created_at: datetime
    class Config: from_attributes = True
