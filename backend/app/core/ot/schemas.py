"""OT Module — Schemas"""
from typing import Optional, List
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from decimal import Decimal

class OTRoomCreate(BaseModel):
    room_code: str; room_name: str; room_type: str = "general"
    floor: Optional[str] = None; is_laminar_flow: bool = False
    has_c_arm: bool = False; has_laser: bool = False

class OTRoomOut(BaseModel):
    id: UUID; org_id: UUID; room_code: str; room_name: str; room_type: str
    is_laminar_flow: bool; has_c_arm: bool; has_laser: bool; status: str; is_active: bool
    class Config: from_attributes = True

class OTScheduleCreate(BaseModel):
    ot_room_id: UUID; patient_id: UUID; patient_name: str
    patient_uhid: Optional[str] = None; admission_id: Optional[UUID] = None
    surgery_name: str; surgery_code: Optional[str] = None
    surgery_type: str = "elective"; laterality: Optional[str] = None
    estimated_duration_mins: int = 60; anesthesia_type: Optional[str] = None
    scheduled_date: datetime; primary_surgeon_name: str
    anesthesiologist_name: Optional[str] = None; scrub_nurse_name: Optional[str] = None
    pre_op_diagnosis: Optional[str] = None; blood_group: Optional[str] = None

class OTScheduleOut(BaseModel):
    id: UUID; org_id: UUID; ot_room_id: UUID; patient_name: str; patient_uhid: Optional[str]
    surgery_name: str; surgery_type: str; anesthesia_type: Optional[str]
    scheduled_date: datetime; estimated_duration_mins: int
    primary_surgeon_name: str; anesthesiologist_name: Optional[str]
    status: str; consent_obtained: bool; blood_loss_ml: Optional[int]
    total_charges: Decimal; created_at: datetime
    class Config: from_attributes = True

class OTStatusUpdate(BaseModel):
    status: str  # pre_op, patient_in_ot, anesthesia_start, incision, closing, post_op, completed, cancelled
    post_op_diagnosis: Optional[str] = None; post_op_notes: Optional[str] = None
    blood_loss_ml: Optional[int] = None; cancellation_reason: Optional[str] = None

class OTConsumableCreate(BaseModel):
    ot_schedule_id: UUID; item_name: str; item_code: Optional[str] = None
    quantity: int = 1; unit_price: Decimal = Decimal("0"); category: Optional[str] = None

class OTConsumableOut(BaseModel):
    id: UUID; item_name: str; item_code: Optional[str]; quantity: int
    unit_price: Decimal; total_price: Decimal; category: Optional[str]; is_returned: bool
    class Config: from_attributes = True

class OTAnesthesiaCreate(BaseModel):
    ot_schedule_id: UUID; anesthesia_type: str; asa_score: Optional[str] = None
    airway: Optional[str] = None; medications_given: Optional[list] = None
    notes: Optional[str] = None

class OTAnesthesiaOut(BaseModel):
    id: UUID; anesthesia_type: str; asa_score: Optional[str]; airway: Optional[str]
    induction_time: Optional[datetime]; extubation_time: Optional[datetime]
    complications: Optional[str]; recorded_by_name: Optional[str]
    class Config: from_attributes = True

class OTDashboardStats(BaseModel):
    total_rooms: int = 0; rooms_available: int = 0; rooms_in_use: int = 0
    todays_surgeries: int = 0; in_progress: int = 0; completed_today: int = 0
    cancelled_today: int = 0; emergency_today: int = 0
