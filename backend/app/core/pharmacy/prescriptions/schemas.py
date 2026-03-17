from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime
from typing import Optional, List

class PrescriptionItemCreate(BaseModel):
    drug_id: uuid.UUID
    dosage: str
    frequency: str
    duration: str
    instructions: Optional[str] = None

class PrescriptionCreate(BaseModel):
    patient_id: uuid.UUID
    encounter_id: uuid.UUID
    order_id: Optional[uuid.UUID] = None
    prescribing_doctor_id: uuid.UUID
    items: List[PrescriptionItemCreate]

class PrescriptionItemOut(BaseModel):
    id: uuid.UUID
    drug_id: uuid.UUID
    dosage: str
    frequency: str
    duration: str
    instructions: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class PrescriptionOut(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    encounter_id: uuid.UUID
    order_id: Optional[uuid.UUID]
    prescribing_doctor_id: uuid.UUID
    prescription_time: datetime
    status: str
    items: List[PrescriptionItemOut]
    model_config = ConfigDict(from_attributes=True)
