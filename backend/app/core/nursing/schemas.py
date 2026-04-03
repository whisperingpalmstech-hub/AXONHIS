from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class VitalCreate(BaseModel):
    admission_number: str
    patient_uhid: str
    heart_rate: Optional[int] = None
    blood_pressure_sys: Optional[int] = None
    blood_pressure_dia: Optional[int] = None
    temperature_f: Optional[float] = None
    spo2: Optional[float] = None
    respiratory_rate: Optional[int] = None
    pain_score: Optional[int] = None

class VitalOut(VitalCreate):
    id: UUID
    recorded_by: str
    recorded_at: datetime
    is_abnormal: bool

    class Config:
        from_attributes = True

class NoteCreate(BaseModel):
    admission_number: str
    patient_uhid: str
    note_type: str
    clinical_note: str

class NoteOut(NoteCreate):
    id: UUID
    nurse_uuid: str
    recorded_at: datetime

    class Config:
        from_attributes = True

# MAR schemas
class MARCreate(BaseModel):
    admission_number: str
    medication_name: str
    route: str
    frequency: str
    scheduled_slot: str

class MAROut(MARCreate):
    id: UUID
    is_administered: bool
    administered_by: Optional[str]
    administered_at: Optional[datetime]
    batch_number: Optional[str]
    notes: Optional[str]

    class Config:
        from_attributes = True

# Base response structure for the coversheet
class CoversheetDataOut(BaseModel):
    vitals: List[VitalOut]
    notes: List[NoteOut]
    mar: List[MAROut]
