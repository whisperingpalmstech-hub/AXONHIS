from datetime import datetime
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Optional, List, Any


# Summary Sources
class RpiwSummarySourceOut(BaseModel):
    id: UUID
    summary_id: UUID
    source_module: str
    source_record_id: str
    timestamp_aggregated: datetime
    model_config = ConfigDict(from_attributes=True)


# Summary Alerts
class RpiwSummaryAlertCreate(BaseModel):
    alert_type: str
    severity: str
    message: str

class RpiwSummaryAlertOut(BaseModel):
    id: UUID
    summary_id: UUID
    alert_type: str
    severity: str
    message: str
    is_active: bool
    detected_at: datetime
    resolved_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)


# Summary Tasks
class RpiwSummaryTaskCreate(BaseModel):
    task_category: str
    description: str
    status: str = "Pending"
    due_at: Optional[datetime] = None

class RpiwSummaryTaskOut(BaseModel):
    id: UUID
    summary_id: UUID
    task_category: str
    description: str
    status: str
    due_at: Optional[datetime]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# Summary Vitals
class RpiwSummaryVitalCreate(BaseModel):
    vital_sign: str
    value: str
    unit: str
    is_abnormal: bool = False
    recorded_at: datetime

class RpiwSummaryVitalOut(BaseModel):
    id: UUID
    summary_id: UUID
    vital_sign: str
    value: str
    unit: str
    is_abnormal: bool
    recorded_at: datetime
    model_config = ConfigDict(from_attributes=True)


# Summary Medications
class RpiwSummaryMedicationCreate(BaseModel):
    drug_name: str
    dosage: str
    frequency: str
    route: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: bool = True

class RpiwSummaryMedicationOut(BaseModel):
    id: UUID
    summary_id: UUID
    drug_name: str
    dosage: str
    frequency: str
    route: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


# Core Patient Summary
class RpiwPatientSummaryCreate(BaseModel):
    patient_uhid: str
    admission_number: Optional[str] = None
    visit_id: Optional[str] = None
    chief_issue: Optional[str] = None
    primary_diagnosis: Optional[str] = None
    current_clinical_status: Optional[str] = None

class RpiwPatientSummaryOut(BaseModel):
    id: UUID
    patient_uhid: str
    admission_number: Optional[str]
    visit_id: Optional[str]
    chief_issue: Optional[str]
    primary_diagnosis: Optional[str]
    current_clinical_status: Optional[str]
    generated_at: datetime
    last_updated_at: datetime
    last_updated_by: Optional[str]
    model_config = ConfigDict(from_attributes=True)


# Composite Summary Report for UI
class RpiwCompositeSummary(BaseModel):
    summary: RpiwPatientSummaryOut
    sources: List[RpiwSummarySourceOut] = []
    alerts: List[RpiwSummaryAlertOut] = []
    tasks: List[RpiwSummaryTaskOut] = []
    vitals: List[RpiwSummaryVitalOut] = []
    medications: List[RpiwSummaryMedicationOut] = []
