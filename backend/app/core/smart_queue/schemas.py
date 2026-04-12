from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from .models import QueueStatus, RoomStatus, QueuePriority

# ── Queue Master ────────────────────────────────────────────────────────────

class QueueMasterBase(BaseModel):
    doctor_id: Optional[UUID] = None
    department: Optional[str] = None
    room_number: Optional[str] = None
    room_status: RoomStatus = RoomStatus.open

class QueueMasterCreate(QueueMasterBase):
    pass

class QueueMasterOut(QueueMasterBase):
    id: UUID
    queue_date: datetime
    status_reason: Optional[str] = None
    current_length: int
    avg_consult_time_min: float
    class Config:
        from_attributes = True

# ── Queue Patient Position ──────────────────────────────────────────────────

class QueuePositionCreate(BaseModel):
    queue_id: UUID
    visit_id: UUID
    patient_id: UUID
    priority_level: QueuePriority = QueuePriority.walk_in

class QueuePositionUpdate(BaseModel):
    status: Optional[QueueStatus] = None
    priority_level: Optional[QueuePriority] = None

class QueuePositionOut(BaseModel):
    id: UUID
    queue_id: UUID
    visit_id: UUID
    patient_id: UUID
    status: QueueStatus
    priority_level: QueuePriority
    calculated_priority_score: int
    position_number: Optional[int] = None
    estimated_wait_time_min: Optional[int] = None
    estimated_call_time: Optional[datetime] = None
    missed_calls_count: int
    joined_at: datetime
    class Config:
        from_attributes = True

# ── Audit & Events ──────────────────────────────────────────────────────────

class QueueEventCreate(BaseModel):
    queue_id: UUID
    visit_id: UUID
    event_type: str
    event_details: Dict[str, Any] = {}
    actor_id: Optional[UUID] = None

class QueueEventOut(QueueEventCreate):
    id: UUID
    created_at: datetime
    class Config:
        from_attributes = True

# ── Notifications ───────────────────────────────────────────────────────────

class NotificationOut(BaseModel):
    id: UUID
    visit_id: UUID
    patient_id: UUID
    channel: str
    notification_type: str
    message_content: str
    sent_at: datetime
    status: str
    class Config:
        from_attributes = True

# ── Wayfinding & AI Prediction ──────────────────────────────────────────────

class RoomWayfindingCreate(BaseModel):
    room_number: str
    department: str
    display_instructions: str

class WayfindingOut(RoomWayfindingCreate):
    id: UUID
    class Config:
        from_attributes = True

class CrowdPredictionSnapshotOut(BaseModel):
    id: UUID
    prediction_date: datetime
    department: Optional[str]
    predicted_peak_start: Optional[str]
    predicted_peak_end: Optional[str]
    predicted_inflow_count: int
    confidence_score: float
    factors_used: List[str]
    class Config:
        from_attributes = True

# ── Digital Signage Dashboard Schema ────────────────────────────────────────

class ActivePatientDisplay(BaseModel):
    position_number: int
    patient_id: UUID
    patient_uhid: Optional[str] = None # Filled by service
    patient_name: Optional[str] = None # Filled by service
    priority_level: str
    status: str

class DigitalSignageDisplay(BaseModel):
    room_number: str
    doctor_name: str
    department: str
    current_patient: Optional[ActivePatientDisplay] = None
    next_patients: List[ActivePatientDisplay] = []
    queue_length: int
    avg_wait_time_min: int
