from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any

class AiContextCreate(BaseModel):
    patient_uhid: str
    user_id: str
    role_code: str
    clinical_summary: Optional[str] = None
    recent_vitals: Optional[Dict[str, Any]] = None
    active_medications: Optional[Dict[str, Any]] = None
    latest_labs: Optional[Dict[str, Any]] = None

class RpiwAiContextOut(AiContextCreate):
    id: UUID
    analyzed_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AiSuggestionOut(BaseModel):
    id: UUID
    context_id: UUID
    patient_uhid: str
    user_id: str
    target_role: str
    suggestion_type: str
    title: str
    content: str
    structured_data: Optional[Dict[str, Any]]
    status: str
    created_at: datetime
    resolved_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)

class AiAlertOut(BaseModel):
    id: UUID
    patient_uhid: str
    target_role: str
    risk_category: str
    severity: str
    message: str
    is_acknowledged: bool
    detected_at: datetime
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[str]
    model_config = ConfigDict(from_attributes=True)

class AiFeedbackCreate(BaseModel):
    user_id: str
    feedback_rating: str  # Helpful, Irrelevant, Incorrect
    comments: Optional[str] = None

class AiFeedbackOut(AiFeedbackCreate):
    id: UUID
    suggestion_id: UUID
    submitted_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AiActivityLogOut(BaseModel):
    id: UUID
    patient_uhid: str
    user_id: str
    role_code: str
    event_type: str
    reference_id: Optional[str]
    metadata_payload: Optional[Dict[str, Any]]
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

class GenerateAiResponseRequest(BaseModel):
    patient_uhid: str
    user_id: str
    role_code: str

class AcceptSuggestionRequest(BaseModel):
    user_id: str
    role_code: str
