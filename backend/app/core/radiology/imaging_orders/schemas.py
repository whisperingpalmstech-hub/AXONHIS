import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List

class ImagingOrderBase(BaseModel):
    requested_modality: str
    requested_study: str
    priority: str = "routine"
    encounter_id: uuid.UUID
    patient_id: uuid.UUID
    order_id: uuid.UUID # Reference to the core hospital order

class ImagingOrderCreate(ImagingOrderBase):
    pass

class ImagingOrderOut(ImagingOrderBase):
    id: uuid.UUID
    status: str
    ordered_by: uuid.UUID
    ordered_at: datetime

    class Config:
        orm_mode = True
