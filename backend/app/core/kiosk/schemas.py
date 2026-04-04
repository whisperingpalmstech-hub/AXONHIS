from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

class TokenQueueCreate(BaseModel):
    department: str
    doctor_id: Optional[uuid.UUID] = None
    patient_uhid: Optional[str] = None
    patient_name: Optional[str] = None
    priority: bool = False
    priority_reason: Optional[str] = None

class TokenQueueOut(BaseModel):
    id: uuid.UUID
    token_number: int
    token_display: str
    department: str
    doctor_id: Optional[uuid.UUID]
    patient_uhid: Optional[str]
    patient_name: Optional[str]
    status: str
    priority: bool
    generated_at: datetime
    counter_name: Optional[str] = None

class QueueCounterCreate(BaseModel):
    counter_name: str
    department: str

class QueueCounterOut(QueueCounterCreate):
    id: uuid.UUID
    is_active: bool

class CallTokenCommand(BaseModel):
    token_id: uuid.UUID
    counter_id: Optional[uuid.UUID] = None

class AppointmentCheckInCommand(BaseModel):
    identifier: str # Mobile, Appt ID, or UHID
    
class AnnouncementOut(BaseModel):
    id: uuid.UUID
    announcement_text: str
    announced_at: datetime
    
class KioskAppointmentBooking(BaseModel):
    department: str
    doctor_id: uuid.UUID
    patient_name: str
    mobile: str
    date: str
    time_slot: str
