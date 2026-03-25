from datetime import datetime
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Optional, List, Dict, Any

# Common Action Info
class ActionBase(BaseModel):
    patient_uhid: str
    admission_number: Optional[str] = None
    visit_id: Optional[str] = None
    created_by_user_id: str
    created_by_role: str

class RpiwActionOut(BaseModel):
    id: UUID
    patient_uhid: str
    admission_number: Optional[str]
    visit_id: Optional[str]
    action_type: str
    status: str
    validation_status: str
    validation_remarks: Optional[str]
    created_by_user_id: str
    created_by_role: str
    created_at: datetime
    executed_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)


# ─── Clinical Notes ──────────────────────────────────
class ClinicalNoteCreate(ActionBase):
    note_type: str  # Progress, Nursing, Procedure, Discharge
    content: str

class RpiwClinicalNoteOut(BaseModel):
    id: UUID
    action_id: UUID
    note_type: str
    content: str
    is_signed: bool
    recorded_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ─── Orders ──────────────────────────────────
class OrderCreate(ActionBase):
    order_category: str  # laboratory, radiology, procedure, consult
    item_code: str
    item_name: str
    priority: str = "Routine"

class RpiwOrderOut(BaseModel):
    id: UUID
    action_id: UUID
    order_category: str
    item_code: str
    item_name: str
    priority: str
    routed_to_module: Optional[str]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ─── Prescriptions ──────────────────────────────────
class PrescriptionCreate(ActionBase):
    drug_name: str
    dosage: str
    frequency: str
    route: str
    duration_days: int
    instructions: Optional[str] = None

class RpiwPrescriptionOut(BaseModel):
    id: UUID
    action_id: UUID
    drug_name: str
    dosage: str
    frequency: str
    route: str
    duration_days: int
    instructions: Optional[str]
    routed_to_pharmacy: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ─── Tasks ──────────────────────────────────
class TaskCreate(ActionBase):
    assigned_role: str  # nurse, phlebotomist
    assigned_user_id: Optional[str] = None
    task_description: str
    priority: str = "Routine"
    due_at: Optional[datetime] = None

class RpiwTaskOut(BaseModel):
    id: UUID
    action_id: UUID
    assigned_role: str
    assigned_user_id: Optional[str]
    task_description: str
    priority: str
    due_at: Optional[datetime]
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# ─── Voice-to-Action ──────────────────────────────────
class VoiceCommandRequest(ActionBase):
    transcript: str

class StructuredActionResponse(BaseModel):
    action_type: str  # e.g., "prescription", "order", "task"
    parsed_data: Dict[str, Any]

class VoiceCommandResult(BaseModel):
    actions_extracted: List[StructuredActionResponse]
    raw_transcript: str
